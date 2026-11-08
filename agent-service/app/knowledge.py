"""知识图谱与学情模型服务（阶段4 + 多语言扩展）。

数据表（backend/migrations/004、005、007、008）：
  knowledge_nodes  概念节点，按 language 分区（go / python / java / cpp）
  knowledge_edges  概念前置依赖边（language, from 是 to 的先修）
  problem_concepts 题目-概念标注（诊断命中自动累积 hit_count，按语言）
  student_mastery  学生掌握度（EMA 更新，按 language 独立计算）

掌握度算法（EMA，规则可解释，论文中作为公式呈现）：
  失败（诊断触发，即未通过）：new = old * (1 - ALPHA_FAIL)
  通过（判题 ACCEPTED）    ：new = old + ALPHA_PASS * (1 - old)
  首次接触默认 0.5；跌破 0.4 记一次"薄弱"（weakness_count）。

多语言：概念词表与学生掌握度均按语言隔离，Python 提交不会命中 Go 的「切片」。
"""
from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple

from . import db

logger = logging.getLogger("agent-service")

ALPHA_FAIL = 0.3          # 失败时向 0 衰减的步长
ALPHA_PASS = 0.4          # 通过时向 1 增强的步长
DEFAULT_MASTERY = 0.5     # 首次接触的初始掌握度
WEAK_THRESHOLD = 0.4      # 低于此值记为"薄弱"
CONCEPTS_TTL_SECONDS = 300

# 语言别名归一（与 Go 侧 sandbox.Normalize 保持一致）
_LANG_ALIASES = {
    "golang": "go",
    "py": "python",
    "python3": "python",
    "c++": "cpp",
    "cxx": "cpp",
}


def normalize_language(language: str) -> str:
    lang = (language or "go").strip().lower()
    return _LANG_ALIASES.get(lang, lang)


# DB 不可用时按语言的兜底知识点列表（与 seeds 保持一致）
DEFAULT_CONCEPTS: Dict[str, List[str]] = {
    "go": [
        "变量与常量", "基本类型", "输入输出", "运算符与表达式",
        "条件分支", "switch 分支", "for 循环", "break 与 continue",
        "数组", "切片", "map", "字符串处理",
        "函数", "多返回值", "递归", "指针",
        "结构体", "方法", "接口", "错误处理",
        "defer 与 panic", "包与导入", "排序与查找", "时间复杂度",
        "goroutine", "channel", "sync 包",
    ],
    "python": [
        "变量与赋值", "数据类型", "输入输出", "运算符",
        "字符串", "列表", "元组", "字典", "集合",
        "条件语句", "循环", "循环控制",
        "函数", "函数参数", "作用域", "异常处理",
        "类与对象", "继承与多态", "模块与导入", "文件读写",
        "列表推导式", "排序与查找", "递归",
    ],
    "java": [
        "变量与基本类型", "运算符与表达式", "输入输出",
        "条件与分支", "循环", "数组", "字符串", "集合框架",
        "方法与重载", "递归", "类与对象", "继承与多态",
        "接口与抽象类", "异常处理", "泛型",
        "包与访问控制", "静态成员", "排序与查找", "时间复杂度",
    ],
    "cpp": [
        "变量与基本类型", "运算符与表达式", "输入输出流",
        "条件分支", "循环", "数组与 vector", "string 字符串",
        "指针与引用", "函数与重载", "递归", "结构体与类",
        "构造与析构", "继承与多态", "动态内存",
        "STL 容器", "STL 算法", "异常处理", "模板", "时间复杂度",
    ],
}

_concepts_cache: Dict[str, List[str]] = {}
_concepts_loaded_at: Dict[str, float] = {}


async def get_concepts(language: str = "go") -> List[str]:
    """某语言的知识点全集，用于约束诊断 Agent 的 concepts 输出。按语言缓存 5 分钟。"""
    lang = normalize_language(language)
    cached = _concepts_cache.get(lang)
    if cached and time.time() - _concepts_loaded_at.get(lang, 0) < CONCEPTS_TTL_SECONDS:
        return cached

    rows = await db.fetch(
        "SELECT name FROM knowledge_nodes WHERE language = $1 ORDER BY category, name",
        lang,
    )
    concepts = [r["name"] for r in rows] if rows else list(DEFAULT_CONCEPTS.get(lang, []))
    if concepts:
        _concepts_cache[lang] = concepts
        _concepts_loaded_at[lang] = time.time()
    return concepts


async def on_diagnosis(
    user_id: Optional[int],
    problem_id: Optional[int],
    language: str,
    concepts: List[str],
) -> None:
    """诊断完成后调用：① 自动标注题目-概念 ② 学生掌握度衰减（EMA）。"""
    lang = normalize_language(language)
    known = await _known_concepts(lang, concepts)
    if not known:
        return
    p = db.pool()
    if p is None:
        return

    for name in known:
        if problem_id:
            try:
                await p.execute(
                    """
                    INSERT INTO problem_concepts (problem_id, language, concept_name, hit_count)
                    VALUES ($1, $2, $3, 1)
                    ON CONFLICT (problem_id, language, concept_name)
                    DO UPDATE SET hit_count = problem_concepts.hit_count + 1,
                                  updated_at = NOW()
                    """,
                    problem_id, lang, name,
                )
            except Exception as e:
                logger.warning("problem_concepts 标注失败 (%s): %s", name, e)

        if user_id:
            try:
                await _update_mastery(p, user_id, lang, name, failed=True)
            except Exception as e:
                logger.warning("student_mastery 衰减失败 (%s): %s", name, e)


async def record_outcome(user_id: int, problem_id: int, language: str = "go") -> None:
    """提交判题通过（ACCEPTED）后调用：强化该题标注概念的掌握度（EMA 增强）。

    题目在该语言下尚未标注概念时为 no-op（标注会随诊断逐渐累积）。
    """
    lang = normalize_language(language)
    p = db.pool()
    if p is None or not user_id or not problem_id:
        return
    rows = await p.fetch(
        """
        SELECT concept_name FROM problem_concepts
        WHERE problem_id = $1 AND language = $2
        ORDER BY hit_count DESC
        LIMIT 5
        """,
        problem_id, lang,
    )
    for r in rows:
        try:
            await _update_mastery(p, user_id, lang, r["concept_name"], failed=False)
        except Exception as e:
            logger.warning("record_outcome 强化失败 (%s): %s", r["concept_name"], e)


async def get_weak_concepts(
    user_id: Optional[int],
    language: str = "go",
    limit: int = 5,
) -> List[Tuple[str, float]]:
    """取学生该语言下最薄弱的知识点（掌握度 < 0.6，升序），供规划 Agent 注入学情。"""
    if not user_id:
        return []
    rows = await db.fetch(
        """
        SELECT concept_name, mastery FROM student_mastery
        WHERE user_id = $1 AND language = $2 AND mastery < 0.6
        ORDER BY mastery ASC
        LIMIT $3
        """,
        user_id, normalize_language(language), limit,
    )
    return [(r["concept_name"], float(r["mastery"])) for r in rows]


async def _known_concepts(language: str, concepts: List[str]) -> List[str]:
    """过滤出该语言图谱中存在的概念（外键保护，防止 LLM 输出越界写库）。"""
    if not concepts:
        return []
    known = set(await get_concepts(language))
    return [c for c in concepts if c in known]


async def _update_mastery(
    p,
    user_id: int,
    language: str,
    concept: str,
    *,
    failed: bool,
) -> None:
    row = await p.fetchrow(
        """
        SELECT mastery FROM student_mastery
        WHERE user_id = $1 AND language = $2 AND concept_name = $3
        """,
        user_id, language, concept,
    )
    old = float(row["mastery"]) if row else DEFAULT_MASTERY

    if failed:
        new = round(old * (1 - ALPHA_FAIL), 4)
        weak_incr = 1 if new < WEAK_THRESHOLD else 0
        await p.execute(
            """
            INSERT INTO student_mastery
                (user_id, language, concept_name, mastery, attempts, weakness_count)
            VALUES ($1, $2, $3, $4, 1, $5)
            ON CONFLICT (user_id, language, concept_name)
            DO UPDATE SET mastery = $4,
                          attempts = student_mastery.attempts + 1,
                          weakness_count = student_mastery.weakness_count + $5,
                          updated_at = NOW()
            """,
            user_id, language, concept, new, weak_incr,
        )
    else:
        new = round(old + ALPHA_PASS * (1 - old), 4)
        await p.execute(
            """
            INSERT INTO student_mastery (user_id, language, concept_name, mastery, attempts)
            VALUES ($1, $2, $3, $4, 1)
            ON CONFLICT (user_id, language, concept_name)
            DO UPDATE SET mastery = $4,
                          attempts = student_mastery.attempts + 1,
                          updated_at = NOW()
            """,
            user_id, language, concept, new,
        )
