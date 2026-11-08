from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import httpx

from ..config import settings
from ..db import LLMCallRecord, log_llm_call


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost_yuan: float
    model_name: str = ""
    tier: str = ""


class LLMClient(ABC):
    """模型客户端接口。云端大模型与端侧小模型各自实现。"""

    tier: str = ""

    @abstractmethod
    async def chat(
        self,
        messages: List[dict],
        *,
        agent_role: str,
        user_id: Optional[int] = None,
        submission_id: Optional[int] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        ...


# ===== 共享 HTTP 客户端 + 限流冷却 =====

_http: Optional[httpx.AsyncClient] = None

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4

# 全局限流冷却：收到 429 后记录恢复时间点，后续请求过闸时先等到该时间再发。
# 实测免费模型的限流是分钟级窗口，短退避重试只会白白消耗尝试次数。
_rate_limit_until = 0.0


def get_http() -> httpx.AsyncClient:
    global _http
    if _http is None:
        _http = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
    return _http


async def close_http() -> None:
    global _http
    if _http is not None:
        await _http.aclose()
        _http = None


class OpenAICompatibleClient(LLMClient):
    """OpenAI 兼容 chat/completions 客户端基类（智谱云端 / Ollama 端侧共用）。

    特性：实例级并发闸 + 429 全局冷却 + 指数退避重试 + 成本日志。
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        input_price_per_1k: float,
        output_price_per_1k: float,
        max_concurrency: int,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.input_price = input_price_per_1k
        self.output_price = output_price_per_1k
        # 每个客户端独立并发闸：云端受免费模型配额限制（默认串行），
        # 端侧本地推理不受限，允许更高并发。
        self._gate = asyncio.Semaphore(max_concurrency)

    async def chat(
        self,
        messages: List[dict],
        *,
        agent_role: str,
        user_id: Optional[int] = None,
        submission_id: Optional[int] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            # 各 Agent 的 JSON 产出均不超过数百字，限长避免长篇生成拖慢全流程。
            # 规划 Agent 步骤较多，单独放宽（见 agents/planning.py）。
            "max_tokens": max_tokens,
        }

        client = get_http()
        wall_start = time.perf_counter()
        last_error: Optional[Exception] = None

        global _rate_limit_until

        for attempt in range(MAX_ATTEMPTS):
            retry_delay = 0.0

            async with self._gate:
                # 过闸先等全局限流冷却期结束（429 恢复窗口）
                cooldown = _rate_limit_until - time.monotonic()
                if cooldown > 0:
                    await asyncio.sleep(cooldown)

                try:
                    resp = await client.post(url, json=payload, headers=headers)
                except httpx.TransportError as e:
                    last_error = e
                    retry_delay = 2.0 ** attempt
                else:
                    if resp.status_code == 429 and attempt < MAX_ATTEMPTS - 1:
                        last_error = RuntimeError("LLM API 429 rate limited")
                        # 分钟级限流窗口：冷却 10s 起步，逐次加倍
                        _rate_limit_until = (
                            time.monotonic() + 10.0 * (2 ** attempt)
                        )
                        retry_delay = 0.5
                    elif (
                        resp.status_code in RETRYABLE_STATUS
                        and attempt < MAX_ATTEMPTS - 1
                    ):
                        last_error = RuntimeError(
                            f"LLM API HTTP {resp.status_code}"
                        )
                        retry_delay = 2.0 ** attempt
                    else:
                        # 成功或不可重试的错误（后者 raise）
                        resp.raise_for_status()
                        data = resp.json()

                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {}) or {}
                        prompt_tokens = int(usage.get("prompt_tokens", 0))
                        completion_tokens = int(
                            usage.get("completion_tokens", 0)
                        )
                        cost = (
                            prompt_tokens / 1000.0 * self.input_price
                            + completion_tokens / 1000.0 * self.output_price
                        )
                        latency_ms = int(
                            (time.perf_counter() - wall_start) * 1000
                        )

                        await log_llm_call(
                            LLMCallRecord(
                                agent_role=agent_role,
                                model_tier=self.tier,
                                model_name=self.model,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                latency_ms=latency_ms,
                                cost_yuan=cost,
                                user_id=user_id,
                                submission_id=submission_id,
                            )
                        )

                        return LLMResponse(
                            content=content,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            latency_ms=latency_ms,
                            cost_yuan=cost,
                            model_name=self.model,
                            tier=self.tier,
                        )

            if retry_delay > 0:
                await asyncio.sleep(retry_delay)

        raise last_error or RuntimeError("LLM 调用失败")


class CloudLLMClient(OpenAICompatibleClient):
    """智谱 GLM 云端大模型。"""

    tier = "cloud"

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.zhipu_base_url,
            api_key=settings.zhipu_api_key,
            model=settings.zhipu_model,
            input_price_per_1k=settings.zhipu_input_price_per_1k,
            output_price_per_1k=settings.zhipu_output_price_per_1k,
            max_concurrency=settings.llm_max_concurrency,
        )


class EdgeLLMClient(OpenAICompatibleClient):
    """Ollama 端侧小模型（本地推理，成本记 0，不受云端限流约束）。"""

    tier = "edge"

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.ollama_base_url,
            api_key="ollama",  # Ollama 不校验 key
            model=settings.ollama_model,
            input_price_per_1k=0.0,
            output_price_per_1k=0.0,
            max_concurrency=2,
        )
