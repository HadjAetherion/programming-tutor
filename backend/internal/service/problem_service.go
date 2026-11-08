package service

import (
	"context"

	"programming-tutor/backend/internal/model"
	"programming-tutor/backend/internal/repository"
)

type ProblemService struct {
	problemRepo *repository.ProblemRepository
}

func NewProblemService(
	problemRepo *repository.ProblemRepository,
) *ProblemService {
	return &ProblemService{
		problemRepo: problemRepo,
	}
}

func (s *ProblemService) List(
	ctx context.Context,
) ([]model.Problem, error) {
	return s.problemRepo.List(ctx)
}

func (s *ProblemService) GetByID(
	ctx context.Context,
	id int64,
) (*model.Problem, error) {
	return s.problemRepo.FindByID(ctx, id)
}
