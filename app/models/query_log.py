from sqlalchemy import Column, String, Integer, Boolean

from app.core.database import Base


class QueryLog(Base):
    """查询埋点表"""
    __tablename__ = "query_log"

    query_id = Column(String(64), primary_key=True, comment="查询唯一ID")
    timestamp = Column(String(32), nullable=False, index=True, comment="查询时间")
    raw_text = Column(String(1024), comment="用户输入的原始文本")
    customer_id = Column(String(32), index=True, comment="客户ID")
    error_code = Column(String(64), comment="命中的错误码")
    confidence = Column(String(16), comment="置信度：high / low")
    latency_ms = Column(Integer, comment="检索耗时（毫秒）")
    copied = Column(Integer, default=0, comment="是否被复制：0/1")
    thumbs_down = Column(Integer, default=0, comment="是否被踩：0/1")
