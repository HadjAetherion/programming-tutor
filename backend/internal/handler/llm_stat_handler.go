package handler

import (
	"net/http"

	"programming-tutor/backend/internal/repository"

	"github.com/gin-gonic/gin"
)

// LLMStatHandler 推理成本/延迟统计接口（创新点③：成本-质量联合评估的数据面）。
type LLMStatHandler struct {
	repo *repository.LLMStatRepository
}

func NewLLMStatHandler(repo *repository.LLMStatRepository) *LLMStatHandler {
	return &LLMStatHandler{repo: repo}
}

// GetMyLLMStats GET /api/v1/me/llm-stats —— 当前学生按角色×模型层的调用聚合。
func (h *LLMStatHandler) GetMyLLMStats(c *gin.Context) {
	userID, ok := getUserID(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "user not authenticated",
		})
		return
	}

	stats, err := h.repo.AggregateByUserID(c.Request.Context(), userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to get llm stats",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"stats": stats,
	})
}
