from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ===== 智谱 GLM 云端大模型 =====
    zhipu_api_key: str = ""
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    # glm-4.7-flash 为智谱免费模型；如接口报模型不存在，改为 glm-4-flash / glm-4.5-flash
    zhipu_model: str = "glm-4.7-flash"

    # ===== Ollama 端侧小模型 =====
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen2.5:7b"

    # ===== 数据库（与 Go 后端共用同一个 PostgreSQL） =====
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "programming_tutor"
    db_sslmode: str = "disable"

    # ===== 并发控制 =====
    # 云端免费模型并发配额低，默认串行（同一时刻 1 个在途 LLM 请求）
    llm_max_concurrency: int = 1

    # ===== 路由决策器（阶段3） =====
    # 空 = 自动按任务类型/复杂度路由；"cloud" = 全部走云端（对照组实验）；
    # "edge" = 全部走端侧
    router_force_tier: str = ""
    # 累计成本阈值（元），超过后强制端侧；0 = 不启用（云端配置了单价才有意义）
    router_budget_yuan: float = 0.0

    # ===== 成本单价（元 / 1K tokens） =====
    # 请按智谱官方当前定价填写；为 0 时 cost_yuan 记 0，但 token 与延迟照常记录。
    zhipu_input_price_per_1k: float = 0.0
    zhipu_output_price_per_1k: float = 0.0
    ollama_price_per_1k: float = 0.0  # 本地推理，成本记 0

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?sslmode={self.db_sslmode}"
        )


settings = Settings()
