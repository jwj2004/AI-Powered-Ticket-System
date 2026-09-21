from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Text, func

from app.core.database import Base


class Feedback(Base):
    """赞/踩反馈表"""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("message.id"), nullable=False, index=True, comment="关联消息")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="反馈用户")
    useful = Column(Boolean, nullable=False, comment="是否有用：True=赞/False=踩")
    comment = Column(Text, comment="文字反馈（可选）")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
