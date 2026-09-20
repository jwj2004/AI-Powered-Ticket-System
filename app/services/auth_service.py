from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.core.logger import log
from app.models.user import User


def create_user(db: Session, username: str, password: str, role: str = "newbie", status: str = "active") -> User:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError(f"用户名 {username} 已存在")

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        status=status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log.info(f"创建用户: {username} (role={role}, status={status})")
    return user


def register_user(db: Session, username: str, password: str, role: str = "newbie") -> User:
    if role not in ("admin", "ops", "newbie"):
        raise ValueError("role 必须是 admin/ops/newbie")
    return create_user(db, username, password, role, status="pending")


def authenticate(db: Session, username: str, password: str) -> dict:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("用户名或密码错误")

    if user.status == "pending":
        raise PermissionError("账号待审核，请等待管理员通过")
    if user.status == "rejected":
        raise PermissionError("账号已被拒绝")
    if user.status == "disabled":
        raise PermissionError("账号已被禁用")

    token = create_access_token(user.id, user.username, user.role)
    log.info(f"用户登录: {username}")
    return {"token": token, "role": user.role, "username": user.username}
