package repository

import (
	"context"

	//"github.com/jackc/pgx/v5"

	"programming-tutor/backend/internal/model"
)

type ProblemTestCaseRepository struct {
	db DBTX
}

func NewProblemTestCaseRepository(db DBTX) *ProblemTestCaseRepository {
	return &ProblemTestCaseRepository{
		db: db,
	}
}

func (r *ProblemTestCaseRepository) ListByProblemID(
	ctx context.Context,
	problemID int64,
) ([]*model.ProblemTestCase, error) {

	rows, err := r.db.Query(
		ctx,
		`
		SELECT
			id,
			problem_id,
			input,
			expected_output,
			is_sample,
			created_at
		FROM problem_test_cases
		WHERE problem_id = $1
		ORDER BY id
		`,
		problemID,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var testCases []*model.ProblemTestCase

	for rows.Next() {
		var tc model.ProblemTestCase

		if err := rows.Scan(
			&tc.ID,
			&tc.ProblemID,
			&tc.Input,
			&tc.ExpectedOutput,
			&tc.IsSample,
			&tc.CreatedAt,
		); err != nil {
			return nil, err
		}

		testCases = append(testCases, &tc)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return testCases, nil
}
