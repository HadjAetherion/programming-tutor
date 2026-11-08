package repository

import (
	"context"

	"programming-tutor/backend/internal/model"
)

// LLMStatRepository llm_call_log 聚合查询（仪表盘用）。
type LLMStatRepository struct {
	db DBTX
}

func NewLLMStatRepository(db DBTX) *LLMStatRepository {
	return &LLMStatRepository{db: db}
}

// AggregateByUserID 按角色×模型层聚合当前用户的调用记录（延迟/Token/成本）。
func (r *LLMStatRepository) AggregateByUserID(
	ctx context.Context,
	userID int64,
) ([]model.LLMStat, error) {
	rows, err := r.db.Query(
		ctx,
		`
		SELECT agent_role, model_tier,
		       COUNT(*) AS calls,
		       COALESCE(AVG(latency_ms), 0)                 AS avg_latency_ms,
		       COALESCE(AVG(prompt_tokens), 0)              AS avg_prompt_tokens,
		       COALESCE(AVG(completion_tokens), 0)          AS avg_completion_tokens,
		       COALESCE(SUM(cost_yuan), 0)                  AS total_cost_yuan
		FROM llm_call_log
		WHERE user_id = $1
		GROUP BY agent_role, model_tier
		ORDER BY agent_role, model_tier
		`,
		userID,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []model.LLMStat
	for rows.Next() {
		var s model.LLMStat
		if err := rows.Scan(
			&s.AgentRole,
			&s.ModelTier,
			&s.Calls,
			&s.AvgLatencyMs,
			&s.AvgPromptTokens,
			&s.AvgCompletionTokens,
			&s.TotalCostYuan,
		); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, rows.Err()
}
