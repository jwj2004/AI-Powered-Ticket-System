from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.core.database import Base


class DocSpace(Base):
    """文档空间（按部门隔离）"""
    __tablename__ = "doc_space"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True, comment="空间名称")
    description = Column(Text, comment="空间描述")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
