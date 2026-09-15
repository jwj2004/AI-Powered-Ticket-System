from sqlalchemy import Column, String, Text

from app.core.database import Base


class CustomerAsset(Base):
    """客户资产表"""
    __tablename__ = "customer_asset"

    customer_id = Column(String(32), primary_key=True, index=True, comment="客户ID")
    shop_name = Column(String(128), nullable=False, comment="店铺名称")
    plan = Column(String(32), comment="套餐版本（基础版/专业版/企业版）")
    version = Column(String(32), comment="当前系统版本号")
    enabled_modules = Column(String(512), comment="已开通模块，逗号分隔")
    key_configs = Column(Text, comment="关键配置，分号分隔")
    recent_changes = Column(String(512), comment="最近变更")
