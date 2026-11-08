"""实验数据录入工具（分组 / 前后测 / NASA-TLX）。

用法：
    python scripts/experiment_admin.py group  --email a@x.com --group experimental
    python scripts/experiment_admin.py score  --email a@x.com --phase pre  --score 45
    python scripts/experiment_admin.py tlx    --email a@x.com --mental 70 --physical 20 \
        --temporal 60 --performance 40 --effort 75 --frustration 55
    python scripts/experiment_admin.py list

依赖：仅 asyncpg（agent-service/.venv 已包含）。
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parent.parent


def load_dsn() -> str:
    import os

    if os.getenv("DSN"):
        return os.environ["DSN"]

    env_path = ROOT / "agent-service" / ".env"
    cfg = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()

    return (
        f"postgresql://{cfg.get('DB_USER', 'postgres')}:{cfg.get('DB_PASSWORD', '123456')}"
        f"@{cfg.get('DB_HOST', 'localhost')}:{cfg.get('DB_PORT', '5432')}"
        f"/{cfg.get('DB_NAME', 'programming_tutor')}"
    )


async def user_id_by_email(conn: asyncpg.Connection, email: str) -> int:
    uid = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
    if uid is None:
        raise SystemExit(f"找不到用户：{email}")
    return uid


async def cmd_group(conn, args) -> None:
    uid = await user_id_by_email(conn, args.email)
    await conn.execute(
        """
        INSERT INTO experiment_groups (user_id, group_name, note)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE SET group_name = $2, note = $3
        """,
        uid, args.group, args.note or "",
    )
    print(f"用户 {args.email} (id={uid}) → {args.group}")


async def cmd_score(conn, args) -> None:
    uid = await user_id_by_email(conn, args.email)
    await conn.execute(
        """
        INSERT INTO assessment_scores (user_id, phase, score, max_score)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id, phase) DO UPDATE SET score = $3, max_score = $4
        """,
        uid, args.phase, args.score, args.max_score,
    )
    pct = args.score / args.max_score * 100
    print(f"用户 {args.email} 的 {args.phase} 成绩：{args.score}/{args.max_score}（{pct:.1f}%）")


async def cmd_tlx(conn, args) -> None:
    uid = await user_id_by_email(conn, args.email)
    dims = [args.mental, args.physical, args.temporal,
            args.performance, args.effort, args.frustration]
    weighted = sum(dims) / len(dims)
    await conn.execute(
        """
        INSERT INTO nasa_tlx (user_id, mental, physical, temporal,
                              performance, effort, frustration, weighted)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (user_id) DO UPDATE SET
            mental = $2, physical = $3, temporal = $4,
            performance = $5, effort = $6, frustration = $7, weighted = $8
        """,
        uid, *dims, weighted,
    )
    print(f"用户 {args.email} 的 NASA-TLX 未加权总分：{weighted:.1f}")


async def cmd_list(conn, args) -> None:
    rows = await conn.fetch(
        """
        SELECT u.email, g.group_name,
               pre.score AS pre_score, post.score AS post_score,
               t.weighted AS tlx
        FROM users u
        LEFT JOIN experiment_groups g ON g.user_id = u.id
        LEFT JOIN assessment_scores pre  ON pre.user_id = u.id AND pre.phase = 'pre'
        LEFT JOIN assessment_scores post ON post.user_id = u.id AND post.phase = 'post'
        LEFT JOIN nasa_tlx t ON t.user_id = u.id
        WHERE g.user_id IS NOT NULL
        ORDER BY g.group_name, u.email
        """
    )
    if not rows:
        print("暂无实验数据")
        return
    print(f"{'组别':<14}{'邮箱':<32}{'前测':>8}{'后测':>8}{'TLX':>8}")
    for r in rows:
        pre = "-" if r["pre_score"] is None else f"{r['pre_score']:.0f}"
        post = "-" if r["post_score"] is None else f"{r['post_score']:.0f}"
        tlx = "-" if r["tlx"] is None else f"{r['tlx']:.1f}"
        print(f"{r['group_name']:<14}{r['email']:<32}{pre:>8}{post:>8}{tlx:>8}")


async def main() -> None:
    ap = argparse.ArgumentParser(description="实验数据录入")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("group", help="设置学生分组")
    p.add_argument("--email", required=True)
    p.add_argument("--group", required=True, choices=["experimental", "control"])
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_group)

    p = sub.add_parser("score", help="录入前测/后测成绩")
    p.add_argument("--email", required=True)
    p.add_argument("--phase", required=True, choices=["pre", "post"])
    p.add_argument("--score", type=float, required=True)
    p.add_argument("--max-score", dest="max_score", type=float, default=100)
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("tlx", help="录入 NASA-TLX")
    p.add_argument("--email", required=True)
    for name in ("mental", "physical", "temporal", "performance", "effort", "frustration"):
        p.add_argument(f"--{name}", type=float, required=True)
    p.set_defaults(func=cmd_tlx)

    p = sub.add_parser("list", help="查看已录入的实验数据")
    p.set_defaults(func=cmd_list)

    args = ap.parse_args()

    conn = await asyncpg.connect(load_dsn())
    try:
        await args.func(conn, args)
    finally:
        await conn.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(main())
