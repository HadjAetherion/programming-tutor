from __future__ import annotations

import json
from typing import List, Tuple

from ..llm.client import LLMResponse
from ..llm.gateway import ModelGateway
from .base import Agent, AgentContext, DiagnosisOutput, FeedbackOutput, language_label

SYSTEM_PROMPT = """你是一名耐心的 {LANG} 编程辅导老师，在在线编程学习系统中根据诊断结果对学生进行个性化辅导。

你会收到：
1. 题目与学生代码、评测结果
2. 诊断 Agent 的诊断结论（错误类型/根因/涉及知识点）
3. 系统为你选定的**干预策略**（tutoring_style），你必须严格按该策略生成辅导内容

三种干预策略的定义：
- direct_hint（直接提示）：适用于编译错误等低阶问题。直接指出错误位置和原因，让学生改正，无需绕弯子。
- socratic（苏格拉底式提问）：适用于接近正确的逻辑错误。不直接说答案，通过 2-3 个层层递进的问题引导学生自己发现错误。
- scaffold（分步引导）：适用于离正确解法较远的情况。把题目拆解成 2-4 个小步骤，逐步引导，可给一个极小的代码片段示意（不能是完整解法）。

通用要求：
- 全程使用中文，语气鼓励、不评判
- 永远不要直接给出完整正确代码（scaffold 也只允许极小片段）
- 内容不超过 250 字

请以 **JSON** 输出：
{
  "content": "按策略生成的辅导内容",
  "guiding_questions": ["引导问题1", "问题2"],
  "code_example": "仅 scaffold 策略时给极小片段，其他策略留空字符串"
}

只输出 JSON。"""

# 干预策略选择规则（规则式、可解释——论文中作为自适应策略依据呈现）
STYLE_RULES_DOC = """
| 错误类型 | 通过率 | 策略 |
|---|---|---|
| COMPILE_ERROR | 任意 | direct_hint |
| RUNTIME_ERROR | 任意 | socratic |
| WRONG_ANSWER | >=0.6 | socratic |
| WRONG_ANSWER | <0.6 | scaffold |
| TIME_LIMIT | 任意 | socratic |
| 其他 | 任意 | scaffold |
"""


def decide_style(judge_status: str, passed: int, total: int) -> str:
    """根据错误类型与通过率选择干预策略（自适应辅导的核心规则）。"""
    ratio = (passed / total) if total and total > 0 else 0.0

    if judge_status == "COMPILE_ERROR":
        return "direct_hint"
    if judge_status == "RUNTIME_ERROR":
        return "socratic"
    if judge_status == "WRONG_ANSWER":
        return "socratic" if ratio >= 0.6 else "scaffold"
    if judge_status == "TIME_LIMIT":
        return "socratic"
    return "scaffold"


class FeedbackAgent(Agent):
    name = "feedback"

    def build_messages(
        self,
        ctx: AgentContext,
        diagnosis: DiagnosisOutput,
        style: str,
    ) -> List[dict]:
        passed = ctx.judge_result.passed_tests
        total = ctx.judge_result.total_tests
        lang = language_label(ctx.language)
        user = f"""## 题目
标题：{ctx.problem.title}
描述：{ctx.problem.description}
示例输入：{ctx.problem.sample_input}
示例输出：{ctx.problem.sample_output}

## 学生代码（{lang}）
```{ctx.language}
{ctx.code}
```

## 评测结果
状态：{ctx.judge_result.status}
通过用例：{passed}/{total}
错误输出：
{ctx.judge_result.stderr}

## 诊断结论（来自诊断 Agent）
错误类型：{diagnosis.error_type}
根因：{diagnosis.root_cause}
涉及知识点：{', '.join(diagnosis.concepts)}

## 系统选定的干预策略
{style}
"""
        return [
            {"role": "system", "content": SYSTEM_PROMPT.replace("{LANG}", lang)},
            {"role": "user", "content": user},
        ]

    async def run(
        self,
        ctx: AgentContext,
        gateway: ModelGateway,
    ) -> Tuple[FeedbackOutput, LLMResponse]:
        if ctx.diagnosis_result is None:
            raise ValueError("FeedbackAgent 需要 diagnosis_result（请先运行诊断 Agent）")

        style = decide_style(
            ctx.judge_result.status,
            ctx.judge_result.passed_tests or 0,
            ctx.judge_result.total_tests or 0,
        )

        messages = self.build_messages(ctx, ctx.diagnosis_result, style)
        resp = await gateway.complete(
            messages,
            agent_role=self.name,
            user_id=ctx.user_id,
            submission_id=ctx.submission_id,
            ctx=ctx,
            routing_hint=style,
        )
        return self._parse(resp.content, style), resp

    @staticmethod
    def _parse(content: str, style: str) -> FeedbackOutput:
        data = _extract_json(content)
        if data is None:
            return FeedbackOutput(
                tutoring_style=style,
                content=content.strip(),
            )
        questions = data.get("guiding_questions") or []
        if isinstance(questions, str):
            questions = [questions]
        return FeedbackOutput(
            tutoring_style=str(data.get("tutoring_style", style)) or style,
            content=str(data.get("content", "")),
            guiding_questions=[str(q) for q in questions],
            code_example=str(data.get("code_example", "") or ""),
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
