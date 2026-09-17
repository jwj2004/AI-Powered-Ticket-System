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


class Citation(BaseModel):
    document_id: int
    title: str
    chunk_index: int


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    citations: list[Citation]
    confidence: str
    message_id: int


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
        conv = Conversation(user_id=user.id, title=req.message[:50])
        db.add(conv)
        db.flush()

    user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
    db.add(user_msg)
    db.flush()

    # RAG 检索：错误码精确 + 文档块向量 + 工单向量
    from app.services.vector_retriever import VectorRetriever
    search_result = VectorRetriever.hybrid_search(req.message, top_k=3)

    # 构建 citations
    citations = []
    for chunk in search_result.get("doc_chunks", []):
        citations.append(Citation(
            document_id=chunk["document_id"],
            title=chunk["title"],
            chunk_index=chunk["chunk_index"],
        ))

    # 构建回复（B 接入 LLM 后替换此段）
    reply_parts = []

    if search_result["error_code"] and search_result["solution"]:
        reply_parts.append(f"**错误码**: {search_result['error_code']}")
        reply_parts.append(f"**解决方案**: {search_result['solution']}")

    if search_result["doc_chunks"]:
        reply_parts.append("**相关文档**:")
        for chunk in search_result["doc_chunks"][:3]:
            reply_parts.append(f"- [{chunk['title']}] 块{chunk['chunk_index']}: {chunk['content'][:100]}...")

    if search_result["tickets"]:
        reply_parts.append("**相似工单**:")
        for t in search_result["tickets"][:2]:
            reply_parts.append(f"- 工单{t['ticket_id']}: {t['raw_text'][:80]}...")

    reply = "\n".join(reply_parts) if reply_parts else "暂未找到相关信息，已记录为知识缺口。"

    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=reply,
        confidence=search_result["confidence"],
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(conv)
    db.refresh(assistant_msg)

    return ChatResponse(
        conversation_id=conv.id,
        reply=reply,
        citations=citations,
        confidence=search_result["confidence"],
        message_id=assistant_msg.id,
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
