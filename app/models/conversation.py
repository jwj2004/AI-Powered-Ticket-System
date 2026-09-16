from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

from app.core.database import Base


class Conversation(Base):
    """会话表"""
    __tablename__ = "conversation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="所属用户")
    title = Column(String(256), comment="会话标题")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
