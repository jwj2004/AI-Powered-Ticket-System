from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.models.message import Message
from app.models.feedback import Feedback

router = APIRouter(prefix="/api/dashboard", tags=["看板"])


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    from datetime import datetime, timezone, timedelta
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    today_messages = (
        db.query(Message)
        .filter(Message.role == "user", Message.created_at >= today_start)
        .count()
    )

    total_feedback = db.query(Feedback).count()
    positive = db.query(Feedback).filter(Feedback.useful == True).count()
    hit_rate = (positive / total_feedback * 100) if total_feedback > 0 else 0

    top_questions = (
        db.query(Message.content, func.count(Message.id).label("cnt"))
        .filter(Message.role == "user")
        .group_by(Message.content)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )

    return {
        "today_question_count": today_messages,
        "hit_rate": round(hit_rate, 1),
        "total_feedback": total_feedback,
        "top_questions": [
            {"question": q, "count": c} for q, c in top_questions
        ],
    }
