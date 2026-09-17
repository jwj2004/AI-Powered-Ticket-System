"""B 模块本地库：会话、消息、反馈、知识缺口、通知。"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Optional

from backend.config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    citations_json TEXT,
    confidence TEXT,
    gap_id INTEGER,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    useful INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge_gap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    status TEXT NOT NULL,
    answer TEXT,
    resolved_by INTEGER,
    resolved_at TEXT,
    document_id INTEGER,
    source_message_id INTEGER,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    gap_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    settings = get_settings()
    path = settings.database_path
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def create_conversation(user_id: int, title: str) -> dict[str, Any]:
    ts = now_iso()
    title = (title or "新对话").strip()[:40] or "新对话"
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO conversation (user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, title, ts, ts),
        )
        conn.commit()
        return {
            "id": cur.lastrowid,
            "user_id": user_id,
            "title": title,
            "created_at": ts,
            "updated_at": ts,
        }
    finally:
        conn.close()


def get_conversation(conversation_id: int) -> Optional[dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM conversation WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def touch_conversation(conversation_id: int) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE conversation SET updated_at = ? WHERE id = ?",
            (now_iso(), conversation_id),
        )
        conn.commit()
    finally:
        conn.close()


def list_conversations(user_id: int) -> list[dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, title, updated_at
            FROM conversation
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [
            {
                "conversation_id": row["id"],
                "title": row["title"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def add_message(
    *,
    conversation_id: int,
    role: str,
    content: str,
    citations: Optional[list[dict[str, Any]]] = None,
    confidence: Optional[str] = None,
    gap_id: Optional[int] = None,
) -> int:
    ts = now_iso()
    citations_json = json.dumps(citations, ensure_ascii=False) if citations is not None else None
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO message (
                conversation_id, role, content, citations_json, confidence, gap_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (conversation_id, role, content, citations_json, confidence, gap_id, ts),
        )
        conn.execute(
            "UPDATE conversation SET updated_at = ? WHERE id = ?",
            (ts, conversation_id),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_messages(conversation_id: int) -> list[dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, role, content, citations_json, confidence, gap_id, created_at
            FROM message
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            item: dict[str, Any] = {
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"],
            }
            if row["role"] == "assistant":
                citations = json.loads(row["citations_json"] or "[]")
                item["citations"] = citations
                item["confidence"] = row["confidence"]
                item["message_id"] = row["id"]
            items.append(item)
        return items
    finally:
        conn.close()


def last_turns(conversation_id: int, n_turns: int = 5) -> list[dict[str, str]]:
    """最近 n 轮（最多 2n 条消息），按时间正序。"""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT role, content FROM message
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (conversation_id, n_turns * 2),
        ).fetchall()
        items = [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
        return items
    finally:
        conn.close()


def last_user_question(user_id: int, exclude_conversation_id: Optional[int] = None) -> Optional[str]:
    """跨会话：该用户最近一条提问。"""
    conn = get_conn()
    try:
        if exclude_conversation_id is None:
            row = conn.execute(
                """
                SELECT m.content FROM message m
                JOIN conversation c ON c.id = m.conversation_id
                WHERE c.user_id = ? AND m.role = 'user'
                ORDER BY m.id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT m.content FROM message m
                JOIN conversation c ON c.id = m.conversation_id
                WHERE c.user_id = ? AND m.role = 'user' AND m.conversation_id != ?
                ORDER BY m.id DESC
                LIMIT 1
                """,
                (user_id, exclude_conversation_id),
            ).fetchone()
        return row["content"] if row else None
    finally:
        conn.close()


def get_message(message_id: int) -> Optional[dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM message WHERE id = ?", (message_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        conv = conn.execute(
            "SELECT user_id FROM conversation WHERE id = ?",
            (data["conversation_id"],),
        ).fetchone()
        data["user_id"] = conv["user_id"] if conv else None
        return data
    finally:
        conn.close()


def add_feedback(message_id: int, user_id: int, useful: bool) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO feedback (message_id, user_id, useful, created_at) VALUES (?, ?, ?, ?)",
            (message_id, user_id, 1 if useful else 0, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


def count_thumbs_down(message_id: int) -> int:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM feedback WHERE message_id = ? AND useful = 0",
            (message_id,),
        ).fetchone()
        return int(row["n"] if row else 0)
    finally:
        conn.close()


def create_gap(
    *,
    question: str,
    user_id: int,
    username: str,
    source_message_id: Optional[int] = None,
) -> int:
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO knowledge_gap (
                question, user_id, username, status, answer, resolved_by,
                resolved_at, document_id, source_message_id, created_at
            ) VALUES (?, ?, ?, 'pending', NULL, NULL, NULL, NULL, ?, ?)
            """,
            (question, user_id, username, source_message_id, now_iso()),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_gaps() -> list[dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, question, user_id, username, status, created_at
            FROM knowledge_gap
            ORDER BY id DESC
            """
        ).fetchall()
        return [
            {
                "gap_id": row["id"],
                "question": row["question"],
                "user_id": row["user_id"],
                "username": row["username"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_gap(gap_id: int) -> Optional[dict[str, Any]]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM knowledge_gap WHERE id = ?", (gap_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def resolve_gap(
    *,
    gap_id: int,
    answer: str,
    resolved_by: int,
    document_id: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    gap = get_gap(gap_id)
    if not gap:
        return None
    ts = now_iso()
    conn = get_conn()
    try:
        conn.execute(
            """
            UPDATE knowledge_gap
            SET status = 'resolved', answer = ?, resolved_by = ?, resolved_at = ?, document_id = ?
            WHERE id = ?
            """,
            (answer, resolved_by, ts, document_id, gap_id),
        )
        conn.execute(
            """
            INSERT INTO notification (user_id, gap_id, question, answer, read, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (gap["user_id"], gap_id, gap["question"], answer, ts),
        )
        conn.commit()
        return {"ok": True, "notified_user_id": gap["user_id"]}
    finally:
        conn.close()


def list_notifications(user_id: int) -> list[dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, gap_id, question, answer, read, created_at
            FROM notification
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()
        return [
            {
                "notification_id": row["id"],
                "gap_id": row["gap_id"],
                "question": row["question"],
                "answer": row["answer"],
                "read": bool(row["read"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def mark_notification_read(notification_id: int, user_id: int) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT user_id FROM notification WHERE id = ?",
            (notification_id,),
        ).fetchone()
        if not row or row["user_id"] != user_id:
            return False
        conn.execute(
            "UPDATE notification SET read = 1 WHERE id = ?",
            (notification_id,),
        )
        conn.commit()
        return True
    finally:
        conn.close()
