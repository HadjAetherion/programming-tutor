package repository

import (
	"context"

	"programming-tutor/backend/internal/model"
)

type SubmissionRepository struct {
	db DBTX
}

func NewSubmissionRepository(db DBTX) *SubmissionRepository {
	return &SubmissionRepository{
		db: db,
	}
}

func (r *SubmissionRepository) Create(
	ctx context.Context,
	submission *model.Submission,
) (*model.Submission, error) {

	query := `
		INSERT INTO submissions (
			user_id,
			problem_id,
			language,
			code,
			status,
			stdout,
			stderr,
			exit_code,
			execution_time_ms,
			passed_tests,
			total_tests
		)
		VALUES (
			$1, $2, $3, $4, $5,
			$6, $7, $8, $9, $10, $11
		)
		RETURNING
			id,
			created_at
	`

	err := r.db.QueryRow(
		ctx,
		query,
		submission.UserID,
		submission.ProblemID,
		submission.Language,
		submission.Code,
		submission.Status,
		submission.Stdout,
		submission.Stderr,
		submission.ExitCode,
		submission.ExecutionTimeMs,
		submission.PassedTests,
		submission.TotalTests,
	).Scan(
		&submission.ID,
		&submission.CreatedAt,
	)

	if err != nil {
		return nil, err
	}

	return submission, nil
}

func (r *SubmissionRepository) ListByUserID(
	ctx context.Context,
	userID int64,
) ([]*model.SubmissionSummary, error) {

	rows, err := r.db.Query(
		ctx,
		`
		SELECT
			s.id,
			s.problem_id,
			s.language,
			s.status,
			s.exit_code,
			s.execution_time_ms,
			CASE WHEN d.id IS NULL THEN false ELSE true END,
			s.created_at
		FROM submissions s
		LEFT JOIN submission_diagnosis d
			ON d.submission_id = s.id
		WHERE s.user_id = $1
		ORDER BY s.id DESC
		`,
		userID,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var submissions []*model.SubmissionSummary

	for rows.Next() {
		var submission model.SubmissionSummary

		if err := rows.Scan(
			&submission.ID,
			&submission.ProblemID,
			&submission.Language,
			&submission.Status,
			&submission.ExitCode,
			&submission.ExecutionTimeMs,
			&submission.HasDiagnosis,
			&submission.CreatedAt,
		); err != nil {
			return nil, err
		}

		submissions = append(
			submissions,
			&submission,
		)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return submissions, nil
}

func (r *SubmissionRepository) GetByIDAndUserID(
	ctx context.Context,
	id int64,
	userID int64,
) (*model.Submission, error) {

	var submission model.Submission

	err := r.db.QueryRow(
		ctx,
		`
		SELECT
			id,
			user_id,
			problem_id,
			language,
			code,
			status,
			stdout,
			stderr,
			exit_code,
			execution_time_ms,
			passed_tests,
			total_tests,
			created_at
		FROM submissions
		WHERE id = $1
		  AND user_id = $2
		`,
		id,
		userID,
	).Scan(
		&submission.ID,
		&submission.UserID,
		&submission.ProblemID,
		&submission.Language,
		&submission.Code,
		&submission.Status,
		&submission.Stdout,
		&submission.Stderr,
		&submission.ExitCode,
		&submission.ExecutionTimeMs,
		&submission.PassedTests,
		&submission.TotalTests,
		&submission.CreatedAt,
	)

	if err != nil {
		return nil, err
	}

	return &submission, nil
}
