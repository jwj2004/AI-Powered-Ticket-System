"""问答契约测试（mock 检索 + JWT）。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _login(client: TestClient, username: str = "ops", password: str = "ops123") -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["token"]


def _auth(token: str, *, accept: str = "application/json") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": accept}


def test_login_and_health(client: TestClient):
    assert client.get("/api/health").json()["status"] == "ok"
    bad = client.post("/api/auth/login", json={"username": "ops", "password": "wrong"})
    assert bad.status_code == 401


def test_chat_requires_jwt(client: TestClient):
    resp = client.post("/api/chat", json={"message": "订单导出超时怎么办？", "conversation_id": None})
    assert resp.status_code == 401


def test_chat_high_confidence_with_citations(client: TestClient):
    token = _login(client)
    resp = client.post(
        "/api/chat",
        json={"message": "订单导出超时怎么办？", "conversation_id": None},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence"] == "high"
    assert data["conversation_id"] >= 1
    assert data["message_id"] >= 1
    assert data["reply"]
    assert "5 万" in data["reply"] or "5万" in data["reply"] or "五万" in data["reply"]
    assert 1 <= len(data["citations"]) <= 5
    for item in data["citations"]:
        assert "document_id" in item
        assert "title" in item
        assert "chunk_index" in item
    assert "gap_id" not in data or data.get("gap_id") is None


def test_chat_lookup_error_code(client: TestClient):
    token = _login(client)
    resp = client.post(
        "/api/chat",
        json={"message": "PAY_CALLBACK_TIMEOUT 怎么处理", "conversation_id": None},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence"] == "high"
    assert "PAY_CALLBACK_TIMEOUT" in data["reply"] or "回调" in data["reply"]


def test_chat_low_confidence_writes_gap(client: TestClient):
    token = _login(client)
    resp = client.post(
        "/api/chat",
        json={"message": "量子加密证书在工单里怎么配置", "conversation_id": None},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence"] == "low"
    assert data["reply"] == "这个问题我没找到可靠依据，已记录，管理员补全后会通知你。"
    assert data["citations"] == []
    assert data["gap_id"] >= 1


def test_chat_refuse_chitchat(client: TestClient):
    token = _login(client)
    resp = client.post(
        "/api/chat",
        json={"message": "今天天气怎么样，帮我写一首诗", "conversation_id": None},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence"] == "low"
    assert data["citations"] == []
    assert "gap_id" not in data


def test_chat_rejects_blank_message(client: TestClient):
    token = _login(client)
    resp = client.post(
        "/api/chat",
        json={"message": "   ", "conversation_id": None},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_multiturn_and_history_endpoints(client: TestClient):
    token = _login(client)
    first = client.post(
        "/api/chat",
        json={"message": "订单导出超时怎么办？", "conversation_id": None},
        headers=_auth(token),
    ).json()
    cid = first["conversation_id"]
    second = client.post(
        "/api/chat",
        json={"message": "那高峰时段怎么办？", "conversation_id": cid},
        headers=_auth(token),
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == cid

    listed = client.get("/api/conversations", headers=_auth(token))
    assert listed.status_code == 200
    assert any(item["conversation_id"] == cid for item in listed.json())

    msgs = client.get(f"/api/conversations/{cid}/messages", headers=_auth(token))
    assert msgs.status_code == 200
    roles = [m["role"] for m in msgs.json()]
    assert roles.count("user") == 2
    assert roles.count("assistant") == 2
    last = msgs.json()[-1]
    assert last["message_id"] == second.json()["message_id"]
    assert last["confidence"] in {"high", "medium", "low"}


def test_feedback_and_gap_resolve_notifies_user(client: TestClient):
    ops_token = _login(client, "ops", "ops123")
    chat = client.post(
        "/api/chat",
        json={"message": "量子加密证书在工单里怎么配置", "conversation_id": None},
        headers=_auth(ops_token),
    ).json()
    gap_id = chat["gap_id"]
    fb = client.post(
        "/api/feedback",
        json={"message_id": chat["message_id"], "useful": False},
        headers=_auth(ops_token),
    )
    assert fb.status_code == 200
    assert fb.json() == {"ok": True}

    admin_token = _login(client, "admin", "admin123")
    forbidden = client.get("/api/gaps", headers=_auth(ops_token))
    assert forbidden.status_code == 403

    gaps = client.get("/api/gaps", headers=_auth(admin_token))
    assert gaps.status_code == 200
    gap_payload = gaps.json()
    assert gap_payload["total"] >= 1
    assert any(g["gap_id"] == gap_id for g in gap_payload["items"])

    resolved = client.post(
        f"/api/gaps/{gap_id}/resolve",
        json={"answer": "按周拆分导出即可", "document_id": None},
        headers=_auth(admin_token),
    )
    assert resolved.status_code == 200
    assert resolved.json()["ok"] is True
    assert resolved.json()["notified_user_id"] == 2

    notes = client.get("/api/notifications", headers=_auth(ops_token))
    assert notes.status_code == 200
    note_payload = notes.json()
    assert note_payload["total"] >= 1
    assert note_payload["unread"] >= 1
    assert note_payload["items"][0]["gap_id"] == gap_id
    assert note_payload["items"][0]["read"] is False

    nid = note_payload["items"][0]["notification_id"]
    read = client.post(f"/api/notifications/{nid}/read", headers=_auth(ops_token))
    assert read.json() == {"ok": True}


def test_chat_contract_field_is_message(client: TestClient):
    token = _login(client)
    resp = client.post(
        "/api/chat",
        json={"message": "订单导出超时怎么办？", "conversation_id": None},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert "reply" in resp.json()


def test_chat_accepts_legacy_query_alias(client: TestClient):
    """联调前部分调用方曾传 query；契约字段是 message，两者都要能进。"""
    token = _login(client)
    resp = client.post(
        "/api/chat",
        json={"query": "订单导出超时怎么办？", "conversation_id": None},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["confidence"] == "high"


def test_accepts_token_payload_shape_from_a(client: TestClient):
    """A 签发的 token 只有 sub/username/role，没有 user_id。"""
    import jwt
    from datetime import datetime, timedelta, timezone

    from backend.config import get_settings

    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "2",
            "username": "ops",
            "role": "ops",
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            "iat": datetime.now(timezone.utc),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    resp = client.get("/api/conversations", headers=_auth(token))
    assert resp.status_code == 200
