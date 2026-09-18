from sqlalchemy import Column, String, Text, Integer

from app.core.database import Base


class Ticket(Base):
    """历史工单表"""
    __tablename__ = "ticket"

    ticket_id = Column(String(32), primary_key=True, index=True, comment="工单ID")
    customer_id = Column(String(32), index=True, comment="客户ID")
    created_at = Column(String(32), comment="创建时间（ISO字符串）")
    error_code = Column(String(64), index=True, comment="关联错误码，为空表示未分类")
    raw_text = Column(Text, comment="客户原话/原始问题")
    solution_text = Column(Text, comment="解决文案")
    status = Column(String(16), comment="工单状态")
    handle_minutes = Column(Integer, comment="处理时长（分钟）")
