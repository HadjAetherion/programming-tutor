-- 阶段2补充：submissions 记录用例通过数（反馈 Agent 干预策略需要通过率）
-- psql -d programming_tutor -f 003_add_submission_test_counts.sql

ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS passed_tests INT NOT NULL DEFAULT 0;

ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS total_tests INT NOT NULL DEFAULT 0;
