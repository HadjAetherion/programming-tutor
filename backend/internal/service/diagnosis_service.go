package service

import (
	"context"
	"encoding/json"

	"programming-tutor/backend/internal/diagnosis"
	"programming-tutor/backend/internal/model"
	"programming-tutor/backend/internal/repository"
)

type DiagnosisService struct {
	diagnosisRepo *repository.DiagnosisRepository
	client        *diagnosis.Client
}

func NewDiagnosisService(
	diagnosisRepo *repository.DiagnosisRepository,
	client *diagnosis.Client,
) *DiagnosisService {
	return &DiagnosisService{
		diagnosisRepo: diagnosisRepo,
		client:        client,
	}
}

// DiagnoseSubmission 对一次提交触发多智能体诊断辅导（诊断/反馈/审查/规划），
// 结果落库后返回。
func (s *DiagnosisService) DiagnoseSubmission(
	ctx context.Context,
	submission *model.Submission,
	problem *model.Problem,
) (*model.Diagnosis, error) {
	req := diagnosis.DiagnoseRequest{
		SubmissionID: submission.ID,
		UserID:       submission.UserID,
		ProblemID:    problem.ID,
		Code:         submission.Code,
		Language:     submission.Language,
		Problem: diagnosis.ProblemPayload{
			Title:             problem.Title,
			Description:       problem.Description,
			InputDescription:  problem.InputDescription,
			OutputDescription: problem.OutputDescription,
			Constraints:       problem.Constraints,
			SampleInput:       problem.SampleInput,
			SampleOutput:      problem.SampleOutput,
		},
	}

	passed := submissionPassedTests(submission)
	req.JudgeResult = diagnosis.JudgeResultPayload{
		Status:      submission.Status,
		Stdout:      submission.Stdout,
		Stderr:      submission.Stderr,
		ExitCode:    submission.ExitCode,
		PassedTests: passed.passed,
		TotalTests:  passed.total,
	}

	resp, err := s.client.Diagnose(ctx, req)
	if err != nil {
		return nil, err
	}

	concepts := mustJSON(resp.Diagnosis.Concepts, "[]")
	feedback := mustJSON(resp.Feedback, "{}")
	review := mustJSON(resp.Review, "{}")
	planning := mustJSON(resp.Plan, "{}")

	d := &model.Diagnosis{
		SubmissionID:     submission.ID,
		UserID:           submission.UserID,
		ErrorType:        resp.Diagnosis.ErrorType,
		RootCause:        resp.Diagnosis.RootCause,
		Concepts:         concepts,
		Explanation:      resp.Diagnosis.Explanation,
		Hint:             resp.Diagnosis.Hint,
		Feedback:         feedback,
		Review:           review,
		Planning:         planning,
		ModelName:        resp.Meta.Model,
		ModelTier:        resp.Meta.ModelTier,
		LatencyMs:        resp.Meta.LatencyMs,
		PromptTokens:     resp.Meta.PromptTokens,
		CompletionTokens: resp.Meta.CompletionTokens,
		CostYuan:         resp.Meta.CostYuan,
	}

	return s.diagnosisRepo.Create(ctx, d)
}

func (s *DiagnosisService) GetBySubmission(
	ctx context.Context,
	submissionID int64,
	userID int64,
) (*model.Diagnosis, error) {
	return s.diagnosisRepo.GetBySubmissionID(ctx, submissionID, userID)
}

// passedInfo 从提交记录提取用例通过数，供反馈 Agent 的干预策略使用。
type passedInfo struct {
	passed *int
	total  *int
}

func submissionPassedTests(s *model.Submission) passedInfo {
	if s.TotalTests > 0 {
		passed := s.PassedTests
		total := s.TotalTests
		return passedInfo{passed: &passed, total: &total}
	}
	return passedInfo{}
}

func mustJSON(v any, fallback string) json.RawMessage {
	b, err := json.Marshal(v)
	if err != nil {
		return json.RawMessage(fallback)
	}
	return b
}
