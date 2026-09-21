"""问答编排入口：多轮上下文 + 跨会话记忆 + LangGraph + 热门缓存 + SSE。"""

from __future__ import annotations

import json
from typing import Any, Iterator, Optional

from backend.agent.graph import (
    feedback_node,
    get_graph,
    iter_reply_tokens,
    prepare_state,
)
from backend.auth import CurrentUser
from backend.config import get_settings
from backend import store

_CROSS_SESSION_HINTS = ("刚才那个", "刚才的问题", "上次那个", "上一问", "之前问的")


def _maybe_expand_question(message: str, user_id: int, conversation_id: Optional[int]) -> str:
    if not any(h in message for h in _CROSS_SESSION_HINTS):
        return message
    prev = store.last_user_question(user_id, exclude_conversation_id=conversation_id)
    if not prev:
        return message
    return f"{message}\n（用户指的是之前问过的：{prev}）"


def _open_conversation(
    *,
    message: str,
    conversation_id: Optional[int],
    user: CurrentUser,
) -> tuple[int, list[dict[str, str]], str]:
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
    return conversation_id, history, resolved


def _finalize_payload(
    *,
    conversation_id: int,
    user: CurrentUser,
    original_question: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    gap_id = result.get("gap_id")
    if result.get("create_gap") and not gap_id:
        gap_id = store.create_gap(
            question=original_question,
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

    if not result.get("from_cache"):
        store.save_hot_cache(
            original_question,
            reply=reply,
            citations=citations,
            confidence=confidence,
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


def _cached_result(question: str) -> Optional[dict[str, Any]]:
    settings = get_settings()
    cached = store.get_hot_cache(question, min_hits=settings.hot_cache_min_hits)
    if not cached:
        return None
    return {
        "reply": cached["reply"],
        "citations": cached["citations"],
        "confidence": cached["confidence"],
        "gap_id": None,
        "create_gap": False,
        "from_cache": True,
        "awaiting_feedback": True,
    }


def _initial_state(
    *,
    resolved: str,
    user: CurrentUser,
    history: list[dict[str, str]],
    persist_gap: bool,
) -> dict[str, Any]:
    return {
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
        "persist_gap": persist_gap,
    }


def run_chat(
    *,
    message: str,
    conversation_id: Optional[int],
    user: CurrentUser,
) -> dict[str, Any]:
    conversation_id, history, resolved = _open_conversation(
        message=message,
        conversation_id=conversation_id,
        user=user,
    )
    cached = _cached_result(message.strip())
    if cached:
        return _finalize_payload(
            conversation_id=conversation_id,
            user=user,
            original_question=message.strip(),
            result=cached,
        )

    graph = get_graph()
    result = graph.invoke(
        _initial_state(
            resolved=resolved,
            user=user,
            history=history,
            persist_gap=True,
        )
    )
    return _finalize_payload(
        conversation_id=conversation_id,
        user=user,
        original_question=message.strip(),
        result=result,
    )


def _sse_pack(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def iter_chat_sse(
    *,
    message: str,
    conversation_id: Optional[int],
    user: CurrentUser,
) -> Iterator[str]:
    """SSE：meta → token* → done，供前端打字机真流式渲染。"""
    conversation_id, history, resolved = _open_conversation(
        message=message,
        conversation_id=conversation_id,
        user=user,
    )
    cached = _cached_result(message.strip())
    if cached:
        result = dict(cached)
    else:
        result = prepare_state(
            _initial_state(
                resolved=resolved,
                user=user,
                history=history,
                persist_gap=True,
            )
        )

    meta = {
        "conversation_id": conversation_id,
        "confidence": result.get("confidence") or "low",
        "citations": result.get("citations") or [],
        "gap_id": result.get("gap_id"),
        "from_cache": bool(result.get("from_cache")),
    }
    yield _sse_pack("meta", meta)

    pieces: list[str] = []
    for token in iter_reply_tokens(result):  # type: ignore[arg-type]
        if not token:
            continue
        pieces.append(token)
        yield _sse_pack("token", {"delta": token})

    result["reply"] = "".join(pieces).strip() or (result.get("reply") or "")
    result = {**result, **feedback_node(result)}  # type: ignore[arg-type]
    payload = _finalize_payload(
        conversation_id=conversation_id,
        user=user,
        original_question=message.strip(),
        result=result,
    )
    yield _sse_pack("done", payload)
