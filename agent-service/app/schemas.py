from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ProblemInfoIn(BaseModel):
    title: str = ""
    description: str = ""
    input_description: str = ""
    output_description: str = ""
    constraints: str = ""
    sample_input: str = ""
    sample_output: str = ""


class JudgeResultIn(BaseModel):
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    passed_tests: Optional[int] = None
    total_tests: Optional[int] = None


class DiagnoseRequest(BaseModel):
    submission_id: Optional[int] = None
    user_id: Optional[int] = None
    problem_id: Optional[int] = None
    code: str
    language: str = "go"
    problem: ProblemInfoIn
    judge_result: JudgeResultIn


class MasteryRecordIn(BaseModel):
    """判题通过后 Go 后端上报，用于强化掌握度。"""
    user_id: int
    problem_id: int
    language: str = "go"
    passed: bool = True


# ===== 四个 Agent 的产出 =====

class DiagnosisOut(BaseModel):
    error_type: str
    root_cause: str
    concepts: List[str]
    explanation: str
    hint: str


class FeedbackOut(BaseModel):
    tutoring_style: str
    content: str
    guiding_questions: List[str]
    code_example: str = ""


class ReviewIssueOut(BaseModel):
    severity: str
    category: str
    message: str
    suggestion: str


class ReviewOut(BaseModel):
    overall_score: int
    strengths: List[str]
    issues: List[ReviewIssueOut]
    summary: str


class PlanStepOut(BaseModel):
    action: str
    detail: str


class PlanOut(BaseModel):
    summary: str
    steps: List[PlanStepOut]
    next_problem_hint: str


class DiagnoseMeta(BaseModel):
    model: str
    model_tier: str
    latency_ms: int          # 全流程墙钟时间
    prompt_tokens: int       # 四次调用合计
    completion_tokens: int
    cost_yuan: float = 0.0


class DiagnoseResponse(BaseModel):
    diagnosis: DiagnosisOut
    feedback: FeedbackOut
    review: ReviewOut
    planning: PlanOut
    meta: DiagnoseMeta
