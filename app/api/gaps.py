from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.user import User
from app.models.knowledge_gap import KnowledgeGap
from app.models.notification import Notification

router = APIRouter(prefix="/api/gaps", tags=["知识缺口"])


class GapItem(BaseModel):
    id: int
    question: str
    status: str
    answer: Optional[str] = None
    created_at: str


class GapListResponse(BaseModel):
    total: int
    items: list[GapItem]


class ResolveRequest(BaseModel):
    answer: str


@router.get("", response_model=GapListResponse)
def list_gaps(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    q = db.query(KnowledgeGap)
    if status:
        q = q.filter(KnowledgeGap.status == status)
    gaps = q.order_by(KnowledgeGap.created_at.desc()).all()
    return {
        "total": len(gaps),
        "items": [
            GapItem(
                id=g.id, question=g.question, status=g.status,
                answer=g.answer,
                created_at=g.created_at.isoformat() if g.created_at else "",
            )
            for g in gaps
        ],
    }


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
    return {"ok": True}
