# Programming Tutor Agent Service

多智能体协同诊断与自适应辅导服务（Python / FastAPI）。

## 当前进度（阶段1）

- 模型网关 `ModelGateway` + 云端客户端 `CloudLLMClient`（智谱 GLM-4，OpenAI 兼容接口）
- 诊断 Agent（`DiagnosisAgent`），输出结构化 JSON：错误类型 / 根因 / 命中概念 / 启发式讲解 / 下一步提示
- 编排器（阶段1仅诊断 Agent；阶段2扩展为 诊断∥审查→反馈→规划 的 asyncio 协同）
- 每次 LLM 调用写入 `llm_call_log`（agent / 模型规模 / token / 延迟 / 成本）——创新点③的数据源

> 阶段3：接入 Ollama 端侧小模型 + 路由决策器（`Router`）按任务类型/复杂度/预算选择端侧或云端。

## 运行

```bash
cd agent-service
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
pip install -r requirements.txt
copy .env.example .env          # 填入 ZHIPU_API_KEY 与数据库密码
uvicorn app.main:app --reload --port 8000
```

## 接口

- `GET /health` — 健康检查
- `POST /api/v1/diagnose` — 代码诊断

### `/diagnose` 示例

```json
{
  "submission_id": 12,
  "user_id": 3,
  "code": "package main\n...",
  "language": "go",
  "problem": {
    "title": "两数之和",
    "description": "...",
    "input_description": "...",
    "output_description": "...",
    "constraints": "",
    "sample_input": "1 2",
    "sample_output": "3"
  },
  "judge_result": {
    "status": "WRONG_ANSWER",
    "stdout": "4",
    "stderr": "",
    "exit_code": 0
  }
}
```

返回 `diagnosis` + `meta`（模型 / 延迟 / token / 成本）。
