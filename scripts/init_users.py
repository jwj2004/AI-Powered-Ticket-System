"""初始化用户表 + 默认文档空间"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, init_db
from app.core.logger import log
from app.models.user import User
from app.models.doc_space import DocSpace
from app.services.auth_service import create_user

DEFAULT_SPACES = [
    ("客服文档", "客服团队常见问题和操作指南"),
    ("运维文档", "运维团队系统配置和故障处理"),
    ("新手指南", "新人入职必读文档"),
]

DEFAULT_USERS = [
    ("admin", "admin123", "admin"),
    ("ops01", "ops123", "ops"),
    ("newbie01", "newbie123", "newbie"),
]


def init_users_and_spaces():
    db = SessionLocal()
    try:
        for name, desc in DEFAULT_SPACES:
            exists = db.query(DocSpace).filter(DocSpace.name == name).first()
            if not exists:
                db.add(DocSpace(name=name, description=desc))
                log.info(f"创建文档空间: {name}")
        db.commit()

        for username, password, role in DEFAULT_USERS:
            exists = db.query(User).filter(User.username == username).first()
            if not exists:
                create_user(db, username, password, role)

        log.success("用户和文档空间初始化完成")
        log.info("默认账号:")
        for u, p, r in DEFAULT_USERS:
            log.info(f"  {u} / {p} ({r})")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    init_users_and_spaces()
