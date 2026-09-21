"""会话读写 A 的 zhida.db（conversation / message）；缺口、通知、热门缓存仍由 B 建表。"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime
from typing import Any, Optional

from backend.config import sqlite_path

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
CREATE TABLE IF NOT EXISTS hot_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_key TEXT NOT NULL UNIQUE,
    reply TEXT NOT NULL,
    citations_json TEXT NOT NULL DEFAULT '[]',
    confidence TEXT NOT NULL,
    hit_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row[0] for row in rows}


def _pick_table(conn: sqlite3.Connection, candidates: tuple[str, ...]) -> str:
    names = _table_names(conn)
    for name in candidates:
        if name in names:
            return name
    return candidates[0]


def conversation_table(conn: sqlite3.Connection) -> str:
    return _pick_table(conn, ("conversation", "conversations"))


def message_table(conn: sqlite3.Connection) -> str:
    return _pick_table(conn, ("message", "messages"))


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()}


def _insert(conn: sqlite3.Connection, table: str, data: dict[str, Any]) -> int:
    cols = _columns(conn, table)
    fields = [key for key in data if key in cols]
    placeholders = ", ".join("?" for _ in fields)
    sql = f'INSERT INTO "{table}" ({", ".join(fields)}) VALUES ({placeholders})'
    cur = conn.execute(sql, [data[key] for key in fields])
    return int(cur.lastrowid)


def get_conn() -> sqlite3.Connection:
    path = sqlite_path()
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
        table = conversation_table(conn)
        cols = _columns(conn, table)
        data: dict[str, Any] = {"user_id": user_id, "title": title, "created_at": ts}
        if "updated_at" in cols:
            data["updated_at"] = ts
        if "owner_id" in cols and "user_id" not in cols:
            data["owner_id"] = user_id
            data.pop("user_id", None)
        row_id = _insert(conn, table, data)
        conn.commit()
        return {
            "id": row_id,
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
        table = conversation_table(conn)
        row = conn.execute(
            f'SELECT * FROM "{table}" WHERE id = ?',
            (conversation_id,),
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        if "user_id" not in data and data.get("owner_id") is not None:
            data["user_id"] = data["owner_id"]
        return data
    finally:
        conn.close()


def touch_conversation(conversation_id: int) -> None:
    conn = get_conn()
    try:
        table = conversation_table(conn)
        cols = _columns(conn, table)
        ts = now_iso()
        if "updated_at" in cols:
            conn.execute(
                f'UPDATE "{table}" SET updated_at = ? WHERE id = ?',
                (ts, conversation_id),
            )
        elif "created_at" not in cols:
            pass
        conn.commit()
    finally:
        conn.close()


def list_conversations(user_id: int) -> list[dict[str, Any]]:
    conn = get_conn()
    try:
        table = conversation_table(conn)
        cols = _columns(conn, table)
        owner_col = "user_id" if "user_id" in cols else "owner_id"
        order_col = next(
            (name for name in ("updated_at", "created_at", "id") if name in cols),
            "id",
        )
        select_title = "title" if "title" in cols else "id"
        select_updated = order_col
        rows = conn.execute(
            f'''
            SELECT id, {select_title} AS title, {select_updated} AS updated_at
            FROM "{table}"
            WHERE {owner_col} = ?
            ORDER BY {select_updated} DESC
            ''',
            (user_id,),
        ).fetchall()
        return [
            {
                "conversation_id": row["id"],
                "title": row["title"] if select_title == "title" else str(row["id"]),
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
        table = message_table(conn)
        cols = _columns(conn, table)
        data: dict[str, Any] = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": ts,
            "citations_json": citations_json,
            "confidence": confidence,
            "gap_id": gap_id,
        }
        if "citations" in cols and "citations_json" not in cols:
            data["citations"] = citations_json
        row_id = _insert(conn, table, data)
        conv_table = conversation_table(conn)
        conv_cols = _columns(conn, conv_table)
        if "updated_at" in conv_cols:
            conn.execute(
                f'UPDATE "{conv_table}" SET updated_at = ? WHERE id = ?',
                (ts, conversation_id),
            )
        conn.commit()
        return row_id
    finally:
        conn.close()


def list_messages(conversation_id: int) -> list[dict[str, Any]]:
    conn = get_conn()
    try:
        table = message_table(conn)
        cols = _columns(conn, table)
        citation_col = "citations_json" if "citations_json" in cols else (
            "citations" if "citations" in cols else None
        )
        rows = conn.execute(
            f'''
            SELECT * FROM "{table}"
            WHERE conversation_id = ?
            ORDER BY id ASC
            ''',
            (conversation_id,),
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            item: dict[str, Any] = {
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"] if "created_at" in row.keys() else None,
            }
            if row["role"] == "assistant":
                raw = "[]"
                if citation_col:
                    raw = row[citation_col] or "[]"
                if isinstance(raw, str):
                    citations = json.loads(raw or "[]")
                else:
                    citations = raw or []
                item["citations"] = citations
                item["confidence"] = row["confidence"] if "confidence" in row.keys() else None
                item["message_id"] = row["id"]
            items.append(item)
        return items
    finally:
        conn.close()


def last_turns(conversation_id: int, n_turns: int = 5) -> list[dict[str, str]]:
    """最近 n 轮（最多 2n 条消息），按时间正序。"""
    conn = get_conn()
    try:
        table = message_table(conn)
        rows = conn.execute(
            f'''
            SELECT role, content FROM "{table}"
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            ''',
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
        msg = message_table(conn)
        conv = conversation_table(conn)
        conv_cols = _columns(conn, conv)
        owner_col = "user_id" if "user_id" in conv_cols else "owner_id"
        if exclude_conversation_id is None:
            row = conn.execute(
                f'''
                SELECT m.content FROM "{msg}" m
                JOIN "{conv}" c ON c.id = m.conversation_id
                WHERE c.{owner_col} = ? AND m.role = 'user'
                ORDER BY m.id DESC
                LIMIT 1
                ''',
                (user_id,),
            ).fetchone()
        else:
            row = conn.execute(
                f'''
                SELECT m.content FROM "{msg}" m
                JOIN "{conv}" c ON c.id = m.conversation_id
                WHERE c.{owner_col} = ? AND m.role = 'user' AND m.conversation_id != ?
                ORDER BY m.id DESC
                LIMIT 1
                ''',
                (user_id, exclude_conversation_id),
            ).fetchone()
        return row["content"] if row else None
    finally:
        conn.close()


def get_message(message_id: int) -> Optional[dict[str, Any]]:
    conn = get_conn()
    try:
        msg = message_table(conn)
        conv = conversation_table(conn)
        conv_cols = _columns(conn, conv)
        owner_col = "user_id" if "user_id" in conv_cols else "owner_id"
        row = conn.execute(f'SELECT * FROM "{msg}" WHERE id = ?', (message_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        owner = conn.execute(
            f'SELECT {owner_col} AS user_id FROM "{conv}" WHERE id = ?',
            (data["conversation_id"],),
        ).fetchone()
        data["user_id"] = owner["user_id"] if owner else None
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


_HOT_KEY_RE = re.compile(r"[\s？?！!。，,、.；;：:]+")


def clear_hot_cache() -> int:
    """删掉热缓存。答案存在 SQLite，重启进程不会自动失效。"""
    conn = get_conn()
    try:
        cur = conn.execute("DELETE FROM hot_cache")
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def normalize_question_key(question: str) -> str:
    return _HOT_KEY_RE.sub("", (question or "").strip().lower())


def get_hot_cache(question: str, *, min_hits: int) -> Optional[dict[str, Any]]:
    """高频且已有高质量答案时直接返回缓存。"""
    key = normalize_question_key(question)
    if not key:
        return None
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM hot_cache WHERE question_key = ?",
            (key,),
        ).fetchone()
        if not row:
            return None
        if int(row["hit_count"]) < min_hits:
            return None
        if row["confidence"] not in {"high", "medium"}:
            return None
        ts = now_iso()
        conn.execute(
            "UPDATE hot_cache SET hit_count = hit_count + 1, updated_at = ? WHERE question_key = ?",
            (ts, key),
        )
        conn.commit()
        return {
            "reply": row["reply"],
            "citations": json.loads(row["citations_json"] or "[]"),
            "confidence": row["confidence"],
            "from_cache": True,
        }
    finally:
        conn.close()


def save_hot_cache(
    question: str,
    *,
    reply: str,
    citations: list[dict[str, Any]],
    confidence: str,
) -> None:
    if confidence not in {"high", "medium"} or not (reply or "").strip():
        return
    key = normalize_question_key(question)
    if not key:
        return
    ts = now_iso()
    citations_json = json.dumps(citations or [], ensure_ascii=False)
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO hot_cache (
                question_key, reply, citations_json, confidence, hit_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(question_key) DO UPDATE SET
                reply = excluded.reply,
                citations_json = excluded.citations_json,
                confidence = excluded.confidence,
                hit_count = hot_cache.hit_count + 1,
                updated_at = excluded.updated_at
            """,
            (key, reply, citations_json, confidence, ts, ts),
        )
        conn.commit()
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
