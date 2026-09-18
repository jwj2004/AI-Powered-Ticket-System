# 应用配置
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，从 .env 文件读取"""

    # 数据库
    database_url: str = "sqlite:///./db/zhida.db"

    # 向量检索
    embedding_model: str = "shibing624/text2vec-base-chinese"
    faiss_index_path: str = "./db/ticket_index.faiss"
    faiss_mapping_path: str = "./db/ticket_id_mapping.json"

    # 服务
    app_name: str = "知答 MVP - 数据检索服务"
    debug: bool = True

    # LLM 配置（A 不需要直接调，留空占位，对齐团队结构）
    openai_api_key: str = ""
    openai_base_url: str = ""
    llm_model: str = "deepseek-chat"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
