# 面向在线编程学习的多智能体协同诊断与自适应辅导系统

> 本科毕业设计项目 · Go + Vue 3 + Python 多智能体服务 + 大/小模型协同推理

一个面向程序设计入门课程的在线编程学习平台：学生提交代码后，系统由 **4 个智能体协同**完成错误诊断、代码审查、自适应辅导与学习规划，并通过**轻量级路由决策器**在端侧小模型与云端大模型之间动态分配推理任务。

---

## 核心特性

### 1. 多智能体协同诊断

四个角色分工协作，中间结果通过共享上下文（`AgentContext`）传递：

```
                ┌──────────────┐      ┌──────────────┐
                │  诊断 Agent   │      │  审查 Agent   │   第一阶段（并行）
                │ 错误类型/根因  │      │ 代码质量评分   │
                └──────┬───────┘      └──────┬───────┘
                       │  diagnosis_result    │ review_result
                       └────────┬─────────────┘
                ┌──────────────┐      ┌──────────────┐
                │  反馈 Agent   │      │  规划 Agent   │   第二阶段（并行）
                │ 自适应干预策略  │      │ 基于学情规划   │
                └──────────────┘      └──────────────┘
```

- **自适应干预策略**（规则可解释）：编译错误 → 直接提示；运行时错误 → 苏格拉底式提问；答案错误且通过率 < 0.6 → 分步引导

### 2. 大小模型协同路由（创新点①②）

轻量级路由决策器按 **任务类型 × 上下文复杂度 × 成本预算** 选择推理层级：

| Agent | 路由规则 | 默认层级 |
|---|---|---|
| 诊断 | 编译错误且代码短 | 端侧 |
| 诊断 | 其余情况 | 云端 |
| 审查 | 代码 ≤ 2000 字符 | 端侧 |
| 反馈 | 直接提示策略 | 端侧 |
| 规划 | 涉及概念少且基础分高 | 端侧 |

- 端侧：本地 Ollama `qwen2.5:7b`（零 API 成本，不受限流）
- 云端：智谱 `glm-4.7-flash`
- 端侧失败自动回退云端，保证可用性
- `ROUTER_FORCE_TIER=cloud` 一键切换为「全云端」对照架构（实验分组用）

### 3. 知识图谱与学情模型

- 四种语言各自的知识概念图谱：Go 27 节点 / Python 23 / Java 19 / C++ 19，含前置依赖边
- 掌握度采用 **EMA 增量更新**：诊断失败衰减 `m' = m × 0.7`，判题通过增强 `m' = m + 0.4 × (1 − m)`
- 规划 Agent 读取薄弱知识点，实现「基于学情推荐」而非「凭空建议」

### 4. 多语言判题沙箱

| 语言 | 镜像 | 说明 |
|---|---|---|
| Go | `golang:1.22-alpine` | `go build` 后运行 |
| Python | `python:3.12-alpine` | `py_compile` 语法预检后运行 |
| Java | `eclipse-temurin:17-jdk-alpine` | `javac` + `java` |
| C++ | `gcc:12` | `g++ -O2 -std=c++17` |

### 5. 学习仪表盘（创新点③）

KPI 总览 + 知识点掌握度排名图 + **分角色端侧/云端延迟对比** + 调用明细表，数据源为 `llm_call_log`。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Monaco Editor + Pinia |
| 后端 | Go 1.26 + Gin + pgx + JWT（分层 handler → service → repository） |
| Agent 服务 | Python 3 + FastAPI + httpx + asyncpg |
| 存储 | PostgreSQL（知识图谱直接用表实现，未引入图数据库） |
| 模型 | 智谱 GLM（云）+ Ollama qwen2.5:7b（端） |
| 判题 | Docker 容器隔离沙箱 |

---

## 快速开始

### 环境要求
- Go 1.21+、Node.js 18+、Python 3.9+、PostgreSQL 14+、Docker
- （可选）Ollama，用于端侧小模型

### 1. 准备数据库

```bash
createdb programming_tutor
cd backend
for f in migrations/*.sql; do psql -d programming_tutor -f "$f"; done
```

> 迁移脚本按编号顺序执行：001–003 诊断与提交字段，004–008 知识图谱（含四语言分区），009 题库，010 实验数据表。

### 2. 配置环境变量

```bash
cp .env.example .env
cp agent-service/.env.example agent-service/.env
# 编辑两个 .env：填写数据库密码、JWT_SECRET、ZHIPU_API_KEY
```

### 3. 启动

```bash
# Windows 一键启动（后端 8080 / Agent 8000 / 前端 5173）
start.bat

# 或分别启动
cd backend && go run ./cmd/server
cd agent-service && .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

### 4.（可选）端侧模型

```bash
ollama pull qwen2.5:7b
ollama serve
```

未启动 Ollama 时，路由到端侧的任务会自动回退云端（日志可见 warning）。

---

## 目录结构

```
programming-tutor/
├── backend/                  Go 后端
│   ├── cmd/server/           入口与依赖装配
│   ├── internal/
│   │   ├── handler/          HTTP 处理器
│   │   ├── service/          业务逻辑（判题、诊断、学情）
│   │   ├── repository/       SQL 数据访问
│   │   ├── model/            数据模型
│   │   ├── sandbox/          多语言 Docker 判题沙箱（spec.go 语言规格表）
│   │   └── diagnosis/        调用 Python Agent 服务的 HTTP 客户端
│   └── migrations/           数据库迁移 001-010
├── agent-service/            Python 多智能体服务
│   └── app/
│       ├── agents/           诊断 / 反馈 / 审查 / 规划
│       ├── llm/              模型网关与云端/端侧客户端
│       ├── router.py         路由决策器
│       ├── knowledge.py      知识图谱与学情算法
│       └── orchestrator.py   多智能体编排
├── frontend/                 Vue 3 前端
│   └── src/views/            登录 / 注册 / 题库 / 做题 / 提交详情 / 仪表盘
├── scripts/
│   ├── analysis.py           实验数据统计分析（Mann-Whitney U / Cliff's δ）
│   └── experiment_admin.py   实验数据录入工具
├── docs/
│   ├── 任务清单.md
│   └── 实验/                 实验协议 / 前后测卷 / NASA-TLX / 分析报告
└── start.bat                 一键启动
```

---

## 实验评估

准实验设计，对照 `ROUTER_FORCE_TIER=cloud` 的「全云端」基线：

| 指标 | 测量方式 |
|---|---|
| 学习效果 | 前后测增益（平行卷 A/B） |
| 认知负荷 | NASA-TLX 加权总分 |
| 推理成本 | 每次诊断 Token 消耗 / API 计费 |
| 响应延迟 | `llm_call_log.latency_ms` 与全流程墙钟时间 |

```bash
cd agent-service
.venv/Scripts/python ../scripts/analysis.py --out ../docs/实验/analysis_report.md
```

详见 `docs/实验/实验协议.md`。

---

## 安全说明

- 所有密钥通过 `.env` 配置，**不纳入版本控制**（`.gitignore` 已排除）
- 沙箱通过 Docker 容器隔离执行用户代码
- 首次部署请自行生成 `JWT_SECRET`

## 许可证

本项目为本科毕业设计作品，仅供学习与学术交流使用。
