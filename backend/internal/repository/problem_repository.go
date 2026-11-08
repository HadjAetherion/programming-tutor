package repository

import (
	"context"

	"programming-tutor/backend/internal/model"
)

type ProblemRepository struct {
	db DBTX
}

func NewProblemRepository(db DBTX) *ProblemRepository {
	return &ProblemRepository{
		db: db,
	}
}

func (r *ProblemRepository) List(ctx context.Context) ([]model.Problem, error) {
	rows, err := r.db.Query(ctx, `
		SELECT
			id,
			title,
			description,
			difficulty,
			input_description,
			output_description,
			constraints,
			sample_input,
			sample_output,
			time_limit_ms,
			memory_limit_mb,
			created_at,
			updated_at
		FROM problems
		ORDER BY id ASC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var problems []model.Problem

	for rows.Next() {
		var p model.Problem

		err := rows.Scan(
			&p.ID,
			&p.Title,
			&p.Description,
			&p.Difficulty,
			&p.InputDescription,
			&p.OutputDescription,
			&p.Constraints,
			&p.SampleInput,
			&p.SampleOutput,
			&p.TimeLimitMs,
			&p.MemoryLimitMB,
			&p.CreatedAt,
			&p.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}

		problems = append(problems, p)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return problems, nil
}

func (r *ProblemRepository) FindByID(
	ctx context.Context,
	id int64,
) (*model.Problem, error) {

	var p model.Problem

	err := r.db.QueryRow(ctx, `
		SELECT
			id,
			title,
			description,
			difficulty,
			input_description,
			output_description,
			constraints,
			sample_input,
			sample_output,
			time_limit_ms,
			memory_limit_mb,
			created_at,
			updated_at
		FROM problems
		WHERE id = $1
	`, id).Scan(
		&p.ID,
		&p.Title,
		&p.Description,
		&p.Difficulty,
		&p.InputDescription,
		&p.OutputDescription,
		&p.Constraints,
		&p.SampleInput,
		&p.SampleOutput,
		&p.TimeLimitMs,
		&p.MemoryLimitMB,
		&p.CreatedAt,
		&p.UpdatedAt,
	)

	if err != nil {
		return nil, err
	}

	return &p, nil
}
