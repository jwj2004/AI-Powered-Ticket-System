"""知识缺口/通知/看板接口测试"""
from app.models.knowledge_gap import KnowledgeGap
from app.models.notification import Notification


class TestGaps:
    def test_list_gaps_empty(self, client, admin_headers):
        r = client.get("/api/gaps", headers=admin_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_gaps_unauthorized(self, client, newbie_headers):
        r = client.get("/api/gaps", headers=newbie_headers)
        assert r.status_code == 403

    def test_create_and_list_gap(self, client, admin_headers, db_session):
        gap = KnowledgeGap(question="测试缺口", user_id=1, status="pending")
        db_session.add(gap)
        db_session.commit()

        r = client.get("/api/gaps", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["question"] == "测试缺口"

    def test_resolve_gap(self, client, admin_headers, db_session):
        gap = KnowledgeGap(question="待解决", user_id=1, status="pending")
        db_session.add(gap)
        db_session.commit()
        gap_id = gap.id

        r = client.post(f"/api/gaps/{gap_id}/resolve", json={"answer": "这是答案"}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_resolve_nonexistent_gap(self, client, admin_headers):
        r = client.post("/api/gaps/999/resolve", json={"answer": "x"}, headers=admin_headers)
        assert r.status_code == 404


class TestNotifications:
    def test_list_notifications_empty(self, client, admin_headers):
        r = client.get("/api/notifications", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_notification_after_gap_resolved(self, client, admin_headers, db_session):
        gap = KnowledgeGap(question="测试", user_id=1, status="pending")
        db_session.add(gap)
        db_session.commit()

        client.post(f"/api/gaps/{gap.id}/resolve", json={"answer": "答案"}, headers=admin_headers)

        r = client.get("/api/notifications", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_unread_only_filter(self, client, admin_headers, db_session):
        gap = KnowledgeGap(question="测试", user_id=1, status="pending")
        db_session.add(gap)
        db_session.commit()
        client.post(f"/api/gaps/{gap.id}/resolve", json={"answer": "答案"}, headers=admin_headers)

        r = client.get("/api/notifications?unread_only=true", headers=admin_headers)
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["read"] is False

    def test_mark_read(self, client, admin_headers, db_session):
        gap = KnowledgeGap(question="测试", user_id=1, status="pending")
        db_session.add(gap)
        db_session.commit()
        client.post(f"/api/gaps/{gap.id}/resolve", json={"answer": "答案"}, headers=admin_headers)

        notifs = client.get("/api/notifications", headers=admin_headers).json()
        notif_id = notifs["items"][0]["notification_id"]

        r = client.post(f"/api/notifications/{notif_id}/read", headers=admin_headers)
        assert r.status_code == 200

    def test_mark_all_read(self, client, admin_headers):
        r = client.post("/api/notifications/read-all", headers=admin_headers)
        assert r.status_code == 200


class TestDashboard:
    def test_dashboard_admin(self, client, admin_headers):
        r = client.get("/api/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "questions" in data
        assert "conversations" in data
        assert "documents" in data
        assert "gaps" in data
        assert "top_questions" in data

    def test_dashboard_non_admin(self, client, newbie_headers):
        r = client.get("/api/dashboard", headers=newbie_headers)
        assert r.status_code == 403

    def test_dashboard_after_chat(self, client, admin_headers):
        client.post("/api/chat", json={"message": "测试", "conversation_id": None}, headers=admin_headers)

        r = client.get("/api/dashboard", headers=admin_headers)
        data = r.json()
        assert data["questions"]["total_today"] >= 1
        assert data["conversations"]["total"] >= 1
