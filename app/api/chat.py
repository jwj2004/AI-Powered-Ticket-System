from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.feedback import Feedback

router = APIRouter(prefix="/api", tags=["问答"])


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    query: str


class Citation(BaseModel):
    source: str
    content: str
    score: float


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    citations: list[Citation]
    confidence: str


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = None
    if req.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
        if not conv or conv.user_id != user.id:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        conv = Conversation(user_id=user.id, title=req.query[:50])
        db.add(conv)
        db.flush()

    user_msg = Message(conversation_id=conv.id, role="user", content=req.query)
    db.add(user_msg)
    db.flush()

    # TODO(B): LangGraph 编排 → 路由节点 → 检索节点 → 生成节点 → 质量节点
    # A 提供: detect_error_code() + VectorRetriever.search()
    # B 提供: LLM 生成 + 引用拼装
    # 当前返回占位
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content="[待 B 接入 LLM]",
        confidence="low",
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(conv)
    db.refresh(assistant_msg)

    return ChatResponse(
        conversation_id=conv.id,
        message_id=assistant_msg.id,
        answer=assistant_msg.content,
        citations=[],
        confidence=assistant_msg.confidence,
    )


class FeedbackRequest(BaseModel):
    message_id: int
    useful: bool


@router.post("/feedback")
def feedback(
    req: FeedbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    msg = db.query(Message).filter(Message.id == req.message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    fb = Feedback(message_id=req.message_id, useful=req.useful)
    db.add(fb)
    db.commit()
    return {"ok": True}
