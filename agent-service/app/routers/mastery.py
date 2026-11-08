from __future__ import annotations

from fastapi import APIRouter

from .. import knowledge
from ..schemas import MasteryRecordIn

router = APIRouter()


@router.post("/mastery/record")
async def record_mastery(req: MasteryRecordIn) -> dict:
    """Go 后端在判题通过（ACCEPTED）后调用：强化该题标注概念的掌握度。

    题目尚无概念标注时为 no-op；passed=false 时由诊断路径负责衰减。
    """
    if req.passed:
        await knowledge.record_outcome(req.user_id, req.problem_id, req.language)
    return {"ok": True}
