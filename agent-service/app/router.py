from __future__ import annotations

"""轻量级路由决策器（开题书创新点①②的落地）。

规则式、可解释、零额外推理成本。决策依据：
  任务类型（Agent 角色） x 上下文复杂度 x 成本预算 -> cloud | edge

规则表（论文可直接引用的设计依据）：
  | Agent     | 走端侧 edge                        | 走云端 cloud                    |
  |-----------|-----------------------------------|--------------------------------|
  | diagnosis | 编译错误且代码短（模式匹配即可）      | 语义/逻辑推理（默认）             |
  | review    | 代码 <= 2000 字符                   | 长代码                          |
  | feedback  | direct_hint（低阶错误，模板化提示）   | socratic/scaffold（教学措辞质量） |
  | planning  | 薄弱点少且代码质量分高               | 需全局学情推理（默认）            |

全局约束：
  - ROUTER_FORCE_TIER=cloud/edge 强制指定全部调用走向（对照组实验开关）
  - 累计成本超过 ROUTER_BUDGET_YUAN 时强制端侧（成本感知调度）
"""

from .config import settings

_accumulated_cost_yuan = 0.0


def add_cost(yuan: float) -> None:
    """网关在每次调用后累计成本，供预算约束判断。"""
    global _accumulated_cost_yuan
    _accumulated_cost_yuan += yuan


def accumulated_cost() -> float:
    return _accumulated_cost_yuan


def decide(agent_role: str, ctx, routing_hint=None) -> str:
    """按任务类型与上下文选择模型规模，返回 'cloud' 或 'edge'。"""
    force = (settings.router_force_tier or "").strip().lower()
    if force in ("cloud", "edge"):
        return force

    # 成本预算兜底：累计成本超阈值后强制端侧（成本感知调度）
    if (
        settings.router_budget_yuan > 0
        and _accumulated_cost_yuan >= settings.router_budget_yuan
    ):
        return "edge"

    judge = getattr(ctx, "judge_result", None)
    status = getattr(judge, "status", "") or ""
    code_len = len(getattr(ctx, "code", "") or "")

    diagnosis = getattr(ctx, "diagnosis_result", None)
    concepts = list(getattr(diagnosis, "concepts", []) or [])

    review = getattr(ctx, "review_result", None)
    score = getattr(review, "overall_score", 0) or 0

    if agent_role == "diagnosis":
        # 编译错误：报错信息明确、模式匹配即可 -> 端侧
        if status == "COMPILE_ERROR" and code_len <= 1500:
            return "edge"
        # 逻辑/算法错误需要多步语义推理 -> 云端
        return "cloud"

    if agent_role == "review":
        # 代码质量审查是静态启发任务，短代码端侧即可
        return "edge" if code_len <= 2000 else "cloud"

    if agent_role == "feedback":
        # 低阶错误给直接提示即可；启发式/分步引导需要教学措辞质量 -> 云端
        return "edge" if routing_hint == "direct_hint" else "cloud"

    if agent_role == "planning":
        # 薄弱知识点少且代码质量好 -> 端侧；否则需要全局学情推理 -> 云端
        return "edge" if len(concepts) <= 2 and score >= 80 else "cloud"

    return "cloud"
