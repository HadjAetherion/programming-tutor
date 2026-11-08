package handler

import (
	"context"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"

	"programming-tutor/backend/internal/diagnosis"
	"programming-tutor/backend/internal/model"
	"programming-tutor/backend/internal/sandbox"
	"programming-tutor/backend/internal/service"
)

type SubmissionHandler struct {
	runner            *sandbox.Runner
	judgeService      *service.JudgeService
	submissionService *service.SubmissionService
	diagnosisClient   *diagnosis.Client
}

func NewSubmissionHandler(
	runner *sandbox.Runner,
	judgeService *service.JudgeService,
	submissionService *service.SubmissionService,
	diagnosisClient *diagnosis.Client,
) *SubmissionHandler {
	return &SubmissionHandler{
		runner:            runner,
		judgeService:      judgeService,
		submissionService: submissionService,
		diagnosisClient:   diagnosisClient,
	}
}

type RunCodeRequest struct {
	Code     string `json:"code" binding:"required"`
	Language string `json:"language" binding:"required"`
	Input    string `json:"input"`
}

type SubmitCodeRequest struct {
	ProblemID int64  `json:"problem_id" binding:"required"`
	Code      string `json:"code" binding:"required"`
	Language  string `json:"language" binding:"required"`
}

func (h *SubmissionHandler) RunCode(c *gin.Context) {
	var req RunCodeRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(
			http.StatusBadRequest,
			gin.H{
				"error": "invalid request",
			},
		)
		return
	}

	if _, err := sandbox.SpecFor(req.Language); err != nil {
		c.JSON(
			http.StatusBadRequest,
			gin.H{
				"error":               "unsupported language",
				"supported_languages": sandbox.SupportedLanguages(),
			},
		)
		return
	}

	// 保留原来的单次运行接口。
	// 这里需要 Compile + Run。
	workDir, compileResult, cleanup, err :=
		h.runner.Compile(
			c.Request.Context(),
			req.Code,
			req.Language,
		)

	if err != nil {
		c.JSON(
			http.StatusInternalServerError,
			gin.H{
				"error": "sandbox compilation failed",
			},
		)
		return
	}

	defer cleanup()

	if !compileResult.Success {
		c.JSON(
			http.StatusOK,
			gin.H{
				"status":    "COMPILE_ERROR",
				"stderr":    compileResult.Stderr,
				"exit_code": compileResult.ExitCode,
			},
		)
		return
	}

	result, err := h.runner.Run(
		c.Request.Context(),
		workDir,
		req.Input,
		req.Language,
	)

	if err != nil {
		c.JSON(
			http.StatusInternalServerError,
			gin.H{
				"error": "sandbox execution failed",
			},
		)
		return
	}

	c.JSON(http.StatusOK, result)
}

func (h *SubmissionHandler) SubmitCode(c *gin.Context) {
	var req SubmitCodeRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid request",
		})
		return
	}

	if _, err := sandbox.SpecFor(req.Language); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":               "unsupported language",
			"supported_languages": sandbox.SupportedLanguages(),
		})
		return
	}

	// 语言别名归一（c++/cpp、py/python 等），后续判题与落库统一用规范名。
	language := sandbox.Normalize(req.Language)

	userID, ok := getUserID(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "user not authenticated",
		})
		return
	}

	result, err := h.judgeService.Judge(
		c.Request.Context(),
		req.ProblemID,
		req.Code,
		language,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "judge failed",
		})
		return
	}

	submission := &model.Submission{
		UserID:          userID,
		ProblemID:       req.ProblemID,
		Language:        language,
		Code:            req.Code,
		Status:          result.Status,
		Stdout:          result.Stdout,
		Stderr:          result.Stderr,
		ExitCode:        result.ExitCode,
		ExecutionTimeMs: result.ExecutionTimeMs,
		PassedTests:     result.PassedTests,
		TotalTests:      result.TotalTests,
	}

	createdSubmission, err :=
		h.submissionService.Create(
			c.Request.Context(),
			submission,
		)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "save submission failed",
		})
		return
	}

	// 判题通过 → 通知 agent-service 强化该题概念的掌握度（学情闭环）。
	// fire-and-forget：失败只记日志，不阻塞提交响应。
	if result.Status == service.StatusAccepted {
		go func(uid, pid int64) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			if err := h.diagnosisClient.RecordMastery(ctx, uid, pid, language); err != nil {
				log.Printf("record mastery failed (user %d, problem %d): %v", uid, pid, err)
			}
		}(userID, req.ProblemID)
	}

	c.JSON(http.StatusOK, gin.H{
		"id":                createdSubmission.ID,
		"status":            result.Status,
		"passed_tests":      result.PassedTests,
		"total_tests":       result.TotalTests,
		"stdout":            result.Stdout,
		"stderr":            result.Stderr,
		"exit_code":         result.ExitCode,
		"execution_time_ms": result.ExecutionTimeMs,
	})
}

// 目前保留，后面提交记录会用到。
func getUserID(c *gin.Context) (int64, bool) {
	value, exists := c.Get("user_id")
	if !exists {
		return 0, false
	}

	switch v := value.(type) {
	case int64:
		return v, true

	case string:
		id, err := strconv.ParseInt(v, 10, 64)
		if err != nil {
			return 0, false
		}
		return id, true

	default:
		return 0, false
	}
}
func (h *SubmissionHandler) ListMySubmissions(c *gin.Context) {
	userID, ok := getUserID(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "user not authenticated",
		})
		return
	}

	submissions, err := h.submissionService.ListByUserID(
		c.Request.Context(),
		userID,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to get submissions",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"submissions": submissions,
	})
}
func (h *SubmissionHandler) GetSubmission(c *gin.Context) {
	userID, ok := getUserID(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "user not authenticated",
		})
		return
	}

	id, err := strconv.ParseInt(
		c.Param("id"),
		10,
		64,
	)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid submission id",
		})
		return
	}

	submission, err :=
		h.submissionService.GetByIDAndUserID(
			c.Request.Context(),
			id,
			userID,
		)

	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "submission not found",
		})
		return
	}

	c.JSON(http.StatusOK, submission)
}
