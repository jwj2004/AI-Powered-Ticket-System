from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.services.auth_service import create_user

router = APIRouter(prefix="/api/users", tags=["用户管理"])


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "newbie"


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
