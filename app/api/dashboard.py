from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.models.message import Message
from app.models.feedback import Feedback
from app.models.document import Document
from app.models.knowledge_gap import KnowledgeGap

router = APIRouter(prefix="/api/dashboard", tags=["看板"])


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    from datetime import datetime, timezone
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_today = (
        db.query(Message)
        .filter(Message.role == "user", Message.created_at >= today_start)
        .count()
    )

    total_feedback = db.query(Feedback).count()
    positive = db.query(Feedback).filter(Feedback.useful == True).count()
    hit_rate = (positive / total_feedback) if total_feedback > 0 else 0.0

    top_questions = (
        db.query(Message.content, func.count(Message.id).label("cnt"))
        .filter(Message.role == "user")
        .group_by(Message.content)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )

    doc_count = db.query(Document).count()
    pending_gaps = db.query(KnowledgeGap).filter(KnowledgeGap.status == "pending").count()

    return {
        "total_today": total_today,
        "hit_rate": round(hit_rate, 2),
        "top_questions": [
            {"question": q, "count": c} for q, c in top_questions
        ],
        "doc_count": doc_count,
        "pending_gaps": pending_gaps,
    }
