from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import close_pool, init_pool
from .llm.client import close_http
from .routers import diagnose, mastery


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_http()
    await close_pool()


app = FastAPI(
    title="Programming Tutor Agent Service",
    description="多智能体协同诊断与自适应辅导服务",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "agent-service"}


app.include_router(diagnose.router, prefix="/api/v1")
app.include_router(mastery.router, prefix="/api/v1")
