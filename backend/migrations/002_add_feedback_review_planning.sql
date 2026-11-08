-- 阶段2：4 Agent 协同产出列（反馈/审查/规划）
-- 在同一数据库执行：psql -d programming_tutor -f 002_add_feedback_review_planning.sql

ALTER TABLE submission_diagnosis
    ADD COLUMN IF NOT EXISTS feedback JSONB NOT NULL DEFAULT '{}';

ALTER TABLE submission_diagnosis
    ADD COLUMN IF NOT EXISTS review JSONB NOT NULL DEFAULT '{}';

ALTER TABLE submission_diagnosis
    ADD COLUMN IF NOT EXISTS planning JSONB NOT NULL DEFAULT '{}';
