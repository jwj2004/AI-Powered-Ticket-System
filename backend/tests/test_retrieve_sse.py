"""混合检索、查询改写、重排、热门缓存、SSE 流式。"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from backend.retrieve.hybrid import hybrid_rerank_chunks
from backend.retrieve.rerank import rerank_chunks
from backend.retrieve.rewrite import rewrite_query
from backend.tests.test_chat_api import _auth, _login


def test_query_rewrite_expands_colloquial_payment():
    rewritten = rewrite_query("微信付了钱订单还是没更新")
    assert "支付" in rewritten or "待支付" in rewritten or "回调" in rewritten


def test_hybrid_bm25_promotes_keyword_match():
    chunks = [
        {
            "document_id": 1,
            "title": "无关文档",
            "chunk_index": 0,
            "content": "机房巡检与空调设定",
            "score": 0.91,
        },
        {
            "document_id": 2,
            "title": "订单导出超时排查",
            "chunk_index": 3,
            "content": "订单导出超时通常是因为一次导出超过 5 万条。建议按周拆分导出。",
            "score": 0.40,
        },
    ]
    fused = hybrid_rerank_chunks("订单导出超时怎么办", chunks, top_k=2)
    assert fused[0]["document_id"] == 2
    assert "bm25_score" in fused[0]


def test_rerank_puts_overlap_first():
    chunks = [
        {
            "document_id": 1,
            "title": "优惠券核销失败",
            "chunk_index": 0,
            "content": "核销失败常见原因是活动叠加冲突或券已过期。",
            "score": 0.88,
        },
        {
            "document_id": 2,
            "title": "订单导出超时排查",
            "chunk_index": 3,
            "content": "订单导出超时通常是因为一次导出超过 5 万条。",
            "score": 0.50,
        },
    ]
    ranked = rerank_chunks("订单导出超过五万条怎么拆", chunks, top_k=2)
    assert ranked[0]["document_id"] == 2
    assert "rerank_score" in ranked[0]


def test_hot_question_cache_returns_same_answer(client: TestClient, monkeypatch):
    monkeypatch.setenv("HOT_CACHE_MIN_HITS", "2")
    from backend.config import get_settings
    from backend.agent import graph as graph_mod

    get_settings.cache_clear()
    graph_mod._GRAPH = None

    token = _login(client)
    q = {"message": "订单导出超时怎么办？", "conversation_id": None}
    first = client.post("/api/chat", json=q, headers=_auth(token)).json()
    second = client.post("/api/chat", json=q, headers=_auth(token)).json()
    third = client.post("/api/chat", json=q, headers=_auth(token)).json()
    assert first["confidence"] == "high"
    assert second["confidence"] == "high"
    assert third["reply"] == second["reply"]
    assert third["citations"] == second["citations"]


def test_chat_sse_streams_tokens(client: TestClient):
    token = _login(client)
    with client.stream(
        "POST",
        "/api/chat",
        json={"message": "订单导出超时怎么办？", "conversation_id": None},
        headers=_auth(token, accept="text/event-stream"),
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        body = "".join(resp.iter_text())

    assert "event: meta" in body
    assert "event: token" in body
    assert "event: done" in body
    done_line = [ln for ln in body.splitlines() if ln.startswith("data: ") and "message_id" in ln][-1]
    payload = json.loads(done_line[len("data: ") :])
    assert payload["confidence"] == "high"
    assert payload["reply"]
    assert payload["message_id"] >= 1


def test_chat_json_when_stream_false(client: TestClient):
    token = _login(client)
    resp = client.post(
        "/api/chat",
        json={"message": "订单导出超时怎么办？", "conversation_id": None, "stream": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "json" in (resp.headers.get("content-type") or "")
    assert resp.json()["confidence"] == "high"


def test_chat_defaults_to_sse_without_accept_json(client: TestClient):
    token = _login(client)
    with client.stream(
        "POST",
        "/api/chat",
        json={"message": "订单导出超时怎么办？", "conversation_id": None},
        headers={"Authorization": f"Bearer {token}"},
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        body = "".join(resp.iter_text())
    assert "event: token" in body
    assert "event: done" in body
