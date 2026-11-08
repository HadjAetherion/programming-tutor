from __future__ import annotations

import json
from typing import List, Tuple

from .. import knowledge
from ..llm.client import LLMResponse
from ..llm.gateway import ModelGateway
from .base import (
    Agent,
    AgentContext,
    DiagnosisOutput,
    PlanOutput,
    PlanStep,
    ReviewOutput,
    language_label,
)

SYSTEM_PROMPT = """你是一名 {LANG} 课程的学习规划老师，在在线编程学习系统中根据诊断与审查结果，为学生生成下一步学习规划。

你会收到：诊断结论（错误类型/薄弱知识点）、审查结论（代码质量评分与问题）、评测状态、学生学情（学情模型维护的历史薄弱知识点及掌握度）。

请以 **JSON** 输出：
{
  "summary": "一段话总结当前学习状态，语气鼓励",
  "steps": [
    {"action": "行动名，如 复习/修改重交/巩固练习/反思总结", "detail": "具体做什么，一句话"}
  ],
  "next_problem_hint": "建议下一道练什么类型/知识点的题，一句话（不需要具体题号）"
}

要求：
- steps 为 2-4 条，按优先级排序，具体可执行
- 围绕诊断出的薄弱知识点展开；若提供了学生学情，优先针对掌握度最低的知识点
- 学情与诊断结论冲突时，以本次诊断结论为主
- 全程中文；只输出 JSON"""


class PlanningAgent(Agent):
    name = "planning"

    def build_messages(
        self,
        ctx: AgentContext,
        diagnosis: DiagnosisOutput,
        review: ReviewOutput,
        mastery_lines: List[str],
    ) -> List[dict]:
        issues_text = "\n".join(
            f"- [{i.severity}] {i.category}: {i.message}" for i in review.issues
        ) or "无显著问题"
        mastery_text = (
            "\n".join(f"- {line}" for line in mastery_lines)
            if mastery_lines
            else "暂无学情记录，可依据诊断结论推断"
        )
        lang = language_label(ctx.language)

        user = f"""## 题目
标题：{ctx.problem.title}

## 评测结果
状态：{ctx.judge_result.status}
通过用例：{ctx.judge_result.passed_tests}/{ctx.judge_result.total_tests}

## 诊断结论
错误类型：{diagnosis.error_type}
根因：{diagnosis.root_cause}
薄弱知识点：{', '.join(diagnosis.concepts)}

## 审查结论
代码质量评分：{review.overall_score}/100
问题清单：
{issues_text}

## 学生学情（来自学情模型，掌握度 0~1，越低越薄弱）
{mastery_text}
"""
        return [
            {"role": "system", "content": SYSTEM_PROMPT.replace("{LANG}", lang)},
            {"role": "user", "content": user},
        ]

    async def run(
        self,
        ctx: AgentContext,
        gateway: ModelGateway,
    ) -> Tuple[PlanOutput, LLMResponse]:
        if ctx.diagnosis_result is None:
            raise ValueError("PlanningAgent 需要 diagnosis_result")

        review = ctx.review_result or ReviewOutput()

        weak = await knowledge.get_weak_concepts(ctx.user_id, ctx.language)
        mastery_lines = [f"{name}（掌握度 {m:.2f}）" for name, m in weak]
        messages = self.build_messages(ctx, ctx.diagnosis_result, review, mastery_lines)
        resp = await gateway.complete(
            messages,
            agent_role=self.name,
            user_id=ctx.user_id,
            submission_id=ctx.submission_id,
            ctx=ctx,
            # 规划步骤较多，1024 会截断 JSON（实测输出恰好 1024 tokens 导致解析为空）
            max_tokens=1536,
        )
        return self._parse(resp.content), resp

    @staticmethod
    def _parse(content: str) -> PlanOutput:
        data = _extract_json(content)
        if data is None:
            return PlanOutput(summary=content.strip()[:200])
        steps = []
        for item in data.get("steps") or []:
            if not isinstance(item, dict):
                continue
            steps.append(
                PlanStep(
                    action=str(item.get("action", "")),
                    detail=str(item.get("detail", "")),
                )
            )
        return PlanOutput(
            summary=str(data.get("summary", "")),
            steps=steps,
            next_problem_hint=str(data.get("next_problem_hint", "")),
        )


def _extract_json(content: str):
    s = content.strip()
    if s.startswith("```"):
        s = s[3:]
        if s[:4].lower() == "json":
            s = s[4:]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = s[start : end + 1]
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            return None
    return None
