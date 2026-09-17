from sqlalchemy import Column, Integer, String, DateTime, func

from app.core.database import Base


class VectorIndexMeta(Base):
    """向量索引元数据表"""
    __tablename__ = "vector_index_meta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    index_name = Column(String(64), nullable=False, comment="索引名称")
    model_name = Column(String(128), comment="使用的向量模型")
    vector_dim = Column(Integer, comment="向量维度")
    ticket_count = Column(Integer, comment="索引的工单数量")
    built_at = Column(String(32), comment="构建时间")
