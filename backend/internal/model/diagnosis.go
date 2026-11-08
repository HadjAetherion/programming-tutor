package model

import (
	"encoding/json"
	"time"
)

// Diagnosis 一次提交对应的多智能体诊断辅导结果。
type Diagnosis struct {
	ID               int64           `json:"id"`
	SubmissionID     int64           `json:"submission_id"`
	UserID           int64           `json:"user_id"`
	ErrorType        string          `json:"error_type"`
	RootCause        string          `json:"root_cause"`
	Concepts         json.RawMessage `json:"concepts"`
	Explanation      string          `json:"explanation"`
	Hint             string          `json:"hint"`
	Feedback         json.RawMessage `json:"feedback"`  // 反馈 Agent 产出
	Review           json.RawMessage `json:"review"`    // 审查 Agent 产出
	Planning         json.RawMessage `json:"planning"`  // 规划 Agent 产出
	ModelName        string          `json:"model_name"`
	ModelTier        string          `json:"model_tier"`
	LatencyMs        int64           `json:"latency_ms"`
	PromptTokens     int             `json:"prompt_tokens"`
	CompletionTokens int             `json:"completion_tokens"`
	CostYuan         float64         `json:"cost_yuan"`
	CreatedAt        time.Time       `json:"created_at"`
}
