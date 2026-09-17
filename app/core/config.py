# 应用配置
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，从 .env 文件读取"""

    # 数据库
    database_url: str = "sqlite:///./db/zhida.db"

    # 向量检索
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    faiss_index_path: str = "./db/ticket_index.faiss"
    faiss_mapping_path: str = "./db/ticket_id_mapping.json"
    doc_faiss_index_path: str = "./db/doc_index.faiss"
    doc_faiss_mapping_path: str = "./db/doc_id_mapping.json"

    # 服务
    app_name: str = "知答 MVP - 数据检索服务"
    debug: bool = True

    # LLM 配置（B 调用，A 留空对齐结构）
    openai_api_key: str = ""
    openai_base_url: str = ""
    llm_model: str = "deepseek-chat"

    # JWT 认证
    jwt_secret: str = "zhida-jwt-shared-2026"
    jwt_expire_hours: int = 24
    jwt_algorithm: str = "HS256"

    # 文档上传临时目录
    upload_dir: str = "./data/uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
