package service

import (
	"context"

	"programming-tutor/backend/internal/model"
	"programming-tutor/backend/internal/repository"
)

type SubmissionService struct {
	repo *repository.SubmissionRepository
}

func NewSubmissionService(
	repo *repository.SubmissionRepository,
) *SubmissionService {
	return &SubmissionService{
		repo: repo,
	}
}

func (s *SubmissionService) Create(
	ctx context.Context,
	submission *model.Submission,
) (*model.Submission, error) {
	return s.repo.Create(ctx, submission)
}
func (s *SubmissionService) ListByUserID(
	ctx context.Context,
	userID int64,
) ([]*model.SubmissionSummary, error) {
	return s.repo.ListByUserID(ctx, userID)
}
func (s *SubmissionService) GetByIDAndUserID(
	ctx context.Context,
	id int64,
	userID int64,
) (*model.Submission, error) {
	return s.repo.GetByIDAndUserID(
		ctx,
		id,
		userID,
	)
}
