// Package diagnosis 提供与 Python 多智能体服务的 HTTP 通信。
package diagnosis

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// Client 调用 Python agent-service 的 HTTP 客户端。
type Client struct {
	baseURL string
	http    *http.Client
}

func NewClient(baseURL string) *Client {
	if baseURL == "" {
		baseURL = "http://localhost:8000"
	}
	return &Client{
		baseURL: baseURL,
		http:    &http.Client{Timeout: 300 * time.Second},
	}
}

type ProblemPayload struct {
	Title             string `json:"title"`
	Description       string `json:"description"`
	InputDescription  string `json:"input_description"`
	OutputDescription string `json:"output_description"`
	Constraints       string `json:"constraints"`
	SampleInput       string `json:"sample_input"`
	SampleOutput      string `json:"sample_output"`
}

type JudgeResultPayload struct {
	Status      string `json:"status"`
	Stdout      string `json:"stdout"`
	Stderr      string `json:"stderr"`
	ExitCode    int    `json:"exit_code"`
	PassedTests *int   `json:"passed_tests,omitempty"`
	TotalTests  *int   `json:"total_tests,omitempty"`
}

type DiagnoseRequest struct {
	SubmissionID int64              `json:"submission_id,omitempty"`
	UserID       int64              `json:"user_id,omitempty"`
	ProblemID    int64              `json:"problem_id,omitempty"`
	Code         string             `json:"code"`
	Language     string             `json:"language"`
	Problem      ProblemPayload     `json:"problem"`
	JudgeResult  JudgeResultPayload `json:"judge_result"`
}

type DiagnosisPayload struct {
	ErrorType   string   `json:"error_type"`
	RootCause   string   `json:"root_cause"`
	Concepts    []string `json:"concepts"`
	Explanation string   `json:"explanation"`
	Hint        string   `json:"hint"`
}

type FeedbackPayload struct {
	TutoringStyle    string   `json:"tutoring_style"`
	Content          string   `json:"content"`
	GuidingQuestions []string `json:"guiding_questions"`
	CodeExample      string   `json:"code_example"`
}

type ReviewIssuePayload struct {
	Severity   string `json:"severity"`
	Category   string `json:"category"`
	Message    string `json:"message"`
	Suggestion string `json:"suggestion"`
}

type ReviewPayload struct {
	OverallScore int                  `json:"overall_score"`
	Strengths    []string             `json:"strengths"`
	Issues       []ReviewIssuePayload `json:"issues"`
	Summary      string               `json:"summary"`
}

type PlanStepPayload struct {
	Action string `json:"action"`
	Detail string `json:"detail"`
}

type PlanPayload struct {
	Summary          string            `json:"summary"`
	Steps            []PlanStepPayload `json:"steps"`
	NextProblemHint  string            `json:"next_problem_hint"`
}

type DiagnoseMeta struct {
	Model            string  `json:"model"`
	ModelTier        string  `json:"model_tier"`
	LatencyMs        int64   `json:"latency_ms"`
	PromptTokens     int     `json:"prompt_tokens"`
	CompletionTokens int     `json:"completion_tokens"`
	CostYuan         float64 `json:"cost_yuan"`
}

type DiagnoseResponse struct {
	Diagnosis DiagnosisPayload `json:"diagnosis"`
	Feedback  FeedbackPayload  `json:"feedback"`
	Review    ReviewPayload    `json:"review"`
	Plan      PlanPayload      `json:"planning"`
	Meta      DiagnoseMeta     `json:"meta"`
}

func (c *Client) Diagnose(
	ctx context.Context,
	req DiagnoseRequest,
) (*DiagnoseResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		c.baseURL+"/api/v1/diagnose",
		bytes.NewReader(body),
	)
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.http.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("call agent service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("agent service returned status %d", resp.StatusCode)
	}

	var out DiagnoseResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("decode agent response: %w", err)
	}
	return &out, nil
}

// MasteryRecordRequest 判题通过后上报学情的载荷。
type MasteryRecordRequest struct {
	UserID    int64  `json:"user_id"`
	ProblemID int64  `json:"problem_id"`
	Language  string `json:"language"`
	Passed    bool   `json:"passed"`
}

// RecordMastery 通知 agent-service 强化该题标注概念的掌握度（EMA 增强）。
// 调用方应以 fire-and-forget 方式（goroutine + 短超时）使用，不阻塞判题主流程。
func (c *Client) RecordMastery(
	ctx context.Context,
	userID, problemID int64,
	language string,
) error {
	body, err := json.Marshal(
		MasteryRecordRequest{
			UserID:    userID,
			ProblemID: problemID,
			Language:  language,
			Passed:    true,
		},
	)
	if err != nil {
		return fmt.Errorf("marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		c.baseURL+"/api/v1/mastery/record",
		bytes.NewReader(body),
	)
	if err != nil {
		return err
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.http.Do(httpReq)
	if err != nil {
		return fmt.Errorf("call agent service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("agent service returned status %d", resp.StatusCode)
	}
	return nil
}
