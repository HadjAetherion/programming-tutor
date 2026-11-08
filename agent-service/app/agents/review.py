from __future__ import annotations

import json
from typing import List, Tuple

from ..llm.client import LLMResponse
from ..llm.gateway import ModelGateway
from .base import Agent, AgentContext, ReviewIssue, ReviewOutput, language_label

SYSTEM_PROMPT = """你是一名资深的 {LANG} 代码审查专家（Code Reviewer），在在线编程教学系统中工作。

你的职责：审查学生提交代码的**代码质量**（正确性诊断由另一个 Agent 负责，你不要越界分析对错、不要泄露正确解法）。

审查维度：命名规范、程序结构、边界处理、{LANG} 语言惯例（idiom）、性能意识、可读性。

请以 **JSON** 输出：
{
  "overall_score": 0到100的整数评分,
  "strengths": ["做得好的点，1-3条"],
  "issues": [
    {
      "severity": "high/medium/low",
      "category": "命名/结构/边界/{LANG}惯例/性能/可读性 之一",
      "message": "问题描述，一句话",
      "suggestion": "改进建议，一句话，不给出完整正确代码"
    }
  ],
  "summary": "一段话总体评价，面向学生，语气鼓励"
}

注意：issues 可以为空数组（代码质量好时）；只输出 JSON。"""


class ReviewAgent(Agent):
    name = "review"

    def build_messages(self, ctx: AgentContext) -> List[dict]:
        lang = language_label(ctx.language)
        user = f"""## 题目
标题：{ctx.problem.title}
描述：{ctx.problem.description}
约束：{ctx.problem.constraints}

## 学生代码（{lang}）
```{ctx.language}
{ctx.code}
```

## 评测状态（仅供背景参考，不要分析对错）
{ctx.judge_result.status}
"""
        return [
            {"role": "system", "content": SYSTEM_PROMPT.replace("{LANG}", lang)},
            {"role": "user", "content": user},
        ]

    async def run(
        self,
        ctx: AgentContext,
        gateway: ModelGateway,
    ) -> Tuple[ReviewOutput, LLMResponse]:
        messages = self.build_messages(ctx)
        resp = await gateway.complete(
            messages,
            agent_role=self.name,
            user_id=ctx.user_id,
            submission_id=ctx.submission_id,
            ctx=ctx,
        )
        return self._parse(resp.content), resp

    @staticmethod
    def _parse(content: str) -> ReviewOutput:
        data = _extract_json(content)
        if data is None:
            return ReviewOutput(summary=content.strip()[:200])
        issues = []
        for item in data.get("issues") or []:
            if not isinstance(item, dict):
                continue
            issues.append(
                ReviewIssue(
                    severity=str(item.get("severity", "medium")),
                    category=str(item.get("category", "")),
                    message=str(item.get("message", "")),
                    suggestion=str(item.get("suggestion", "")),
                )
            )
        strengths = data.get("strengths") or []
        if isinstance(strengths, str):
            strengths = [strengths]
        return ReviewOutput(
            overall_score=_to_int(data.get("overall_score"), 0),
            strengths=[str(s) for s in strengths],
            issues=issues,
            summary=str(data.get("summary", "")),
        )


def _to_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
