package service

import (
	"context"
	"programming-tutor/backend/internal/sandbox"
	"strings"
)

const (
	StatusAccepted     = "ACCEPTED"
	StatusWrongAnswer  = "WRONG_ANSWER"
	StatusCompileError = "COMPILE_ERROR"
	StatusRuntimeError = "RUNTIME_ERROR"
	StatusTimeLimit    = "TIME_LIMIT"
)

type JudgeService struct {
	testCaseService *ProblemTestCaseService
	runner          *sandbox.Runner
}

func NewJudgeService(
	testCaseService *ProblemTestCaseService,
	runner *sandbox.Runner,
) *JudgeService {
	return &JudgeService{
		testCaseService: testCaseService,
		runner:          runner,
	}
}

type JudgeResult struct {
	Status          string `json:"status"`
	PassedTests     int    `json:"passed_tests"`
	TotalTests      int    `json:"total_tests"`
	Stdout          string `json:"stdout"`
	Stderr          string `json:"stderr"`
	ExitCode        int    `json:"exit_code"`
	ExecutionTimeMs int64  `json:"execution_time_ms"`
}

func (s *JudgeService) Judge(
	ctx context.Context,
	problemID int64,
	code string,
	language string,
) (*JudgeResult, error) {

	testCases, err := s.testCaseService.ListByProblemID(
		ctx,
		problemID,
	)
	if err != nil {
		return nil, err
	}

	result := &JudgeResult{
		Status:     StatusAccepted,
		TotalTests: len(testCases),
	}

	// ===== 先编译 =====

	workDir, compileResult, cleanup, err :=
		s.runner.Compile(
			ctx,
			code,
			language,
		)

	if err != nil {
		return nil, err
	}

	defer cleanup()

	if !compileResult.Success {

		result.Status = StatusCompileError
		result.Stderr = compileResult.Stderr
		result.ExitCode = compileResult.ExitCode

		return result, nil
	}

	// ===== 开始测试 =====

	for _, testCase := range testCases {

		runResult, err := s.runner.Run(
			ctx,
			workDir,
			testCase.Input,
			language,
		)
		if err != nil {
			return nil, err
		}

		result.ExecutionTimeMs +=
			runResult.ExecutionTimeMs

		result.Stdout = runResult.Stdout
		result.Stderr = runResult.Stderr
		result.ExitCode = runResult.ExitCode

		switch runResult.Status {

		case "TIME_LIMIT":
			result.Status = StatusTimeLimit
			return result, nil

		case "RUNTIME_ERROR":
			result.Status = StatusRuntimeError
			return result, nil
		}

		actual := normalizeOutput(
			runResult.Stdout,
		)

		expected := normalizeOutput(
			testCase.ExpectedOutput,
		)

		if actual != expected {

			result.Status =
				StatusWrongAnswer

			return result, nil
		}

		result.PassedTests++
	}

	return result, nil
}
func normalizeOutput(output string) string {
	return strings.TrimSpace(output)
}

// 防止 model 包未来扩展时这里没有被使用的问题。
