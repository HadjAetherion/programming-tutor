from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ..llm.client import LLMResponse
from ..llm.gateway import ModelGateway


@dataclass
class ProblemInfo:
    title: str = ""
    description: str = ""
    input_description: str = ""
    output_description: str = ""
    constraints: str = ""
    sample_input: str = ""
    sample_output: str = ""


# 语言标识 → 面向 LLM 的语言名称（提示词用）
LANGUAGE_LABELS = {
    "go": "Go",
    "python": "Python",
    "java": "Java",
    "cpp": "C++",
}


def language_label(language: str) -> str:
    return LANGUAGE_LABELS.get((language or "go").strip().lower(), language or "Go")


@dataclass
class JudgeResultInfo:
    status: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    passed_tests: Optional[int] = None
    total_tests: Optional[int] = None


@dataclass
class DiagnosisOutput:
    """诊断 Agent 的产出，供反馈/规划 Agent 消费。"""

    error_type: str = "未知"
    root_cause: str = ""
    concepts: List[str] = field(default_factory=list)
    explanation: str = ""
    hint: str = ""


@dataclass
class ReviewIssue:
    severity: str = "medium"  # high / medium / low
    category: str = ""        # 命名 / 结构 / 边界 / Go惯例 / 性能 / 可读性
    message: str = ""
    suggestion: str = ""


@dataclass
class ReviewOutput:
    """审查 Agent 的产出，供规划 Agent 消费。"""

    overall_score: int = 0
    strengths: List[str] = field(default_factory=list)
    issues: List[ReviewIssue] = field(default_factory=list)
    summary: str = ""


@dataclass
class FeedbackOutput:
    """反馈 Agent 的产出：按干预策略生成的辅导内容。"""

    tutoring_style: str = ""  # direct_hint / socratic / scaffold
    content: str = ""
    guiding_questions: List[str] = field(default_factory=list)
    code_example: str = ""


@dataclass
class PlanStep:
    action: str = ""
    detail: str = ""


@dataclass
class PlanOutput:
    """规划 Agent 的产出：下一步学习建议。"""

    summary: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    next_problem_hint: str = ""


@dataclass
class AgentContext:
    """多智能体共享上下文（通信协议的载体）。

    每个 Agent 从 ctx 读取输入、把产出写回 ctx，供下游 Agent 消费：
      - 诊断 Agent / 审查 Agent：读取基础信息（并行执行，互不依赖）
      - 反馈 Agent：读取 diagnosis_result
      - 规划 Agent：读取 diagnosis_result + review_result
    """

    code: str = ""
    language: str = "go"
    problem: ProblemInfo = field(default_factory=ProblemInfo)
    judge_result: JudgeResultInfo = field(default_factory=JudgeResultInfo)
    user_id: Optional[int] = None
    problem_id: Optional[int] = None
    submission_id: Optional[int] = None

    # 中间结果（Agent 间传递）
    diagnosis_result: Optional[DiagnosisOutput] = None
    review_result: Optional[ReviewOutput] = None


class Agent:
    """Agent 基类：name 标识角色，run 消费 ctx 返回 (产出, LLM响应)。"""

    name: str = ""

    async def run(
        self,
        ctx: AgentContext,
        gateway: ModelGateway,
    ) -> Tuple[object, LLMResponse]:
        raise NotImplementedError
