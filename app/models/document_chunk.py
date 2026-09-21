from sqlalchemy import Column, Integer, String, Text, ForeignKey, func, DateTime

from app.core.database import Base


class DocumentChunk(Base):
    """文档切块表"""
    __tablename__ = "document_chunk"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("document.id"), nullable=False, index=True, comment="所属文档")
    chunk_index = Column(Integer, nullable=False, comment="块序号")
    content = Column(Text, nullable=False, comment="块文本内容")
    chunk_type = Column(String(16), comment="切块类型：faq / normal")
    embedding_id = Column(String(128), comment="FAISS 中的向量 ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
