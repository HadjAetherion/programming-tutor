-- 阶段4：知识图谱 + 学情模型
-- psql -d programming_tutor -f 004_knowledge_mastery.sql

-- 知识节点：Go 概念体系（name 作为主键，便于 LLM 输出直接匹配）
CREATE TABLE IF NOT EXISTS knowledge_nodes (
    name        VARCHAR(64) PRIMARY KEY,
    description TEXT        NOT NULL DEFAULT '',
    category    VARCHAR(32) NOT NULL DEFAULT '',   -- 基础/流程控制/数据结构/函数/面向对象/进阶/并发
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 知识边：前置依赖（from_node 是 to_node 的先修概念）
CREATE TABLE IF NOT EXISTS knowledge_edges (
    from_node VARCHAR(64) NOT NULL REFERENCES knowledge_nodes(name) ON DELETE CASCADE,
    to_node   VARCHAR(64) NOT NULL REFERENCES knowledge_nodes(name) ON DELETE CASCADE,
    PRIMARY KEY (from_node, to_node)
);

-- 题目-概念标注：诊断命中自动累积（hit_count 反映该题常考概念）
CREATE TABLE IF NOT EXISTS problem_concepts (
    problem_id   BIGINT      NOT NULL,
    concept_name VARCHAR(64) NOT NULL REFERENCES knowledge_nodes(name) ON DELETE CASCADE,
    hit_count    INT         NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (problem_id, concept_name)
);

-- 学生掌握度：EMA 更新，失败衰减 / 通过增强
CREATE TABLE IF NOT EXISTS student_mastery (
    user_id        BIGINT          NOT NULL,
    concept_name   VARCHAR(64)     NOT NULL REFERENCES knowledge_nodes(name) ON DELETE CASCADE,
    mastery        REAL            NOT NULL DEFAULT 0.5,  -- 0~1
    attempts       INT             NOT NULL DEFAULT 0,
    weakness_count INT             NOT NULL DEFAULT 0,    -- 掌握度跌破 0.4 的次数
    updated_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, concept_name)
);
CREATE INDEX IF NOT EXISTS idx_student_mastery_user
    ON student_mastery(user_id, mastery ASC);
