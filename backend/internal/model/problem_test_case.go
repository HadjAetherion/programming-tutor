package model

import "time"

type ProblemTestCase struct {
	ID             int64     `json:"id"`
	ProblemID      int64     `json:"problem_id"`
	Input          string    `json:"input"`
	ExpectedOutput string    `json:"expected_output"`
	IsSample       bool      `json:"is_sample"`
	CreatedAt      time.Time `json:"created_at"`
}
