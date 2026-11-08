"""实验数据统计分析脚本（创新点③：成本-质量联合评估）。

从数据库读取实验组/对照组的学习效果、认知负荷、推理成本与响应延迟，
输出 Markdown 报告（含 Mann-Whitney U 检验与效应量）。

依赖：仅 asyncpg（agent-service/.venv 已包含），统计检验用纯 Python 实现。

用法（必须在项目根目录或 agent-service 目录下运行，以便读取 .env）：
    cd agent-service
    .venv/Scripts/python.exe ../scripts/analysis.py --out ../docs/实验/analysis_report.md
"""
from __future__ import annotations

import argparse
import asyncio
import math
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import asyncpg

ROOT = Path(__file__).resolve().parent.parent


def load_dsn() -> str:
    """优先读环境变量，其次解析 .env（不依赖 python-dotenv）。"""
    import os

    if os.getenv("DSN"):
        return os.environ["DSN"]

    env_path = ROOT / "agent-service" / ".env"
    cfg: Dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()

    return (
        f"postgresql://{cfg.get('DB_USER', 'postgres')}:{cfg.get('DB_PASSWORD', '123456')}"
        f"@{cfg.get('DB_HOST', 'localhost')}:{cfg.get('DB_PORT', '5432')}"
        f"/{cfg.get('DB_NAME', 'programming_tutor')}"
    )


# ===================== 统计工具（纯 Python） =====================

def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def stdev(xs: Sequence[float]) -> float:
    if len(xs) < 2:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def mann_whitney_u(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float]:
    """Mann-Whitney U 检验（双侧，正态近似 + 连续性校正）。

    返回 (U, p)。小样本时正态近似偏保守，论文中建议同时报告效应量。
    """
    if not a or not b:
        return float("nan"), float("nan")

    combined = [(x, 0) for x in a] + [(x, 1) for x in b]
    combined.sort(key=lambda t: t[0])

    # 秩（处理并列取平均秩）
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1

    r_a = sum(r for r, (_, g) in zip(ranks, combined) if g == 0)
    n1, n2 = len(a), len(b)
    u1 = r_a - n1 * (n1 + 1) / 2
    u = min(u1, n1 * n2 - u1)

    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if sigma == 0:
        return u, float("nan")

    z = (u - mu + 0.5) / sigma  # 连续性校正
    p = 2 * (1 - normal_cdf(abs(z)))
    return u, min(1.0, p)


def normal_cdf(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def cliff_delta(a: Sequence[float], b: Sequence[float]) -> float:
    """Cliff's delta 效应量（-1~1，|d|<0.147 可忽略，<0.33 小，<0.474 中，其余大）。"""
    if not a or not b:
        return float("nan")
    greater = sum(1 for x in a for y in b if x > y)
    less = sum(1 for x in a for y in b if x < y)
    return (greater - less) / (len(a) * len(b))


def effect_label(d: float) -> str:
    if math.isnan(d):
        return "—"
    ad = abs(d)
    if ad < 0.147:
        return "可忽略"
    if ad < 0.33:
        return "小"
    if ad < 0.474:
        return "中等"
    return "大"


def fmt(x: float, digits: int = 2) -> str:
    if x is None or math.isnan(x):
        return "—"
    return f"{x:.{digits}f}"


# ===================== 数据读取 =====================

async def collect(conn: asyncpg.Connection) -> Dict[str, Dict[str, List[float]]]:
    """按组收集各指标样本。"""
    groups = await conn.fetch(
        "SELECT user_id, group_name FROM experiment_groups"
    )
    gmap = {r["user_id"]: r["group_name"] for r in groups}

    data: Dict[str, Dict[str, List[float]]] = {
        "experimental": {k: [] for k in
                         ("pre", "post", "gain", "tlx", "latency", "cost", "tokens")},
        "control": {k: [] for k in
                    ("pre", "post", "gain", "tlx", "latency", "cost", "tokens")},
    }

    scores = await conn.fetch(
        "SELECT user_id, phase, score, max_score FROM assessment_scores"
    )
    pre: Dict[int, float] = {}
    post: Dict[int, float] = {}
    for r in scores:
        g = gmap.get(r["user_id"])
        if g not in data:
            continue
        pct = r["score"] / r["max_score"] * 100
        (pre if r["phase"] == "pre" else post)[r["user_id"]] = pct
        data[g][r["phase"]].append(pct)

    for uid, g in gmap.items():
        if g not in data:
            continue
        if uid in pre and uid in post:
            data[g]["gain"].append(post[uid] - pre[uid])

    tlx = await conn.fetch("SELECT user_id, weighted FROM nasa_tlx")
    for r in tlx:
        g = gmap.get(r["user_id"])
        if g in data and r["weighted"] is not None:
            data[g]["tlx"].append(float(r["weighted"]))

    # 推理成本/延迟：按该组学生的诊断调用记录聚合（每次诊断一条）
    stats = await conn.fetch(
        """
        SELECT d.user_id, d.latency_ms, COALESCE(l.cost, 0) AS cost
        FROM submission_diagnosis d
        LEFT JOIN (
            SELECT submission_id, SUM(cost_yuan) AS cost
            FROM llm_call_log
            GROUP BY submission_id
        ) l ON l.submission_id = d.submission_id
        """
    )
    for r in stats:
        g = gmap.get(r["user_id"])
        if g in data:
            data[g]["latency"].append(float(r["latency_ms"] or 0))
            data[g]["cost"].append(float(r["cost"] or 0))

    # Token 消耗：免费额度下 cost_yuan 恒为 0，用 Token 作为推理成本的代理指标。
    # 口径与 latency/cost 一致：按「每次诊断」计（总 Token / 诊断次数）。
    tokens = await conn.fetch(
        """
        SELECT l.user_id,
               SUM(l.prompt_tokens + l.completion_tokens)::float
                 / GREATEST(COUNT(DISTINCT l.submission_id), 1) AS tokens_per_diag
        FROM llm_call_log l
        WHERE l.submission_id IS NOT NULL
        GROUP BY l.user_id
        """
    )
    for r in tokens:
        g = gmap.get(r["user_id"])
        if g in data and r["tokens_per_diag"]:
            data[g]["tokens"].append(float(r["tokens_per_diag"]))

    return data


# ===================== 报告生成 =====================

METRICS = [
    ("pre", "前测得分（%）", 1, "学习基线"),
    ("post", "后测得分（%）", 1, "学习效果"),
    ("gain", "增益（后测-前测，%）", 1, "**H1 学习效果**"),
    ("tlx", "NASA-TLX 加权分", 1, "**H2 认知负荷**"),
    ("latency", "诊断响应延迟（ms）", 0, "**H3 响应延迟**"),
    ("tokens", "每次诊断 Token 消耗", 0, "**H3 推理成本（代理指标）**"),
    ("cost", "每次诊断实际计费（元）", 4, "H3 推理成本（实际）"),
]


def build_report(data: Dict[str, Dict[str, List[float]]]) -> str:
    exp, ctrl = data["experimental"], data["control"]
    lines: List[str] = []

    lines.append("# 实验数据分析报告（自动生成）\n")
    lines.append("> 由 `scripts/analysis.py` 生成。数据源：experiment_groups / "
                 "assessment_scores / nasa_tlx / submission_diagnosis / llm_call_log。\n")

    lines.append("## 1. 样本\n")
    lines.append("| 组别 | 学生数 |\n|---|---|")
    lines.append(f"| 实验组（协同） | {len(exp['gain']) or len(exp['post'])} |")
    lines.append(f"| 对照组（全云端） | {len(ctrl['gain']) or len(ctrl['post'])} |\n")

    lines.append("## 2. 指标对比\n")
    lines.append("| 指标 | 实验组 均值±标准差 (n) | 对照组 均值±标准差 (n) | U | p | Cliff's δ | 效应 |")
    lines.append("|---|---|---|---|---|---|---|")

    for key, label, digits, _note in METRICS:
        a, b = exp[key], ctrl[key]
        u, p = mann_whitney_u(a, b)
        d = cliff_delta(a, b)
        sig = ""
        if not math.isnan(p):
            sig = " ***" if p < 0.001 else " **" if p < 0.01 else " *" if p < 0.05 else ""
        lines.append(
            f"| {label} | {fmt(mean(a), digits)}±{fmt(stdev(a), digits)} ({len(a)}) "
            f"| {fmt(mean(b), digits)}±{fmt(stdev(b), digits)} ({len(b)}) "
            f"| {fmt(u, 1)} | {fmt(p, 4)}{sig} | {fmt(d, 3)} | {effect_label(d)} |"
        )

    lines.append("\n注：* p<0.05，** p<0.01，*** p<0.001。"
                 "U 为 Mann-Whitney U 统计量；δ 为 Cliff's delta 效应量。\n")

    lines.append("## 3. 假设检验结论\n")
    lines.extend(_hypothesis_lines(exp, ctrl))

    lines.append("\n## 4. 成本-质量联合评估（创新点③）\n")
    lines.extend(_cost_quality_lines(exp, ctrl))

    lines.append("\n## 5. 明细数据\n")
    for grp_name, grp in (("实验组", exp), ("对照组", ctrl)):
        lines.append(f"### {grp_name}\n")
        for key, label, digits, _ in METRICS:
            vals = grp[key]
            if vals:
                lines.append(f"- {label}: "
                             f"{', '.join(fmt(v, digits) for v in vals)}")
        lines.append("")

    return "\n".join(lines)


def _hypothesis_lines(exp, ctrl) -> List[str]:
    out: List[str] = []

    def judge(a, b, higher_better: bool, h: str, desc: str):
        if not a or not b:
            out.append(f"- {h}：样本不足，暂无法检验。")
            return
        ma, mb = mean(a), mean(b)
        u, p = mann_whitney_u(a, b)
        d = cliff_delta(a, b)
        better = ma > mb if higher_better else ma < mb
        verdict = "支持" if better and p < 0.05 else (
            "部分支持（方向一致但未达显著）" if better else "不支持")
        out.append(
            f"- **{h}** {desc}：实验组 {fmt(ma)} vs 对照组 {fmt(mb)}，"
            f"p={fmt(p, 4)}，δ={fmt(d, 3)}（{effect_label(d)}）→ **{verdict}**"
        )

    judge(exp["gain"], ctrl["gain"], True, "H1", "学习效果增益")
    judge(exp["tlx"], ctrl["tlx"], False, "H2", "认知负荷")
    judge(exp["latency"], ctrl["latency"], False, "H3a", "响应延迟")
    judge(exp["tokens"], ctrl["tokens"], False, "H3b", "Token 消耗")
    if exp["cost"] or ctrl["cost"]:
        judge(exp["cost"], ctrl["cost"], False, "H3c", "实际计费成本")
    else:
        out.append("- **H3c** 实际计费成本：两侧均为 0（云端使用免费额度），"
                   "故以 Token 消耗作为成本代理指标。")
    return out


def _cost_quality_lines(exp, ctrl) -> List[str]:
    out: List[str] = []
    if not (exp["gain"] and ctrl["gain"]):
        return ["样本不足，无法计算成本-质量综合指标。"]

    g_exp, g_ctrl = mean(exp["gain"]), mean(ctrl["gain"])
    cost_exp = mean(exp["cost"]) if exp["cost"] else 0.0
    cost_ctrl = mean(ctrl["cost"]) if ctrl["cost"] else 0.0
    lat_exp = mean(exp["latency"]) if exp["latency"] else 0.0
    lat_ctrl = mean(ctrl["latency"]) if ctrl["latency"] else 0.0
    tok_exp = mean(exp["tokens"]) if exp["tokens"] else 0.0
    tok_ctrl = mean(ctrl["tokens"]) if ctrl["tokens"] else 0.0

    out.append("| 指标 | 实验组 | 对照组 | 相对变化 |")
    out.append("|---|---|---|---|")

    def rel(a, b):
        if not b:
            return "—"
        return f"{(a - b) / b * 100:+.1f}%"

    out.append(f"| 学习增益 | {fmt(g_exp)} | {fmt(g_ctrl)} | {rel(g_exp, g_ctrl)} |")
    out.append(f"| 每次诊断 Token | {fmt(tok_exp, 0)} | {fmt(tok_ctrl, 0)} | {rel(tok_exp, tok_ctrl)} |")
    out.append(f"| 推理成本/次 | {fmt(cost_exp, 4)} | {fmt(cost_ctrl, 4)} | {rel(cost_exp, cost_ctrl)} |")
    out.append(f"| 响应延迟 | {fmt(lat_exp, 0)} ms | {fmt(lat_ctrl, 0)} ms | {rel(lat_exp, lat_ctrl)} |")

    out.append("")
    out.append("> 成本以「Token 消耗」为主指标：端侧模型不产生 API 费用，"
               "云端当前使用免费额度，实际计费为 0；若按商用单价折算，"
               "成本差异与 Token 差异同向。")

    out.append("")
    if g_exp >= g_ctrl and tok_exp < tok_ctrl:
        out.append("**结论**：在保持（或提升）学习效果的同时降低了 Token 消耗与响应延迟，"
                   "**支持**开题书「成本感知调度」与「成本-质量联合评估」的可行性。")
    elif g_exp >= g_ctrl:
        out.append("**结论**：学习效果不劣于基线，但 Token 优势未体现，需检查路由命中率。")
    else:
        out.append("**结论**：学习效果低于基线，需分析路由策略是否牺牲了辅导质量。")
    return out


async def main() -> None:
    ap = argparse.ArgumentParser(description="实验数据分析")
    ap.add_argument("--out", default=str(ROOT / "docs" / "实验" / "analysis_report.md"))
    args = ap.parse_args()

    conn = await asyncpg.connect(load_dsn())
    try:
        data = await collect(conn)
    finally:
        await conn.close()

    report = build_report(data)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n已写入：{out_path}")


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(main())
