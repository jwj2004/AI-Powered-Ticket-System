from sqlalchemy import Column, Integer, String, DateTime, func

from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True, index=True, comment="用户名")
    password_hash = Column(String(256), nullable=False, comment="bcrypt 加密的密码")
    role = Column(String(16), nullable=False, default="newbie", comment="角色：admin/ops/newbie")
    status = Column(String(16), nullable=False, default="active", comment="状态：pending/active/rejected")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
