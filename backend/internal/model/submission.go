package model

import "time"

type Submission struct {
	ID              int64     `json:"id"`
	UserID          int64     `json:"user_id"`
	ProblemID       int64     `json:"problem_id"`
	Language        string    `json:"language"`
	Code            string    `json:"code"`
	Status          string    `json:"status"`
	Stdout          string    `json:"stdout"`
	Stderr          string    `json:"stderr"`
	ExitCode        int       `json:"exit_code"`
	ExecutionTimeMs int64     `json:"execution_time_ms"`
	PassedTests     int       `json:"passed_tests"`
	TotalTests      int       `json:"total_tests"`
	CreatedAt       time.Time `json:"created_at"`
}

type SubmissionSummary struct {
	ID              int64     `json:"id"`
	ProblemID       int64     `json:"problem_id"`
	Language        string    `json:"language"`
	Status          string    `json:"status"`
	ExitCode        int       `json:"exit_code"`
	ExecutionTimeMs int64     `json:"execution_time_ms"`
	HasDiagnosis    bool      `json:"has_diagnosis"`
	CreatedAt       time.Time `json:"created_at"`
}
