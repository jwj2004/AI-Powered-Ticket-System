from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func

from app.core.database import Base


class Message(Base):
    """消息表"""
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversation.id"), nullable=False, index=True, comment="所属会话")
    role = Column(String(16), nullable=False, comment="角色：user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    citations_json = Column(Text, comment="引用来源 JSON 数组")
    confidence = Column(String(16), default="low", comment="置信度：high/low")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
