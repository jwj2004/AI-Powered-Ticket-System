from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.services.auth_service import create_user
from app.services.log_service import log_action

router = APIRouter(prefix="/api/users", tags=["用户管理"])


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "newbie"


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    users = (
        db.query(User)
        .filter(User.status == "active")
        .order_by(User.created_at.desc())
        .all()
    )
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "status": u.status,
            "created_at": u.created_at.isoformat() if u.created_at else "",
        }
        for u in users
    ]


@router.post("")
def create_new_user(
    req: CreateUserRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if req.role not in ("admin", "ops", "newbie"):
        raise HTTPException(status_code=400, detail="role 必须是 admin/ops/newbie")
    try:
        new_user = create_user(db, req.username, req.password, req.role)
        return {"id": new_user.id, "ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pending")
def list_pending(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    pending_users = (
        db.query(User)
        .filter(User.status == "pending")
        .order_by(User.created_at.desc())
        .all()
    )
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "created_at": u.created_at.isoformat() if u.created_at else "",
        }
        for u in pending_users
    ]


@router.post("/{user_id}/approve")
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.status != "pending":
        raise HTTPException(status_code=400, detail=f"用户状态为 {target.status}，无法审核")
    target.status = "active"
    log_action(db, user.id, user.username, "approve_user", resource=f"user:{user_id}", detail=target.username)
    db.commit()
    return {"ok": True}


@router.post("/{user_id}/reject")
def reject_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.status != "pending":
        raise HTTPException(status_code=400, detail=f"用户状态为 {target.status}，无法拒绝")
    target.status = "rejected"
    log_action(db, user.id, user.username, "reject_user", resource=f"user:{user_id}", detail=target.username)
    db.commit()
    return {"ok": True}


@router.post("/{user_id}/make-admin")
def make_admin(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if user_id == user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    target.role = "admin"
    log_action(db, user.id, user.username, "make_admin", resource=f"user:{user_id}", detail=target.username)
    db.commit()
    return {"ok": True}


class UpdateRoleRequest(BaseModel):
    role: str


@router.patch("/{user_id}")
def update_user_role(
    user_id: int,
    req: UpdateRoleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if req.role not in ("admin", "ops", "newbie"):
        raise HTTPException(status_code=400, detail="role 必须是 admin/ops/newbie")
    if user_id == user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    old_role = target.role
    target.role = req.role
    log_action(db, user.id, user.username, "update_role", resource=f"user:{user_id}", detail=f"{target.username}: {old_role} -> {req.role}")
    db.commit()
    return {"ok": True}


@router.post("/{user_id}/disable")
def disable_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if user_id == user.id:
        raise HTTPException(status_code=400, detail="不能禁用自己")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.status == "rejected":
        raise HTTPException(status_code=400, detail="用户已被禁用")
    target.status = "rejected"
    log_action(db, user.id, user.username, "disable_user", resource=f"user:{user_id}", detail=target.username)
    db.commit()
    return {"ok": True}
