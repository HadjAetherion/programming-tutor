from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..agents.base import AgentContext, JudgeResultInfo, ProblemInfo
from ..config import settings
from ..orchestrator import diagnose
from ..schemas import DiagnoseRequest, DiagnoseResponse

router = APIRouter()


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose_endpoint(req: DiagnoseRequest) -> DiagnoseResponse:
    if not settings.zhipu_api_key:
        raise HTTPException(
            status_code=500,
            detail="ZHIPU_API_KEY 未配置，请在 agent-service/.env 中设置",
        )

    ctx = AgentContext(
        code=req.code,
        language=req.language,
        problem=ProblemInfo(**req.problem.model_dump()),
        judge_result=JudgeResultInfo(**req.judge_result.model_dump()),
        user_id=req.user_id,
        problem_id=req.problem_id,
        submission_id=req.submission_id,
    )
    return await diagnose(ctx)
