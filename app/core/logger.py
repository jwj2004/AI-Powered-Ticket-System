# 日志配置
import sys
from loguru import logger

from app.core.config import settings


def setup_logger():
    """配置 loguru 日志"""
    # 移除默认 handler
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.debug else "INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        enqueue=True,
    )

    # 文件输出
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level="INFO",
        encoding="utf-8",
        enqueue=True,
    )

    return logger


# 全局 logger
log = setup_logger()
