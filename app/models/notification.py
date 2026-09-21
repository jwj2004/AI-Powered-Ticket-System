from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, func

from app.core.database import Base


class Notification(Base):
    """通知表"""
    __tablename__ = "notification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="接收人")
    gap_id = Column(Integer, ForeignKey("knowledge_gap.id"), comment="关联的知识缺口")
    read = Column(Boolean, default=False, comment="是否已读")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
