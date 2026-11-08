-- 007：知识图谱改复合主键（多语言支持的核心修正）
-- 必须在校验语言列的 006 之后、种子 008 之前执行。
-- psql -d programming_tutor -f 007_knowledge_composite_pk.sql

-- ===== knowledge_nodes：name 单列主键 -> (language, name) =====
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'knowledge_nodes_pkey'
          AND conrelid = 'knowledge_nodes'::regclass
    ) THEN
        ALTER TABLE knowledge_nodes DROP CONSTRAINT knowledge_nodes_pkey;
    END IF;
END $$;

ALTER TABLE knowledge_nodes
    ADD PRIMARY KEY (language, name);

-- ===== knowledge_edges：(from,to) -> (language,from,to)，外键改复合 =====
ALTER TABLE knowledge_edges DROP CONSTRAINT IF EXISTS knowledge_edges_pkey;
ALTER TABLE knowledge_edges DROP CONSTRAINT IF EXISTS knowledge_edges_from_node_fkey;
ALTER TABLE knowledge_edges DROP CONSTRAINT IF EXISTS knowledge_edges_to_node_fkey;

ALTER TABLE knowledge_edges
    ADD PRIMARY KEY (language, from_node, to_node);

ALTER TABLE knowledge_edges
    ADD CONSTRAINT knowledge_edges_from_fkey
    FOREIGN KEY (language, from_node)
    REFERENCES knowledge_nodes(language, name) ON DELETE CASCADE;

ALTER TABLE knowledge_edges
    ADD CONSTRAINT knowledge_edges_to_fkey
    FOREIGN KEY (language, to_node)
    REFERENCES knowledge_nodes(language, name) ON DELETE CASCADE;

-- ===== problem_concepts：(problem,concept) -> (problem,language,concept) =====
ALTER TABLE problem_concepts DROP CONSTRAINT IF EXISTS problem_concepts_pkey;
ALTER TABLE problem_concepts DROP CONSTRAINT IF EXISTS problem_concepts_concept_name_fkey;

ALTER TABLE problem_concepts
    ADD PRIMARY KEY (problem_id, language, concept_name);

ALTER TABLE problem_concepts
    ADD CONSTRAINT problem_concepts_concept_fkey
    FOREIGN KEY (language, concept_name)
    REFERENCES knowledge_nodes(language, name) ON DELETE CASCADE;

-- ===== student_mastery：外键改复合（主键已在 006 改为 user+language+concept）=====
ALTER TABLE student_mastery DROP CONSTRAINT IF EXISTS student_mastery_concept_name_fkey;

ALTER TABLE student_mastery
    ADD CONSTRAINT student_mastery_concept_fkey
    FOREIGN KEY (language, concept_name)
    REFERENCES knowledge_nodes(language, name) ON DELETE CASCADE;
