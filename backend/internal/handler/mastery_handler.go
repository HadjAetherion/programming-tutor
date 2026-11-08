package handler

import (
	"net/http"

	"programming-tutor/backend/internal/repository"
	"programming-tutor/backend/internal/sandbox"

	"github.com/gin-gonic/gin"
)

// MasteryHandler 学情接口（阶段4）：供前端学习仪表盘绘制掌握度雷达图等。
type MasteryHandler struct {
	repo *repository.MasteryRepository
}

func NewMasteryHandler(repo *repository.MasteryRepository) *MasteryHandler {
	return &MasteryHandler{repo: repo}
}

// GetMyMastery GET /api/v1/me/mastery?language=go —— 当前学生的知识点掌握度列表。
// language 缺省返回全部语言。
func (h *MasteryHandler) GetMyMastery(c *gin.Context) {
	userID, ok := getUserID(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "user not authenticated",
		})
		return
	}

	language := sandbox.Normalize(c.Query("language"))
	if c.Query("language") == "" {
		language = ""
	}

	rows, err := h.repo.ListByUserID(c.Request.Context(), userID, language)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to get mastery",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"mastery": rows,
	})
}
