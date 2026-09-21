from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func

from app.core.database import Base


class DocVersion(Base):
    """文档版本历史表"""
    __tablename__ = "doc_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("document.id"), nullable=False, index=True, comment="所属文档")
    version = Column(Integer, nullable=False, comment="版本号")
    content = Column(Text, comment="该版本的完整内容")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
