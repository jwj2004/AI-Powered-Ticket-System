from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter(prefix="/api/conversations", tags=["会话"])


@router.get("")
def list_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [
        {
            "conversation_id": c.id,
            "title": c.title,
            "updated_at": c.updated_at.isoformat() if c.updated_at else "",
        }
        for c in convs
    ]


@router.get("/{conv_id}/messages")
def list_messages(
    conv_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else "",
            "citations": [],
            "confidence": m.confidence,
            "message_id": m.id,
        }
        for m in messages
    ]


@router.delete("/{conv_id}")
def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.query(Message).filter(Message.conversation_id == conv_id).delete()
    db.delete(conv)
    db.commit()
    return {"ok": True}
