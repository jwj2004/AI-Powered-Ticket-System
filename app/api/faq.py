from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.user import User
from app.models.faq import FAQ

router = APIRouter(prefix="/api/faq", tags=["新手指南"])


class FAQItem(BaseModel):
    id: int
    question: str
    answer: str


class FAQCreateRequest(BaseModel):
    question: str
    answer: str
    gap_id: Optional[int] = None


@router.get("", response_model=list[FAQItem])
def list_faq(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = db.query(FAQ).order_by(FAQ.created_at.desc()).all()
    return [
        FAQItem(id=f.id, question=f.question, answer=f.answer)
        for f in items
    ]


@router.post("")
def create_faq(
    req: FAQCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    faq = FAQ(question=req.question, answer=req.answer, gap_id=req.gap_id)
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return {"id": faq.id, "ok": True}
