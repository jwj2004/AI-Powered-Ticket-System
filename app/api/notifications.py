from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.models.knowledge_gap import KnowledgeGap

router = APIRouter(prefix="/api/notifications", tags=["通知"])


@router.get("")
def list_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    notifs = (
        db.query(Notification, KnowledgeGap)
        .join(KnowledgeGap, Notification.gap_id == KnowledgeGap.id)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return {
        "total": len(notifs),
        "unread": sum(1 for n, _ in notifs if not n.read),
        "items": [
            {
                "id": n.id,
                "gap_id": g.id,
                "question": g.question,
                "answer": g.answer,
                "read": n.read,
                "created_at": n.created_at.isoformat() if n.created_at else "",
            }
            for n, g in notifs
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
