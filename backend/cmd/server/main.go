package main

import (
	"github.com/gin-contrib/cors"
	"log"
	"net/http"
	"os"
	"programming-tutor/backend/internal/diagnosis"
	"programming-tutor/backend/internal/sandbox"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"programming-tutor/backend/internal/handler"
	"programming-tutor/backend/internal/middleware"
	"programming-tutor/backend/internal/repository"
	"programming-tutor/backend/internal/service"
)

func main() {
	if err := godotenv.Load(); err != nil {
		log.Println("warning: .env file not found")
	}

	db, err := repository.NewDBPool()
	if err != nil {
		log.Fatalf("failed to connect database: %v", err)
	}
	defer db.Close()

	// Repository
	userRepo := repository.NewUserRepository(db)

	// Service
	authService := service.NewAuthService(userRepo)

	// Handler
	authHandler := handler.NewAuthHandler(authService)
	userHandler := handler.NewUserHandler(userRepo)

	problemRepo := repository.NewProblemRepository(db)

	problemService := service.NewProblemService(problemRepo)

	problemHandler := handler.NewProblemHandler(problemService)

	//sandbox
	testCaseRepo :=
		repository.NewProblemTestCaseRepository(db)

	testCaseService :=
		service.NewProblemTestCaseService(testCaseRepo)

	runner :=
		sandbox.NewRunner()

	judgeService :=
		service.NewJudgeService(
			testCaseService,
			runner,
		)

	// ===== 诊断（多智能体 Python 服务）客户端 =====
	// 提交判题通过后也用它向 agent-service 上报学情（掌握度强化）。
	diagnosisClient := diagnosis.NewClient(os.Getenv("AGENT_SERVICE_URL"))

	submissionRepo := repository.NewSubmissionRepository(db)

	submissionService := service.NewSubmissionService(
		submissionRepo,
	)

	submissionHandler := handler.NewSubmissionHandler(
		runner,
		judgeService,
		submissionService,
		diagnosisClient,
	)

	// ===== 诊断（多智能体 Python 服务） =====
	diagnosisRepo := repository.NewDiagnosisRepository(db)
	diagnosisService := service.NewDiagnosisService(diagnosisRepo, diagnosisClient)
	diagnosisHandler := handler.NewDiagnosisHandler(
		submissionService,
		problemService,
		diagnosisService,
	)

	// ===== 学情（阶段4：知识图谱 + 掌握度） =====
	masteryRepo := repository.NewMasteryRepository(db)
	masteryHandler := handler.NewMasteryHandler(masteryRepo)

	// ===== 推理成本/延迟统计（阶段5：创新点③数据面） =====
	llmStatRepo := repository.NewLLMStatRepository(db)
	llmStatHandler := handler.NewLLMStatHandler(llmStatRepo)

	router := gin.Default()
	router.Use(cors.New(cors.Config{
		AllowOrigins: []string{
			"http://localhost:5173",
			"http://localhost:5174",
		},
		AllowMethods: []string{
			"GET",
			"POST",
			"PUT",
			"PATCH",
			"DELETE",
			"OPTIONS",
		},
		AllowHeaders: []string{
			"Origin",
			"Content-Type",
			"Accept",
			"Authorization",
		},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "ok",
		})
	})

	router.GET("/health/db", func(c *gin.Context) {
		if err := db.Ping(c.Request.Context()); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"status": "error",
			})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"status":   "ok",
			"database": "connected",
		})
	})

	api := router.Group("/api/v1")
	{
		api.POST("/auth/register", authHandler.Register)
		api.POST("/auth/login", authHandler.Login)
	}

	authRequired := api.Group("")
	authRequired.Use(middleware.AuthMiddleware(authService))
	{
		//authRequired.GET("/me", userHandler.Me)

		authRequired.GET("/problems", problemHandler.List)
		authRequired.GET("/problems/:id", problemHandler.GetByID)
	}
	authRequired.POST(
		"/submissions/run",
		submissionHandler.RunCode,
	)
	authRequired.POST(
		"/submissions/submit",
		submissionHandler.SubmitCode,
	)
	authRequired.GET(
		"/submissions",
		submissionHandler.ListMySubmissions,
	)
	authRequired.GET(
		"/submissions/:id",
		submissionHandler.GetSubmission,
	)
	authRequired.POST(
		"/submissions/:id/diagnose",
		diagnosisHandler.Diagnose,
	)
	authRequired.GET(
		"/submissions/:id/diagnosis",
		diagnosisHandler.Get,
	)
	authRequired.GET(
		"/me/mastery",
		masteryHandler.GetMyMastery,
	)
	authRequired.GET(
		"/me/llm-stats",
		llmStatHandler.GetMyLLMStats,
	)
	// Public routes
	//auth := api.Group("/auth")
	//{
	//	auth.POST("/register", authHandler.Register)
	//	auth.POST("/login", authHandler.Login)
	//}

	// Protected routes
	protected := api.Group("")
	protected.Use(middleware.AuthMiddleware(authService))
	{
		protected.GET("/me", userHandler.Me)
	}

	port := os.Getenv("APP_PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("server starting on :%s", port)

	if err := router.Run(":" + port); err != nil {
		log.Fatal(err)
	}
}
