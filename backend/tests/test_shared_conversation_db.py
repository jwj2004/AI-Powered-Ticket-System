"""会话必须写到 A 的 zhida.db 同一张 conversation 表。"""

from __future__ import annotations

import sqlite3

from backend.config import get_settings, sqlite_path
from backend import store


def test_sqlite_path_follows_database_url(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    db = tmp_path / "zhida.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    get_settings.cache_clear()
    assert sqlite_path() == str(db)


def test_chat_writes_into_existing_a_conversation_table(monkeypatch, tmp_path):
    db = tmp_path / "zhida.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    get_settings.cache_clear()

    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE conversation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        INSERT INTO conversation (user_id, title, created_at)
        VALUES (2, '旧标题', '2026-01-01T00:00:00');
        """
    )
    conn.commit()
    conn.close()

    store.init_db()
    store.add_message(conversation_id=1, role="user", content="这次问的订单导出超时")
    store.add_message(conversation_id=1, role="assistant", content="按周拆分导出")

    listed = store.list_conversations(2)
    assert listed[0]["conversation_id"] == 1
    msgs = store.list_messages(1)
    assert msgs[-1]["content"] == "按周拆分导出"
    assert msgs[0]["content"] == "这次问的订单导出超时"
