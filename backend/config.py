"""LLM、JWT、检索客户端等运行时配置。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# 与 A 统一的 JWT 密钥，B 内所有签发/校验都必须用这一串
SHARED_JWT_SECRET = "zhida-jwt-shared-2026"


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
    retrieve_timeout_seconds: float = 30.0
    use_mock_retrieve: bool = False

    # 文档块相似度阈值：低于 medium 视为证据不足
    high_score_threshold: float = 0.55
    medium_score_threshold: float = 0.35

    # 检索增强：候选池 → BM25+向量融合 → cross-encoder 重排
    retrieve_candidate_k: int = 10
    retrieve_top_k: int = 3
    enable_query_rewrite: bool = True
    enable_hybrid_retrieve: bool = True
    enable_cross_encoder: bool = False
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # 热门问题缓存：命中次数达到阈值后直接返回缓存答案
    hot_cache_min_hits: int = 3

    # 与 A 共用同一份 SQLite。不要再用 zhida_b.db，否则会话列表和问答会错位
    database_url: str = "sqlite:///./db/zhida.db"
    database_path: str = ""

    # JWT：必须与 A 的 jwt_secret 一致，否则 A 签发的 token 会被 B 判无效
    jwt_secret: str = SHARED_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # CORS（C 的 Vue 开发地址）
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def sqlite_path() -> str:
    """解析出 SQLite 文件路径。测试里 DATABASE_PATH 优先；联调走 A 的 zhida.db。"""
    settings = get_settings()
    if (settings.database_path or "").strip():
        return settings.database_path.strip()
    url = (settings.database_url or "").strip()
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///") :]
    return "./db/zhida.db"
