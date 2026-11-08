package handler

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"programming-tutor/backend/internal/service"
)

type DiagnosisHandler struct {
	submissionService *service.SubmissionService
	problemService    *service.ProblemService
	diagnosisService  *service.DiagnosisService
}

func NewDiagnosisHandler(
	submissionService *service.SubmissionService,
	problemService *service.ProblemService,
	diagnosisService *service.DiagnosisService,
) *DiagnosisHandler {
	return &DiagnosisHandler{
		submissionService: submissionService,
		problemService:    problemService,
		diagnosisService:  diagnosisService,
	}
}

// Diagnose 对某次提交触发多智能体诊断辅导（LLM 调用，耗时 1-3 分钟）。
// POST /api/v1/submissions/:id/diagnose
func (h *DiagnosisHandler) Diagnose(c *gin.Context) {
	userID, ok := getUserID(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "user not authenticated",
		})
		return
	}

	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid submission id",
		})
		return
	}

	submission, err := h.submissionService.GetByIDAndUserID(
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

	problem, err := h.problemService.GetByID(
		c.Request.Context(),
		submission.ProblemID,
	)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "problem not found",
		})
		return
	}

	d, err := h.diagnosisService.DiagnoseSubmission(
		c.Request.Context(),
		submission,
		problem,
	)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{
			"error":  "diagnosis failed",
			"detail": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"diagnosis": d,
	})
}

// Get 获取某次提交已保存的诊断结果（不触发 LLM 调用）。
// GET /api/v1/submissions/:id/diagnosis
func (h *DiagnosisHandler) Get(c *gin.Context) {
	userID, ok := getUserID(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "user not authenticated",
		})
		return
	}

	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid submission id",
		})
		return
	}

	d, err := h.diagnosisService.GetBySubmission(
		c.Request.Context(),
		id,
		userID,
	)
	if err != nil {
		// 没有诊断记录时返回 null，前端按无诊断处理
		c.JSON(http.StatusOK, gin.H{
			"diagnosis": nil,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"diagnosis": d,
	})
}
