package model

import "time"

type Problem struct {
	ID                int64     `json:"id"`
	Title             string    `json:"title"`
	Description       string    `json:"description"`
	Difficulty        string    `json:"difficulty"`
	InputDescription  string    `json:"input_description"`
	OutputDescription string    `json:"output_description"`
	Constraints       string    `json:"constraints"`
	SampleInput       string    `json:"sample_input"`
	SampleOutput      string    `json:"sample_output"`
	TimeLimitMs       int       `json:"time_limit_ms"`
	MemoryLimitMB     int       `json:"memory_limit_mb"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}
