"""问答接口测试"""
import io


class TestChat:
    def test_chat_without_token(self, client):
        r = client.post("/api/chat", json={"message": "test", "conversation_id": None})
        assert r.status_code in (401, 403, 422)

    def test_chat_creates_conversation(self, client, admin_headers):
        r = client.post("/api/chat", json={"message": "测试问题", "conversation_id": None}, headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "conversation_id" in data
        assert "reply" in data
        assert "confidence" in data
        assert "message_id" in data
        assert isinstance(data["citations"], list)

    def test_chat_continues_conversation(self, client, admin_headers):
        r1 = client.post("/api/chat", json={"message": "第一轮", "conversation_id": None}, headers=admin_headers)
        conv_id = r1.json()["conversation_id"]

        r2 = client.post("/api/chat", json={"message": "第二轮", "conversation_id": conv_id}, headers=admin_headers)
        assert r2.status_code == 200
        assert r2.json()["conversation_id"] == conv_id

    def test_chat_nonexistent_conversation(self, client, admin_headers):
        r = client.post("/api/chat", json={"message": "test", "conversation_id": 999}, headers=admin_headers)
        assert r.status_code == 404

    def test_chat_empty_message(self, client, admin_headers):
        r = client.post("/api/chat", json={"message": "", "conversation_id": None}, headers=admin_headers)
        assert r.status_code in (200, 422)


class TestFeedback:
    def test_submit_feedback(self, client, admin_headers):
        chat_r = client.post("/api/chat", json={"message": "test", "conversation_id": None}, headers=admin_headers)
        msg_id = chat_r.json()["message_id"]

        r = client.post("/api/feedback", json={"message_id": msg_id, "useful": True}, headers=admin_headers)
        assert r.status_code == 200

    def test_feedback_nonexistent_message(self, client, admin_headers):
        r = client.post("/api/feedback", json={"message_id": 999, "useful": False}, headers=admin_headers)
        assert r.status_code == 404

    def test_feedback_with_comment(self, client, admin_headers):
        chat_r = client.post("/api/chat", json={"message": "test", "conversation_id": None}, headers=admin_headers)
        msg_id = chat_r.json()["message_id"]

        r = client.post(
            "/api/feedback",
            json={"message_id": msg_id, "useful": False, "comment": "回答不准"},
            headers=admin_headers,
        )
        assert r.status_code == 200


class TestDeleteConversation:
    def test_delete_own_conversation(self, client, admin_headers):
        chat_r = client.post("/api/chat", json={"message": "测试删除会话", "conversation_id": None}, headers=admin_headers)
        conv_id = chat_r.json()["conversation_id"]

        r = client.delete(f"/api/conversations/{conv_id}", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

        list_r = client.get("/api/conversations", headers=admin_headers)
        assert all(c["conversation_id"] != conv_id for c in list_r.json())

    def test_delete_nonexistent(self, client, admin_headers):
        r = client.delete("/api/conversations/999", headers=admin_headers)
        assert r.status_code == 404

    def test_delete_others_conversation(self, client, admin_headers, newbie_headers):
        chat_r = client.post("/api/chat", json={"message": "admin的会话", "conversation_id": None}, headers=admin_headers)
        conv_id = chat_r.json()["conversation_id"]

        r = client.delete(f"/api/conversations/{conv_id}", headers=newbie_headers)
        assert r.status_code == 404
