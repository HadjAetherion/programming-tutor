package repository

import (
	"context"

	"programming-tutor/backend/internal/model"
)

type DiagnosisRepository struct {
	db DBTX
}

func NewDiagnosisRepository(db DBTX) *DiagnosisRepository {
	return &DiagnosisRepository{db: db}
}

func (r *DiagnosisRepository) Create(
	ctx context.Context,
	d *model.Diagnosis,
) (*model.Diagnosis, error) {
	query := `
		INSERT INTO submission_diagnosis (
			submission_id, user_id, error_type, root_cause, concepts,
			explanation, hint, feedback, review, planning,
			model_name, model_tier, latency_ms,
			prompt_tokens, completion_tokens, cost_yuan
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
		RETURNING id, created_at
	`
	// jsonb 列统一传 string：pgx 会把 []byte 当 bytea 导致类型不匹配。
	err := r.db.QueryRow(
		ctx,
		query,
		d.SubmissionID,
		d.UserID,
		d.ErrorType,
		d.RootCause,
		string(d.Concepts),
		d.Explanation,
		d.Hint,
		string(d.Feedback),
		string(d.Review),
		string(d.Planning),
		d.ModelName,
		d.ModelTier,
		d.LatencyMs,
		d.PromptTokens,
		d.CompletionTokens,
		d.CostYuan,
	).Scan(&d.ID, &d.CreatedAt)
	if err != nil {
		return nil, err
	}
	return d, nil
}

func (r *DiagnosisRepository) GetBySubmissionID(
	ctx context.Context,
	submissionID int64,
	userID int64,
) (*model.Diagnosis, error) {
	var d model.Diagnosis

	err := r.db.QueryRow(
		ctx,
		`
		SELECT id, submission_id, user_id, error_type, root_cause, concepts,
		       explanation, hint, feedback, review, planning,
		       model_name, model_tier, latency_ms,
		       prompt_tokens, completion_tokens, cost_yuan, created_at
		FROM submission_diagnosis
		WHERE submission_id = $1 AND user_id = $2
		ORDER BY id DESC
		LIMIT 1
		`,
		submissionID,
		userID,
	).Scan(
		&d.ID,
		&d.SubmissionID,
		&d.UserID,
		&d.ErrorType,
		&d.RootCause,
		&d.Concepts,
		&d.Explanation,
		&d.Hint,
		&d.Feedback,
		&d.Review,
		&d.Planning,
		&d.ModelName,
		&d.ModelTier,
		&d.LatencyMs,
		&d.PromptTokens,
		&d.CompletionTokens,
		&d.CostYuan,
		&d.CreatedAt,
	)
	if err != nil {
		return nil, err
	}
	return &d, nil
}
