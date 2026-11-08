from __future__ import annotations

import json
from typing import List, Tuple

from .. import knowledge
from ..llm.client import LLMResponse
from ..llm.gateway import ModelGateway
from .base import Agent, AgentContext, DiagnosisOutput, language_label

SYSTEM_PROMPT = """你是一名资深的 {LANG} 编程教学专家，擅长诊断学生代码中的错误并给出启发式辅导。

你的任务：分析学生的 Go 代码与评测结果，诊断错误类型与根因，并给出**苏格拉底式**的辅导——多用提问引导学生自己发现错误，而不是直接给出完整正确答案。

请以 **JSON** 输出，字段如下：
{
  "error_type": "错误类型，从以下选一：语法错误/编译错误/逻辑错误/算法错误/边界错误/运行时错误",
  "root_cause": "用一句话指出错误的根本原因",
  "concepts": ["命中的知识点，只能从用户消息提供的《知识点列表》中选择，可多个"],
  "explanation": "给学生的讲解：先点出问题所在，再用提问引导（苏格拉底式），不超过200字",
  "hint": "下一步具体提示，一句话"
}

注意：只输出 JSON，不要输出多余文字。"""


class DiagnosisAgent(Agent):
    name = "diagnosis"

    def build_messages(self, ctx: AgentContext, concepts: List[str]) -> List[dict]:
        lang = language_label(ctx.language)
        user = f"""## 题目
标题：{ctx.problem.title}
描述：{ctx.problem.description}
输入说明：{ctx.problem.input_description}
输出说明：{ctx.problem.output_description}
约束：{ctx.problem.constraints}
示例输入：{ctx.problem.sample_input}
示例输出：{ctx.problem.sample_output}

## 学生代码（{lang}）
```{ctx.language}
{ctx.code}
```

## 评测结果
状态：{ctx.judge_result.status}
通过用例：{ctx.judge_result.passed_tests}/{ctx.judge_result.total_tests}
退出码：{ctx.judge_result.exit_code}
标准输出：
{ctx.judge_result.stdout}
错误输出：
{ctx.judge_result.stderr}

## 知识点列表（concepts 字段只能从中选择，没有完全符合的选最接近的）
{'、'.join(concepts)}
"""
        return [
            {"role": "system", "content": SYSTEM_PROMPT.replace("{LANG}", lang)},
            {"role": "user", "content": user},
        ]

    async def run(
        self,
        ctx: AgentContext,
        gateway: ModelGateway,
    ) -> Tuple[DiagnosisOutput, LLMResponse]:
        concepts = await knowledge.get_concepts(ctx.language)
        messages = self.build_messages(ctx, concepts)
        resp = await gateway.complete(
            messages,
            agent_role=self.name,
            user_id=ctx.user_id,
            submission_id=ctx.submission_id,
            ctx=ctx,
        )
        return self._parse(resp.content), resp

    @staticmethod
    def _parse(content: str) -> DiagnosisOutput:
        data = _extract_json(content)
        if data is None:
            return DiagnosisOutput(
                error_type="未知",
                explanation=content.strip(),
            )
        concepts = data.get("concepts") or []
        if isinstance(concepts, str):
            concepts = [concepts]
        return DiagnosisOutput(
            error_type=str(data.get("error_type", "未知")),
            root_cause=str(data.get("root_cause", "")),
            concepts=[str(c) for c in concepts],
            explanation=str(data.get("explanation", "")),
            hint=str(data.get("hint", "")),
        )


def _extract_json(content: str):
    """从模型输出中提取 JSON 对象，兼容 ```json``` 包裹与多余文字。"""
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
