"""问答编排入口：多轮上下文 + 跨会话记忆 + LangGraph。"""

from __future__ import annotations

from typing import Any, Optional

from backend.agent.graph import get_graph
from backend.auth import CurrentUser
from backend import store

_CROSS_SESSION_HINTS = ("刚才那个", "刚才的问题", "上次那个", "上一问", "之前问的")


def _maybe_expand_question(message: str, user_id: int, conversation_id: Optional[int]) -> str:
    if not any(h in message for h in _CROSS_SESSION_HINTS):
        return message
    prev = store.last_user_question(user_id, exclude_conversation_id=conversation_id)
    if not prev:
        return message
    return f"{message}\n（用户指的是之前问过的：{prev}）"


def run_chat(
    *,
    message: str,
    conversation_id: Optional[int],
    user: CurrentUser,
) -> dict[str, Any]:
    store.init_db()
    text = message.strip()

    if conversation_id is None:
        conv = store.create_conversation(user.id, text)
        conversation_id = int(conv["id"])
        history: list[dict[str, str]] = []
    else:
        conv = store.get_conversation(conversation_id)
        if not conv or (conv["user_id"] != user.id and user.role != "admin"):
            raise PermissionError("会话不存在或无权访问")
        history = store.last_turns(conversation_id, n_turns=5)

    resolved = _maybe_expand_question(text, user.id, conversation_id)
    store.add_message(conversation_id=conversation_id, role="user", content=text)

    graph = get_graph()
    result = graph.invoke(
        {
            "message": resolved,
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "history": history,
            "route_kind": "rag",
            "lookup": None,
            "chunks": [],
            "reply": "",
            "citations": [],
            "confidence": "low",
            "gap_id": None,
            "create_gap": False,
        }
    )

    gap_id = result.get("gap_id")
    if result.get("create_gap"):
        gap_id = store.create_gap(
            question=text,
            user_id=user.id,
            username=user.username,
        )

    confidence = result.get("confidence") or "low"
    reply = result.get("reply") or ""
    citations = result.get("citations") or []
    if confidence == "low":
        citations = []

    assistant_id = store.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=reply,
        citations=citations,
        confidence=confidence,
        gap_id=gap_id,
    )

    payload: dict[str, Any] = {
        "conversation_id": conversation_id,
        "reply": reply,
        "citations": citations,
        "confidence": confidence,
        "message_id": assistant_id,
    }
    if confidence == "low" and gap_id is not None:
        payload["gap_id"] = gap_id
    return payload
