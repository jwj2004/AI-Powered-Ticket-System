# 数据库连接
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings
from app.core.logger import log

# SQLite 需要加 check_same_thread=False
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,  # debug 模式打印 SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依赖注入用：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库：建表（D1 MVP 用，正式环境走 alembic）"""
    # 先导入所有 model，确保 Base 知道它们
    from app.models import error_code, customer_asset, ticket, query_log, vector_index_meta  # noqa: F401
    log.info("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    log.success("数据库表创建完成")
