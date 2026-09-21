from sqlalchemy import Column, String, Text

from app.core.database import Base


class ErrorCode(Base):
    """错误码表"""
    __tablename__ = "error_code"

    code = Column(String(64), primary_key=True, index=True, comment="错误码")
    name = Column(String(128), nullable=False, comment="错误名称")
    meaning = Column(Text, comment="错误含义")
    trigger_condition = Column(Text, comment="触发条件")
    known_causes = Column(Text, comment="已知原因列表，分号分隔")
    solution = Column(Text, comment="解决方案（可直接当草稿）")
    related_versions = Column(String(256), comment="关联版本，分号分隔")
