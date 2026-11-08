package handler

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"programming-tutor/backend/internal/service"
)

type ProblemHandler struct {
	problemService *service.ProblemService
}

func NewProblemHandler(
	problemService *service.ProblemService,
) *ProblemHandler {
	return &ProblemHandler{
		problemService: problemService,
	}
}

func (h *ProblemHandler) List(c *gin.Context) {
	problems, err := h.problemService.List(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to get problems",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"problems": problems,
	})
}

func (h *ProblemHandler) GetByID(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid problem id",
		})
		return
	}

	problem, err := h.problemService.GetByID(
		c.Request.Context(),
		id,
	)

	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "problem not found",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"problem": problem,
	})
}
