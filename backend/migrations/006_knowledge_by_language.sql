-- 006：知识图谱按语言分区（多语言支持）
-- psql -d programming_tutor -f 006_knowledge_by_language.sql

-- 1) 节点/边/题目标注加 language 列（默认 go，兼容阶段4 已有数据）
ALTER TABLE knowledge_nodes
    ADD COLUMN IF NOT EXISTS language VARCHAR(16) NOT NULL DEFAULT 'go';

ALTER TABLE knowledge_edges
    ADD COLUMN IF NOT EXISTS language VARCHAR(16) NOT NULL DEFAULT 'go';

ALTER TABLE problem_concepts
    ADD COLUMN IF NOT EXISTS language VARCHAR(16) NOT NULL DEFAULT 'go';

-- 2) 学生掌握度按 (用户, 语言, 概念) 唯一 —— 主键重建
ALTER TABLE student_mastery
    ADD COLUMN IF NOT EXISTS language VARCHAR(16) NOT NULL DEFAULT 'go';

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'student_mastery_pkey'
          AND conrelid = 'student_mastery'::regclass
    ) THEN
        ALTER TABLE student_mastery DROP CONSTRAINT student_mastery_pkey;
    END IF;
END $$;

ALTER TABLE student_mastery
    ADD PRIMARY KEY (user_id, language, concept_name);

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_language
    ON knowledge_nodes(language, category, name);

CREATE INDEX IF NOT EXISTS idx_student_mastery_user_lang
    ON student_mastery(user_id, language, mastery ASC);
