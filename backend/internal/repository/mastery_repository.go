package repository

import (
	"context"

	"programming-tutor/backend/internal/model"
)

// MasteryRepository 学生掌握度查询（数据由 agent-service 学情算法写入）。
type MasteryRepository struct {
	db DBTX
}

func NewMasteryRepository(db DBTX) *MasteryRepository {
	return &MasteryRepository{db: db}
}

// ListByUserID 返回学生全部知识点的掌握度，按语言分组、掌握度升序（最薄弱在前）。
// language 为空时返回全部语言。
func (r *MasteryRepository) ListByUserID(
	ctx context.Context,
	userID int64,
	language string,
) ([]model.StudentMastery, error) {
	query := `
		SELECT language, concept_name, mastery, attempts, weakness_count, updated_at
		FROM student_mastery
		WHERE user_id = $1
	`
	args := []any{userID}
	if language != "" {
		query += ` AND language = $2`
		args = append(args, language)
	}
	query += ` ORDER BY language ASC, mastery ASC, concept_name ASC`

	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []model.StudentMastery
	for rows.Next() {
		var m model.StudentMastery
		if err := rows.Scan(
			&m.Language,
			&m.ConceptName,
			&m.Mastery,
			&m.Attempts,
			&m.WeaknessCount,
			&m.UpdatedAt,
		); err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}
