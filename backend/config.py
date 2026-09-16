"""LLM、JWT、检索客户端等运行时配置。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM（OpenAI 兼容接口）
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    llm_timeout_seconds: float = 10.0

    # A 的检索 / 错误码直查；USE_MOCK_RETRIEVE=true 时不真正发 HTTP
    retrieve_base_url: str = "http://127.0.0.1:8000"
    retrieve_timeout_seconds: float = 10.0
    use_mock_retrieve: bool = True

    # 文档块相似度阈值：低于此值视为证据不足
    high_score_threshold: float = 0.75

    # B 自己的会话 / 缺口 / 通知库（不碰 A 的 SQLite）
    database_path: str = "./backend/data/zhida_b.db"

    # JWT：与 A 约定同一密钥后可互认 token
    jwt_secret: str = "zhida-dev-jwt-secret-please-change"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    # CORS（C 的 Vue 开发地址）
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
