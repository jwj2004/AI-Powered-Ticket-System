from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.feedback import Feedback
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.faq import FAQ
from app.models.knowledge_gap import KnowledgeGap
from app.models.doc_space import DocSpace

router = APIRouter(prefix="/api/dashboard", tags=["看板"])


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # 1. 今日问答量
    total_today = (
        db.query(Message)
        .filter(Message.role == "user", Message.created_at >= today_start)
        .count()
    )

    # 2. 命中率 = confidence high 的消息 / assistant 消息总数
    total_assistant = db.query(Message).filter(Message.role == "assistant").count()
    high_count = db.query(Message).filter(
        Message.role == "assistant", Message.confidence == "high"
    ).count()
    hit_rate = (high_count / total_assistant) if total_assistant > 0 else 0.0

    # 3. 置信度分布
    confidence_dist = (
        db.query(Message.confidence, func.count(Message.id).label("cnt"))
        .filter(Message.role == "assistant")
        .group_by(Message.confidence)
        .all()
    )
    confidence_distribution = {row[0] or "none": row[1] for row in confidence_dist}

    # 4. 热门问题 Top10（按会话分组，取会话标题）
    top_questions = (
        db.query(
            Conversation.id,
            Conversation.title,
            func.count(Message.id).label("msg_cnt"),
        )
        .join(Message, Message.conversation_id == Conversation.id)
        .filter(Message.role == "user")
        .group_by(Conversation.id, Conversation.title)
        .order_by(desc("msg_cnt"))
        .limit(10)
        .all()
    )

    # 5. 文档统计
    doc_count = db.query(Document).count()
    chunk_count = db.query(DocumentChunk).count()
    space_stats = (
        db.query(
            DocSpace.id,
            DocSpace.name,
            func.count(Document.id).label("doc_cnt"),
        )
        .join(Document, Document.space_id == DocSpace.id, isouter=True)
        .group_by(DocSpace.id, DocSpace.name)
        .all()
    )

    # 6. 知识缺口
    pending_gaps = db.query(KnowledgeGap).filter(KnowledgeGap.status == "pending").count()
    resolved_gaps = db.query(KnowledgeGap).filter(KnowledgeGap.status == "resolved").count()
    recent_gaps = (
        db.query(KnowledgeGap)
        .filter(KnowledgeGap.status == "pending")
        .order_by(KnowledgeGap.created_at.desc())
        .limit(5)
        .all()
    )

    # 7. 会话统计
    total_conversations = db.query(Conversation).count()
    today_conversations = (
        db.query(Conversation)
        .filter(Conversation.created_at >= today_start)
        .count()
    )
    week_conversations = (
        db.query(Conversation)
        .filter(Conversation.created_at >= week_ago)
        .count()
    )

    # 8. 反馈统计
    total_feedback = db.query(Feedback).count()
    positive = db.query(Feedback).filter(Feedback.useful == True).count()
    negative = db.query(Feedback).filter(Feedback.useful == False).count()
    satisfaction_rate = (positive / total_feedback) if total_feedback > 0 else 0.0

    return {
        "questions": {
            "total_today": total_today,
            "hit_rate": round(hit_rate, 4),
            "confidence_distribution": confidence_distribution,
            "satisfaction_rate": round(satisfaction_rate, 4),
            "total_feedback": total_feedback,
            "positive_feedback": positive,
            "negative_feedback": negative,
        },
        "conversations": {
            "total": total_conversations,
            "today": today_conversations,
            "this_week": week_conversations,
        },
        "documents": {
            "total": doc_count,
            "total_chunks": chunk_count,
            "spaces": [
                {"id": sid, "name": sname, "doc_count": dcnt}
                for sid, sname, dcnt in space_stats
            ],
        },
        "gaps": {
            "pending": pending_gaps,
            "resolved": resolved_gaps,
            "recent": [
                {
                    "gap_id": g.id,
                    "question": g.question[:100] if g.question else "",
                    "created_at": g.created_at.isoformat() if g.created_at else "",
                }
                for g in recent_gaps
            ],
        },
        "top_questions": [
            {
                "conversation_id": cid,
                "title": title or f"会话#{cid}",
                "message_count": cnt,
            }
            for cid, title, cnt in top_questions
        ],
    }


@router.get("/faq-candidates")
def faq_candidates(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """高频问题 Top10 待确认：按问题文本聚类统计，排除已有 FAQ"""

    def normalize(text: str) -> str:
        return " ".join(text.strip().lower().split())[:200]

    raw_rows = (
        db.query(Message.content, func.count(Message.id).label("cnt"))
        .filter(Message.role == "user")
        .group_by(Message.content)
        .order_by(desc("cnt"))
        .limit(100)
        .all()
    )

    faq_set = {normalize(q[0]) for q in db.query(FAQ.question).all()}
    gap_set = {
        normalize(q[0])
        for q in db.query(KnowledgeGap.question).filter(KnowledgeGap.status == "pending").all()
        if q[0]
    }

    merged: dict[str, dict] = {}
    for content, cnt in raw_rows:
        key = normalize(content)
        if not key or key in faq_set:
            continue
        if key in merged:
            merged[key]["count"] += cnt
        else:
            merged[key] = {
                "question": content.strip(),
                "count": cnt,
                "has_gap": key in gap_set,
            }

    result = sorted(merged.values(), key=lambda x: x["count"], reverse=True)[:10]
    return result
