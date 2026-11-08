from __future__ import annotations

import logging
from typing import List, Optional

from .. import router as llm_router
from .client import CloudLLMClient, EdgeLLMClient, LLMClient, LLMResponse

logger = logging.getLogger("agent-service")


class ModelGateway:
    """模型网关：统一云端大模型与端侧小模型的访问（开题书"模型网关"组件）。

    每次调用先经路由决策器（router.py）按任务类型/复杂度/预算选模型规模；
    端侧调用失败时自动回退云端，保证可用性。
    """

    def __init__(self) -> None:
        self.cloud: LLMClient = CloudLLMClient()
        self.edge: LLMClient = EdgeLLMClient()

    def _client_for(self, tier: str) -> LLMClient:
        return self.edge if tier == "edge" else self.cloud

    async def complete(
        self,
        messages: List[dict],
        *,
        agent_role: str,
        user_id: Optional[int] = None,
        submission_id: Optional[int] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        ctx=None,
        routing_hint: Optional[str] = None,
    ) -> LLMResponse:
        tier = llm_router.decide(agent_role, ctx, routing_hint)

        try:
            resp = await self._client_for(tier).chat(
                messages,
                agent_role=agent_role,
                user_id=user_id,
                submission_id=submission_id,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:  # 端侧离线/超时等 -> 回退另一侧
            fallback = "cloud" if tier == "edge" else "edge"
            logger.warning(
                "Agent %s 走 %s 失败(%s)，回退 %s",
                agent_role, tier, e, fallback,
            )
            resp = await self._client_for(fallback).chat(
                messages,
                agent_role=agent_role,
                user_id=user_id,
                submission_id=submission_id,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        llm_router.add_cost(resp.cost_yuan)
        return resp
