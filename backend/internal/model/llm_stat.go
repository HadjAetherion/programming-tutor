package model

// LLMStat 按 Agent 角色 × 模型层聚合的调用统计（创新点③的数据面）。
type LLMStat struct {
	AgentRole           string  `json:"agent_role"`
	ModelTier           string  `json:"model_tier"`
	Calls               int64   `json:"calls"`
	AvgLatencyMs        float64 `json:"avg_latency_ms"`
	AvgPromptTokens     float64 `json:"avg_prompt_tokens"`
	AvgCompletionTokens float64 `json:"avg_completion_tokens"`
	TotalCostYuan       float64 `json:"total_cost_yuan"`
}
