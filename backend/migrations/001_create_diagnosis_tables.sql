-- 阶段1新增表：诊断结果 + LLM 调用成本日志
-- 在 Go 后端使用的 PostgreSQL 中执行：psql -d <db_name> -f 001_create_diagnosis_tables.sql

-- 诊断结果表：每次诊断与一次提交绑定
CREATE TABLE IF NOT EXISTS submission_diagnosis (
    id                 BIGSERIAL PRIMARY KEY,
    submission_id      BIGINT      NOT NULL,
    user_id            BIGINT      NOT NULL,
    error_type         VARCHAR(64) NOT NULL DEFAULT '',
    root_cause         TEXT        NOT NULL DEFAULT '',
    concepts           JSONB       NOT NULL DEFAULT '[]',   -- 命中的知识点数组
    explanation        TEXT        NOT NULL DEFAULT '',
    hint               TEXT        NOT NULL DEFAULT '',
    model_name         VARCHAR(64) NOT NULL DEFAULT '',
    model_tier         VARCHAR(16) NOT NULL DEFAULT '',     -- cloud / edge
    latency_ms         BIGINT      NOT NULL DEFAULT 0,
    prompt_tokens      INT         NOT NULL DEFAULT 0,
    completion_tokens  INT         NOT NULL DEFAULT 0,
    cost_yuan          DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_submission_diagnosis_submission
    ON submission_diagnosis(submission_id);

-- LLM 调用日志表：每次调用一行，供成本-质量联合评估（创新点③）
CREATE TABLE IF NOT EXISTS llm_call_log (
    id                 BIGSERIAL PRIMARY KEY,
    agent_role         VARCHAR(32) NOT NULL,                -- diagnosis/feedback/review/planning
    model_tier         VARCHAR(16) NOT NULL,                -- cloud / edge
    model_name         VARCHAR(64) NOT NULL,
    prompt_tokens      INT         NOT NULL DEFAULT 0,
    completion_tokens  INT         NOT NULL DEFAULT 0,
    latency_ms         BIGINT      NOT NULL DEFAULT 0,
    cost_yuan          DOUBLE PRECISION NOT NULL DEFAULT 0,
    user_id            BIGINT,
    submission_id      BIGINT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_llm_call_log_submission
    ON llm_call_log(submission_id);
CREATE INDEX IF NOT EXISTS idx_llm_call_log_user
    ON llm_call_log(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_call_log_created
    ON llm_call_log(created_at);
