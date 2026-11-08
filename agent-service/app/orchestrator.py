from __future__ import annotations

import asyncio
import logging
import time

from .agents.base import (
    AgentContext,
    DiagnosisOutput,
    FeedbackOutput,
    PlanOutput,
    ReviewOutput,
)
from .agents.diagnosis import DiagnosisAgent
from .agents.feedback import FeedbackAgent
from .agents.planning import PlanningAgent
from .agents.review import ReviewAgent
from .config import settings
from . import knowledge
from .llm.client import LLMResponse
from .llm.gateway import ModelGateway
from .schemas import (
    DiagnosisOut,
    DiagnoseMeta,
    DiagnoseResponse,
    FeedbackOut,
    PlanOut,
    PlanStepOut,
    ReviewIssueOut,
    ReviewOut,
)

logger = logging.getLogger("agent-service")

_gateway = ModelGateway()


async def _run_agent(agent, ctx: AgentContext):
    """运行单个 Agent，失败时返回兜底产出而不中断整个流程。"""
    try:
        return await agent.run(ctx, _gateway)
    except Exception as e:
        logger.exception("Agent %s 执行失败: %s", agent.name, e)
        return None, None


async def diagnose(ctx: AgentContext) -> DiagnoseResponse:
    """多智能体协同编排器。

    协作流程（开题书定义的四类角色）：
      第一阶段（并行）：诊断 Agent ∥ 审查 Agent    —— asyncio.gather
      第二阶段（串行）：反馈 Agent  <- 消费诊断结果
                        规划 Agent  <- 消费诊断 + 审查结果

    中间结果通过 AgentContext 在 Agent 间传递（见 agents/base.py）。
    每次 LLM 调用由网关独立记录成本/延迟（llm_call_log）。
    """
    wall_start = time.perf_counter()

    # ===== 第一阶段：诊断 ∥ 审查（并行） =====
    (diag_out, diag_llm), (review_out, review_llm) = await asyncio.gather(
        _run_agent(DiagnosisAgent(), ctx),
        _run_agent(ReviewAgent(), ctx),
    )

    diagnosis: DiagnosisOutput = diag_out or DiagnosisOutput(
        error_type="暂时不可用",
        explanation="诊断智能体本次调用失败（可能是云端模型并发限流），已自动降级。请稍后重新提交，或直接查看其它标签页内容。",
    )
    review: ReviewOutput = review_out or ReviewOutput(
        summary="审查智能体本次调用失败（可能是云端模型并发限流），已自动降级，请稍后重试。"
    )

    # 中间结果写入共享上下文（通信协议）
    ctx.diagnosis_result = diagnosis
    ctx.review_result = review

    # ===== 学情更新（阶段4）：自动标注题目概念 + 掌握度衰减 =====
    # 放在第二阶段之前：规划 Agent 随后读到的薄弱点已包含本次失败的影响。
    try:
        await knowledge.on_diagnosis(
            ctx.user_id, ctx.problem_id, ctx.language, diagnosis.concepts
        )
    except Exception as e:
        logger.warning("学情更新失败（不影响诊断流程）: %s", e)

    # ===== 第二阶段：反馈（依赖诊断）∥ 规划（依赖诊断+审查）=====
    (fb_out, fb_llm), (plan_out, plan_llm) = await asyncio.gather(
        _run_agent(FeedbackAgent(), ctx),
        _run_agent(PlanningAgent(), ctx),
    )

    feedback: FeedbackOutput = fb_out or FeedbackOutput(
        tutoring_style="",
        content="反馈智能体本次调用失败（可能是云端模型并发限流），已自动降级，请稍后重试。",
    )
    plan: PlanOutput = plan_out or PlanOutput(
        summary="规划智能体本次调用失败（可能是云端模型限流），已自动降级，请稍后重试。",
    )

    wall_ms = int((time.perf_counter() - wall_start) * 1000)

    # ===== 聚合成本与 token（llm_call_log 已逐调用记录） =====
    llms = [x for x in (diag_llm, review_llm, fb_llm, plan_llm) if x is not None]
    prompt_tokens = sum(x.prompt_tokens for x in llms)
    completion_tokens = sum(x.completion_tokens for x in llms)
    cost = sum(x.cost_yuan for x in llms)
    models_used = list(dict.fromkeys(x.model_name for x in llms if x.model_name))
    tiers_used = list(dict.fromkeys(x.tier for x in llms))

    return DiagnoseResponse(
        diagnosis=DiagnosisOut(
            error_type=diagnosis.error_type,
            root_cause=diagnosis.root_cause,
            concepts=diagnosis.concepts,
            explanation=diagnosis.explanation,
            hint=diagnosis.hint,
        ),
        feedback=FeedbackOut(
            tutoring_style=feedback.tutoring_style,
            content=feedback.content,
            guiding_questions=feedback.guiding_questions,
            code_example=feedback.code_example,
        ),
        review=ReviewOut(
            overall_score=review.overall_score,
            strengths=review.strengths,
            issues=[
                ReviewIssueOut(
                    severity=i.severity,
                    category=i.category,
                    message=i.message,
                    suggestion=i.suggestion,
                )
                for i in review.issues
            ],
            summary=review.summary,
        ),
        planning=PlanOut(
            summary=plan.summary,
            steps=[
                PlanStepOut(action=s.action, detail=s.detail) for s in plan.steps
            ],
            next_problem_hint=plan.next_problem_hint,
        ),
        meta=DiagnoseMeta(
            model=",".join(models_used) or settings.zhipu_model,
            model_tier=tiers_used[0] if len(tiers_used) == 1 else "mixed",
            latency_ms=wall_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_yuan=cost,
        ),
    )
