package sandbox

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

type CompileResult struct {
	Success  bool   `json:"success"`
	Stderr   string `json:"stderr"`
	ExitCode int    `json:"exit_code"`
}

type Result struct {
	Status          string `json:"status"`
	Stdout          string `json:"stdout"`
	Stderr          string `json:"stderr"`
	ExitCode        int    `json:"exit_code"`
	ExecutionTimeMs int64  `json:"execution_time_ms"`
}

// Runner 按语言规格在 Docker 中编译/运行用户代码。
type Runner struct{}

func NewRunner() *Runner {
	return &Runner{}
}

// Compile 编译用户代码。
// 返回一个可执行文件所在的临时目录和编译结果。
func (r *Runner) Compile(
	ctx context.Context,
	code string,
	language string,
) (string, *CompileResult, func(), error) {

	spec, err := SpecFor(language)
	if err != nil {
		return "", nil, nil, err
	}

	workDir, err := os.MkdirTemp(
		"",
		"programming-tutor-sandbox-*",
	)
	if err != nil {
		return "", nil, nil, fmt.Errorf(
			"create temp directory: %w",
			err,
		)
	}

	cleanup := func() {
		_ = os.RemoveAll(workDir)
	}

	codePath := filepath.Join(workDir, spec.SourceFile)

	if err := os.WriteFile(
		codePath,
		[]byte(code),
		0600,
	); err != nil {
		cleanup()

		return "", nil, nil, fmt.Errorf(
			"write code: %w",
			err,
		)
	}

	compileCtx, cancel := context.WithTimeout(
		ctx,
		10*time.Second,
	)
	defer cancel()

	var args []string
	if len(spec.CompileArgs) > 0 {
		args = append(args, dockerArgs(workDir, spec.Image)...)
		args = append(args, spec.CompileArgs...)
	} else {
		// 解释型语言：编译阶段只做语法预检（python 的 py_compile）
		args = append(args, dockerArgs(workDir, spec.Image)...)
		args = append(args, pythonSyntaxCheck(spec)...)
	}

	cmd := exec.CommandContext(
		compileCtx,
		"docker",
		args...,
	)

	var stdout bytes.Buffer
	var stderr bytes.Buffer

	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err = cmd.Run()

	if compileCtx.Err() == context.DeadlineExceeded {
		cleanup()

		return "", &CompileResult{
			Success:  false,
			Stderr:   "compilation timeout",
			ExitCode: -1,
		}, func() {}, nil
	}

	if err != nil {
		exitCode := -1

		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		}

		cleanup()

		return "", &CompileResult{
			Success:  false,
			Stderr:   stderr.String(),
			ExitCode: exitCode,
		}, func() {}, nil
	}

	return workDir, &CompileResult{
		Success:  true,
		Stderr:   stderr.String(),
		ExitCode: 0,
	}, cleanup, nil
}

// Run 执行已经编译好的程序。
func (r *Runner) Run(
	ctx context.Context,
	workDir string,
	input string,
	language string,
) (*Result, error) {

	spec, err := SpecFor(language)
	if err != nil {
		return nil, err
	}

	inputPath := filepath.Join(workDir, "input.txt")

	if err := os.WriteFile(
		inputPath,
		[]byte(input),
		0600,
	); err != nil {
		return nil, fmt.Errorf(
			"write input: %w",
			err,
		)
	}

	runCtx, cancel := context.WithTimeout(
		ctx,
		5*time.Second,
	)
	defer cancel()

	var runCmd []string
	if len(spec.RunArgs) > 0 {
		runCmd = spec.RunArgs
	} else {
		runCmd = []string{"./" + spec.CompileOut}
	}
	args := append(dockerArgs(workDir, spec.Image), "sh", "-c", shellRun(runCmd))

	cmd := exec.CommandContext(
		runCtx,
		"docker",
		args...,
	)

	var stdout bytes.Buffer
	var stderr bytes.Buffer

	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	start := time.Now()

	err = cmd.Run()

	executionTime := time.Since(start).Milliseconds()

	if runCtx.Err() == context.DeadlineExceeded {
		return &Result{
			Status:          "TIME_LIMIT",
			Stdout:          stdout.String(),
			Stderr:          stderr.String(),
			ExitCode:        -1,
			ExecutionTimeMs: executionTime,
		}, nil
	}

	if err == nil {
		return &Result{
			Status:          "FINISHED",
			Stdout:          stdout.String(),
			Stderr:          stderr.String(),
			ExitCode:        0,
			ExecutionTimeMs: executionTime,
		}, nil
	}

	if exitErr, ok := err.(*exec.ExitError); ok {
		return &Result{
			Status:          "RUNTIME_ERROR",
			Stdout:          stdout.String(),
			Stderr:          stderr.String(),
			ExitCode:        exitErr.ExitCode(),
			ExecutionTimeMs: executionTime,
		}, nil
	}

	return nil, fmt.Errorf(
		"docker execution failed: %w",
		err,
	)
}

// dockerArgs 公共 docker run 参数（挂载工作区、设工作目录）。
func dockerArgs(workDir, image string) []string {
	return []string{
		"run",
		"--rm",
		"--mount",
		fmt.Sprintf("type=bind,source=%s,target=/workspace", filepath.Clean(workDir)),
		"--workdir",
		"/workspace",
		image,
	}
}

// pythonSyntaxCheck 解释型语言的"编译"阶段：语法预检，便于把语法错误归为编译错误。
func pythonSyntaxCheck(spec Spec) []string {
	return []string{"python", "-m", "py_compile", spec.SourceFile}
}

// shellRun 拼出带输入重定向的运行命令。
func shellRun(runCmd []string) string {
	cmd := ""
	for i, part := range runCmd {
		if i > 0 {
			cmd += " "
		}
		cmd += part
	}
	return cmd + " < input.txt"
}
