from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.models.knowledge_gap import KnowledgeGap
from app.models.notification import Notification

router = APIRouter(prefix="/api/gaps", tags=["知识缺口"])


class ResolveRequest(BaseModel):
    answer: str
    document_id: Optional[int] = None


@router.get("")
def list_gaps(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    q = db.query(KnowledgeGap, User).join(User, KnowledgeGap.user_id == User.id)
    if status:
        q = q.filter(KnowledgeGap.status == status)
    rows = q.order_by(KnowledgeGap.created_at.desc()).all()
    return [
        {
            "gap_id": g.id,
            "question": g.question,
            "user_id": g.user_id,
            "username": u.username,
            "status": g.status,
            "created_at": g.created_at.isoformat() if g.created_at else "",
        }
        for g, u in rows
    ]


@router.post("/{gap_id}/resolve")
def resolve_gap(
    gap_id: int,
    req: ResolveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    from datetime import datetime, timezone
    gap = db.query(KnowledgeGap).filter(KnowledgeGap.id == gap_id).first()
    if not gap:
        raise HTTPException(status_code=404, detail="缺口不存在")

    gap.status = "resolved"
    gap.answer = req.answer
    gap.resolved_by = user.id
    gap.resolved_at = datetime.now(timezone.utc)

    notification = Notification(
        user_id=gap.user_id,
        gap_id=gap.id,
        read=False,
    )
    db.add(notification)
    db.commit()
    return {"ok": True, "notified_user_id": gap.user_id}


class MergeRequest(BaseModel):
    target_gap_id: int


@router.post("/{gap_id}/merge")
def merge_gaps(
    gap_id: int,
    req: MergeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    source = db.query(KnowledgeGap).filter(KnowledgeGap.id == gap_id).first()
    target = db.query(KnowledgeGap).filter(KnowledgeGap.id == req.target_gap_id).first()
    if not source or not target:
        raise HTTPException(status_code=404, detail="缺口不存在")
    if source.id == target.id:
        raise HTTPException(status_code=400, detail="不能合并到自己")
    target.question_count = (target.question_count or 1) + (source.question_count or 1)
    if source.answer and not target.answer:
        target.answer = source.answer
        target.status = "resolved"
    db.delete(source)
    db.commit()
    return {"ok": True, "merged_into": target.id}
