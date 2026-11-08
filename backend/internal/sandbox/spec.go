package sandbox

import "fmt"

// Spec 一种受支持语言的沙箱执行规格（镜像 + 源码文件名 + 编译/运行命令 + 输出清洗）。
type Spec struct {
	Language     string   // 规范化语言标识：go / python / java / cpp
	Image        string   // Docker 镜像
	SourceFile   string   // 写入沙箱的源码文件名
	CompileArgs  []string // 编译命令参数；为空表示不需要编译
	CompileOut   string   // 编译产物路径（为空时 Run 直接用解释器运行源码）
	RunArgs      []string // 运行命令参数（解释型语言用）
	CleanOutput  func(string) string
}

// specs 语言 → 执行规格。新增语言只需在此登记 + 有对应镜像。
var specs = map[string]Spec{
	"go": {
		Language:    "go",
		Image:       "golang:1.22-alpine",
		SourceFile:  "main.go",
		CompileArgs: []string{"go", "build", "-o", "program", "main.go"},
		CompileOut:  "program",
	},
	"python": {
		Language:   "python",
		Image:      "python:3.12-alpine",
		SourceFile: "main.py",
		RunArgs:    []string{"python", "main.py"},
	},
	"java": {
		Language:    "java",
		Image:       "eclipse-temurin:17-jdk-alpine",
		SourceFile:  "Main.java",
		CompileArgs: []string{"javac", "Main.java"},
		// 不生成 jar，直接让 JVM 解释 class 文件
		RunArgs: []string{"java", "Main"},
	},
	"cpp": {
		Language:    "cpp",
		Image:       "gcc:12",
		SourceFile:  "main.cpp",
		CompileArgs: []string{"g++", "-O2", "-std=c++17", "-o", "program", "main.cpp"},
		CompileOut:  "program",
	},
}

// SpecFor 返回语言的执行规格。
func SpecFor(language string) (Spec, error) {
	spec, ok := specs[normalizeLanguage(language)]
	if !ok {
		return Spec{}, fmt.Errorf("unsupported language: %s", language)
	}
	return spec, nil
}

// SupportedLanguages 受支持的语言列表。
func SupportedLanguages() []string {
	out := make([]string, 0, len(specs))
	for name := range specs {
		out = append(out, name)
	}
	return out
}

// normalizeLanguage 语言别名归一（兼容 c++/cpp、py/python 等前端常见写法）。
func normalizeLanguage(language string) string {
	switch language {
	case "c++", "cpp", "cxx":
		return "cpp"
	case "py", "python3":
		return "python"
	case "golang":
		return "go"
	case "java":
		return "java"
	default:
		return language
	}
}

// Normalize 供外部包使用的语言归一化。
func Normalize(language string) string {
	return normalizeLanguage(language)
}
