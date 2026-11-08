from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import asyncpg

from .config import settings

logger = logging.getLogger("agent-service")

_pool: Optional[asyncpg.Pool] = None


async def init_pool() -> None:
    """初始化 PostgreSQL 连接池。

    连接失败时不抛异常（仅告警），让 /diagnose 仍可工作，
    只是成本日志不记录——便于本地开发。
    """
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                dsn=settings.dsn,
                min_size=1,
                max_size=5,
            )
        except Exception as e:
            logger.warning("DB 连接失败，成本日志将不记录: %s", e)
            _pool = None


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> Optional[asyncpg.Pool]:
    """连接池访问器（None 表示 DB 不可用）。"""
    return _pool


async def fetch(sql: str, *args) -> list:
    """只读查询；DB 不可用时返回空列表而不是抛异常。"""
    if _pool is None:
        return []
    return await _pool.fetch(sql, *args)


async def fetchrow(sql: str, *args):
    if _pool is None:
        return None
    return await _pool.fetchrow(sql, *args)


@dataclass
class LLMCallRecord:
    agent_role: str
    model_tier: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost_yuan: float
    user_id: Optional[int]
    submission_id: Optional[int]


async def log_llm_call(record: LLMCallRecord) -> None:
    """记录一次 LLM 调用的成本/延迟，供创新点③评估。"""
    if _pool is None:
        return
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO llm_call_log
                (agent_role, model_tier, model_name,
                 prompt_tokens, completion_tokens,
                 latency_ms, cost_yuan, user_id, submission_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            record.agent_role,
            record.model_tier,
            record.model_name,
            record.prompt_tokens,
            record.completion_tokens,
            record.latency_ms,
            record.cost_yuan,
            record.user_id,
            record.submission_id,
        )
