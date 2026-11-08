package service

import (
	"context"

	"programming-tutor/backend/internal/model"
	"programming-tutor/backend/internal/repository"
)

type ProblemTestCaseService struct {
	repo *repository.ProblemTestCaseRepository
}

func NewProblemTestCaseService(
	repo *repository.ProblemTestCaseRepository,
) *ProblemTestCaseService {
	return &ProblemTestCaseService{
		repo: repo,
	}
}

func (s *ProblemTestCaseService) ListByProblemID(
	ctx context.Context,
	problemID int64,
) ([]*model.ProblemTestCase, error) {
	return s.repo.ListByProblemID(ctx, problemID)
}
