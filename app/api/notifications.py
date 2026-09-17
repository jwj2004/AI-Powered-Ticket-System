from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.models.knowledge_gap import KnowledgeGap

router = APIRouter(prefix="/api/notifications", tags=["通知"])


@router.get("")
def list_notifications(
    unread_only: bool = Query(False, description="只返回未读"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = (
        db.query(Notification, KnowledgeGap, User)
        .join(KnowledgeGap, Notification.gap_id == KnowledgeGap.id, isouter=True)
        .join(User, KnowledgeGap.resolved_by == User.id, isouter=True)
    )

    # admin 能看全部，其他角色只看自己的
    if user.role != "admin":
        q = q.filter(Notification.user_id == user.id)

    if unread_only:
        q = q.filter(Notification.read == False)

    total = q.count()
    rows = q.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "notification_id": n.id,
                "gap_id": g.id if g else None,
                "question": g.question if g else "",
                "answer": g.answer if g else "",
                "status": g.status if g else "",
                "resolved_by": u.username if u else "",
                "read": n.read,
                "created_at": n.created_at.isoformat() if n.created_at else "",
            }
            for n, g, u in rows
        ],
    }


@router.post("/{notif_id}/read")
def mark_read(
    notif_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="通知不存在")
    notif.read = True
    db.commit()
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.read == False,
    ).update({"read": True})
    db.commit()
    return {"ok": True}
