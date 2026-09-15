"""/api/draft 端到端契约测试（mock retrieve）。"""

from fastapi.testclient import TestClient

from backend.config import get_settings
from main import app

client = TestClient(app)


def setup_module():
    get_settings.cache_clear()


def test_draft_high_confidence_with_payment_query():
    resp = client.post(
        "/api/draft",
        json={
            "raw_text": "客户说已经微信付了198块钱，但是后台订单一直是待支付",
            "customer_id": "C003",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_id"].startswith("q_")
    assert data["confidence"] == "high"
    assert data["error_code"] == "PAY_CALLBACK_TIMEOUT"
    assert data["draft"] is not None
    assert "v3.8.5" in data["draft"]
    assert isinstance(data["evidence"], list)
    assert 1 <= len(data["evidence"]) <= 3
    for item in data["evidence"]:
        assert "ticket_id" in item
        assert "summary" in item
        assert len(item["summary"]) <= 100
    assert "message" not in data or data.get("message") is None


def test_draft_low_confidence_when_no_evidence():
    resp = client.post(
        "/api/draft",
        json={
            "raw_text": "今天天气怎么样，帮我写一首诗",
            "customer_id": None,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_id"].startswith("q_")
    assert data["confidence"] == "low"
    assert data["draft"] is None
    assert data["error_code"] is None
    assert data["evidence"] == []
    assert data["message"] == "未找到可靠依据，建议转二线处理"


def test_draft_rejects_blank_raw_text():
    resp = client.post("/api/draft", json={"raw_text": "   ", "customer_id": None})
    assert resp.status_code == 422


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
