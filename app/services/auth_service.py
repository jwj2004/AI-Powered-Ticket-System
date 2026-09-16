from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.core.logger import log
from app.models.user import User


def create_user(db: Session, username: str, password: str, role: str = "newbie") -> User:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError(f"用户名 {username} 已存在")

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log.info(f"创建用户: {username} (role={role})")
    return user


def authenticate(db: Session, username: str, password: str) -> dict:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("用户名或密码错误")

    token = create_access_token(user.id, user.username, user.role)
    log.info(f"用户登录: {username}")
    return {"token": token, "role": user.role, "username": user.username}
