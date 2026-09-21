from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func

from app.core.database import Base


class KnowledgeGap(Base):
    """知识缺口表"""
    __tablename__ = "knowledge_gap"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False, comment="未答上来的问题")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="提问人")
    username = Column(String(64), comment="提问人用户名（冗余，方便查询）")
    status = Column(String(16), default="pending", comment="状态：pending/resolved")
    answer = Column(Text, comment="管理员补的答案")
    resolved_by = Column(Integer, ForeignKey("user.id"), comment="补答案的管理员")
    resolved_at = Column(DateTime, comment="解决时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    question_count = Column(Integer, default=1, comment="相同问题出现次数")
    document_id = Column(Integer, ForeignKey("document.id"), nullable=True, index=True, comment="关联文档ID")
    source_message_id = Column(Integer, ForeignKey("message.id"), nullable=True, index=True, comment="来源消息ID")
