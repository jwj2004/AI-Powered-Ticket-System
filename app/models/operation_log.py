from sqlalchemy import Column, Integer, String, DateTime, Text, func

from app.core.database import Base


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, comment="操作人ID")
    username = Column(String(64), comment="操作人用户名")
    action = Column(String(128), nullable=False, comment="操作类型")
    resource = Column(String(256), comment="操作对象")
    detail = Column(Text, comment="详情")
    created_at = Column(DateTime, server_default=func.now(), comment="操作时间")
