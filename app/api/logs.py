from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.models.operation_log import OperationLog

router = APIRouter(prefix="/api/logs", tags=["操作日志"])


@router.get("")
def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    q = db.query(OperationLog)
    if user_id:
        q = q.filter(OperationLog.user_id == user_id)
    if action:
        q = q.filter(OperationLog.action.contains(action))
    total = q.count()
    items = q.order_by(OperationLog.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "resource": log.resource,
                "detail": log.detail,
                "created_at": log.created_at.isoformat() if log.created_at else "",
            }
            for log in items
        ],
    }
