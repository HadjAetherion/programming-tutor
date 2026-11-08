-- 010：准实验数据表（分组 / 前后测成绩 / NASA-TLX 认知负荷）
-- psql -d programming_tutor -f 010_experiment_tables.sql

-- 实验分组：experimental=大小模型协同（路由开启），control=全云端（ROUTER_FORCE_TIER=cloud）
CREATE TABLE IF NOT EXISTS experiment_groups (
    user_id    BIGINT PRIMARY KEY,
    group_name VARCHAR(32) NOT NULL
        CHECK (group_name IN ('experimental', 'control')),
    note       TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 前测/后测成绩（同一学生每个阶段一条）
CREATE TABLE IF NOT EXISTS assessment_scores (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    phase      VARCHAR(8) NOT NULL CHECK (phase IN ('pre', 'post')),
    score      REAL NOT NULL,
    max_score  REAL NOT NULL DEFAULT 100,
    details    JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, phase)
);

-- NASA-TLX 认知负荷（6 个维度 0-100，weighted 为加权总分）
CREATE TABLE IF NOT EXISTS nasa_tlx (
    user_id     BIGINT PRIMARY KEY,
    mental      REAL,
    physical    REAL,
    temporal    REAL,
    performance REAL,
    effort      REAL,
    frustration REAL,
    weighted    REAL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assessment_phase ON assessment_scores(phase);
