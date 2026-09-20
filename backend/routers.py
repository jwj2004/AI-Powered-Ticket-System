"""B 负责的 HTTP 路由：登录（独立联调）、会话、反馈、缺口闭环、通知。

问答入口只在 app/api/chat.py，这里不再注册 /api/chat。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from backend.auth import CurrentUser, create_access_token, find_seed_user, get_current_user, require_admin
from backend.clients.retrieve_client import RetrieveClient
from backend import store

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class FeedbackRequest(BaseModel):
    message_id: int
    useful: bool


class ResolveGapRequest(BaseModel):
    answer: str
    document_id: Optional[int] = None

    @field_validator("answer")
    @classmethod
    def answer_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("answer 不能为空")
        return text


@router.post("/api/auth/login")
def login(body: LoginRequest) -> dict[str, Any]:
    """A 为正式登录源。B 提供种子账号，便于本模块单独联调。"""
    row = find_seed_user(body.username, body.password)
    if not row:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(
        user_id=row["id"],
        username=row["username"],
        role=row["role"],
    )
    return {"token": token, "role": row["role"], "username": row["username"]}


@router.post("/api/feedback")
def feedback(body: FeedbackRequest, user: CurrentUser = Depends(get_current_user)) -> dict[str, bool]:
    store.init_db()
    msg = store.get_message(body.message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    if msg["role"] != "assistant":
        raise HTTPException(status_code=400, detail="只能对助手回复点赞或点踩")
    if msg["user_id"] != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权反馈该消息")

    store.add_feedback(body.message_id, user.id, body.useful)

    if not body.useful and store.count_thumbs_down(body.message_id) >= 1:
        if not msg.get("gap_id"):
            conv_messages = store.list_messages(msg["conversation_id"])
            question = ""
            for item in reversed(conv_messages):
                if item["role"] == "user":
                    question = item["content"]
                    break
            if question:
                store.create_gap(
                    question=question,
                    user_id=user.id,
                    username=user.username,
                    source_message_id=body.message_id,
                )
    return {"ok": True}


@router.get("/api/conversations")
def conversations(user: CurrentUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    store.init_db()
    return store.list_conversations(user.id)


@router.get("/api/conversations/{conversation_id}/messages")
def conversation_messages(
    conversation_id: int,
    user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    store.init_db()
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if conv["user_id"] != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看该会话")
    return store.list_messages(conversation_id)


@router.get("/api/gaps")
def list_gaps(user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(user)
    store.init_db()
    items = store.list_gaps()
    return {"total": len(items), "items": items}


@router.post("/api/gaps/{gap_id}/resolve")
def resolve_gap(
    gap_id: int,
    body: ResolveGapRequest,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    require_admin(user)
    store.init_db()
    result = store.resolve_gap(
        gap_id=gap_id,
        answer=body.answer,
        resolved_by=user.id,
        document_id=body.document_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="知识缺口不存在")
    if body.document_id is not None:
        RetrieveClient().reindex_document(body.document_id)
    return result


@router.get("/api/notifications")
def notifications(user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    store.init_db()
    items = store.list_notifications(user.id)
    unread = sum(1 for item in items if not item.get("read"))
    return {"total": len(items), "unread": unread, "items": items}


@router.post("/api/notifications/{notification_id}/read")
def read_notification(
    notification_id: int,
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, bool]:
    store.init_db()
    ok = store.mark_notification_read(notification_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="通知不存在")
    return {"ok": True}
