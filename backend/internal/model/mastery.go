package model

import "time"

// StudentMastery 学生对某语言某知识点的掌握度（阶段4 学情模型，EMA 更新）。
type StudentMastery struct {
	Language      string    `json:"language"`
	ConceptName   string    `json:"concept_name"`
	Mastery       float64   `json:"mastery"`
	Attempts      int       `json:"attempts"`
	WeaknessCount int       `json:"weakness_count"`
	UpdatedAt     time.Time `json:"updated_at"`
}
