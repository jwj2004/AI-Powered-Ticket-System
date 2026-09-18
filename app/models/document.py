from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func

from app.core.database import Base


class Document(Base):
    """文档表"""
    __tablename__ = "document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    space_id = Column(Integer, ForeignKey("doc_space.id"), nullable=False, index=True, comment="所属文档空间")
    title = Column(String(256), nullable=False, comment="文档标题")
    content = Column(Text, comment="文档纯文本内容")
    content_type = Column(String(16), nullable=False, default="md", comment="类型：pdf/md/docx/txt")
    version = Column(Integer, default=1, comment="当前版本号")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    owner_id = Column(Integer, ForeignKey("user.id"), comment="上传者")
    approved = Column(Boolean, default=False, comment="是否审批通过")
    view_count = Column(Integer, default=0, comment="访问次数")
