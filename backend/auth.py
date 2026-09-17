"""JWT 校验。登录由 A 负责；B 独立联调时用种子账号签发 token。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Header, HTTPException
from pydantic import BaseModel

from backend.config import get_settings

# B 独立运行时的种子用户（密码仅用于本模块 /api/auth/login）
SEED_USERS: list[dict] = [
    {"id": 1, "username": "admin", "password": "admin123", "role": "admin"},
    {"id": 2, "username": "ops", "password": "ops123", "role": "ops"},
    {"id": 3, "username": "newbie", "password": "newbie123", "role": "newbie"},
]


class CurrentUser(BaseModel):
    id: int
    username: str
    role: str


def find_seed_user(username: str, password: str) -> Optional[dict]:
    for row in SEED_USERS:
        if row["username"] == username and row["password"] == password:
            return row
    return None


def create_access_token(*, user_id: int, username: str, role: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    # 字段与 A 的 create_access_token 对齐：sub / username / role
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> CurrentUser:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="未登录或 token 无效") from exc

    user_id = payload.get("user_id") or payload.get("sub")
    username = payload.get("username") or ""
    role = payload.get("role") or ""
    try:
        uid = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="未登录或 token 无效") from exc
    if not username or role not in {"admin", "ops", "newbie"}:
        raise HTTPException(status_code=401, detail="未登录或 token 无效")
    return CurrentUser(id=uid, username=username, role=role)


def get_current_user(authorization: Optional[str] = Header(default=None)) -> CurrentUser:
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录或 token 无效")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="未登录或 token 无效")
    return decode_access_token(token.strip())


def require_admin(user: CurrentUser) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    return user
