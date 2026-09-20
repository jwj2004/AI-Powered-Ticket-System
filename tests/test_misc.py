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

    def test_admin_can_mark_others_notification(self, client, admin_headers, ops_headers, db_session):
        gap = KnowledgeGap(question="别人的问题", user_id=2, status="pending")
        db_session.add(gap)
        db_session.commit()
        client.post(f"/api/gaps/{gap.id}/resolve", json={"answer": "答案"}, headers=admin_headers)

        ops_notifs = client.get("/api/notifications", headers=ops_headers).json()
        assert ops_notifs["total"] >= 1
        notif_id = ops_notifs["items"][0]["notification_id"]

        r = client.post(f"/api/notifications/{notif_id}/read", headers=admin_headers)
        assert r.status_code == 200

    def test_non_admin_cannot_mark_others_notification(self, client, admin_headers, newbie_headers, db_session):
        gap = KnowledgeGap(question="admin的问题", user_id=1, status="pending")
        db_session.add(gap)
        db_session.commit()
        client.post(f"/api/gaps/{gap.id}/resolve", json={"answer": "答案"}, headers=admin_headers)

        admin_notifs = client.get("/api/notifications", headers=admin_headers).json()
        notif_id = admin_notifs["items"][0]["notification_id"]

        r = client.post(f"/api/notifications/{notif_id}/read", headers=newbie_headers)
        assert r.status_code == 404


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


class TestFAQCandidates:
    def test_faq_candidates_empty(self, client, admin_headers):
        r = client.get("/api/dashboard/faq-candidates", headers=admin_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_faq_candidates_after_chat(self, client, admin_headers):
        for _ in range(3):
            client.post("/api/chat", json={"message": "支付回调超时", "conversation_id": None}, headers=admin_headers)
        client.post("/api/chat", json={"message": "其他问题", "conversation_id": None}, headers=admin_headers)

        r = client.get("/api/dashboard/faq-candidates", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        assert data[0]["question"] == "支付回调超时"
        assert data[0]["count"] >= 3

    def test_faq_candidates_excludes_existing_faq(self, client, admin_headers, db_session):
        from app.models.faq import FAQ
        db_session.add(FAQ(question="支付回调超时", answer="联系支付服务商", gap_id=None))
        db_session.commit()

        for _ in range(3):
            client.post("/api/chat", json={"message": "支付回调超时", "conversation_id": None}, headers=admin_headers)

        r = client.get("/api/dashboard/faq-candidates", headers=admin_headers)
        assert r.status_code == 200
        questions = [item["question"] for item in r.json()]
        assert "支付回调超时" not in questions

    def test_faq_candidates_non_admin(self, client, newbie_headers):
        r = client.get("/api/dashboard/faq-candidates", headers=newbie_headers)
        assert r.status_code == 403


class TestDocSpaceCRUD:
    def test_create_space(self, client, admin_headers):
        r = client.post("/api/doc-spaces", json={"name": "新空间", "description": "测试"}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_create_duplicate_space(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        db_session.add(DocSpace(name="重复空间"))
        db_session.commit()
        r = client.post("/api/doc-spaces", json={"name": "重复空间"}, headers=admin_headers)
        assert r.status_code == 400

    def test_update_space(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        space = DocSpace(name="更新前")
        db_session.add(space)
        db_session.commit()
        r = client.put(f"/api/doc-spaces/{space.id}", json={"name": "更新后"}, headers=admin_headers)
        assert r.status_code == 200

    def test_delete_space(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        space = DocSpace(name="删除空间")
        db_session.add(space)
        db_session.commit()
        space_id = space.id
        r = client.delete(f"/api/doc-spaces/{space_id}", headers=admin_headers)
        assert r.status_code == 200

    def test_delete_nonexistent_space(self, client, admin_headers):
        r = client.delete("/api/doc-spaces/999", headers=admin_headers)
        assert r.status_code == 404

    def test_create_space_non_admin(self, client, newbie_headers):
        r = client.post("/api/doc-spaces", json={"name": "test"}, headers=newbie_headers)
        assert r.status_code == 403


class TestOperationLogs:
    def test_list_logs_empty(self, client, admin_headers):
        r = client.get("/api/logs", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_list_logs_non_admin(self, client, newbie_headers):
        r = client.get("/api/logs", headers=newbie_headers)
        assert r.status_code == 403

    def test_list_logs_with_data(self, client, admin_headers, db_session):
        from app.models.operation_log import OperationLog
        db_session.add(OperationLog(user_id=1, username="testadmin", action="login", resource="auth"))
        db_session.commit()
        r = client.get("/api/logs", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        assert r.json()["items"][0]["action"] == "login"

    def test_list_logs_pagination(self, client, admin_headers, db_session):
        from app.models.operation_log import OperationLog
        for i in range(25):
            db_session.add(OperationLog(user_id=1, username="testadmin", action=f"action_{i}"))
        db_session.commit()
        r = client.get("/api/logs?page=2&size=10", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 10


class TestDocumentApproval:
    def test_upload_default_not_approved(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        import io
        db_session.add(DocSpace(name="审批测试空间"))
        db_session.commit()
        files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
        data = {"space_id": "1"}
        r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        assert r.status_code == 200
        doc_id = r.json()["id"]
        doc_r = client.get(f"/api/documents/{doc_id}", headers=admin_headers)
        assert doc_r.json()["approved"] is False

    def test_approve_document(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        import io
        db_session.add(DocSpace(name="审批空间2"))
        db_session.commit()
        files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
        data = {"space_id": "1"}
        upload_r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        doc_id = upload_r.json()["id"]
        r = client.post(f"/api/documents/{doc_id}/approve", headers=admin_headers)
        assert r.status_code == 200
        doc_r = client.get(f"/api/documents/{doc_id}", headers=admin_headers)
        assert doc_r.json()["approved"] is True

    def test_reject_document(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        import io
        db_session.add(DocSpace(name="审批空间3"))
        db_session.commit()
        files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
        data = {"space_id": "1"}
        upload_r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        doc_id = upload_r.json()["id"]
        client.post(f"/api/documents/{doc_id}/approve", headers=admin_headers)
        r = client.post(f"/api/documents/{doc_id}/reject", headers=admin_headers)
        assert r.status_code == 200
        doc_r = client.get(f"/api/documents/{doc_id}", headers=admin_headers)
        assert doc_r.status_code == 404

    def test_approve_non_admin(self, client, newbie_headers, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        import io
        db_session.add(DocSpace(name="审批空间4"))
        db_session.commit()
        files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
        data = {"space_id": "1"}
        upload_r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        doc_id = upload_r.json()["id"]
        r = client.post(f"/api/documents/{doc_id}/approve", headers=newbie_headers)
        assert r.status_code == 403

    def test_approve_nonexistent(self, client, admin_headers):
        r = client.post("/api/documents/999/approve", headers=admin_headers)
        assert r.status_code == 404


class TestDocumentViewCount:
    def test_view_count_increments(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        from app.models.document import Document
        db_session.add(DocSpace(name="浏览测试空间"))
        db_session.commit()
        doc = Document(space_id=1, title="view_test.txt", content="content", content_type="txt", version=1, owner_id=1)
        db_session.add(doc)
        db_session.commit()
        client.get(f"/api/documents/{doc.id}", headers=admin_headers)
        client.get(f"/api/documents/{doc.id}", headers=admin_headers)
        r = client.get(f"/api/documents/{doc.id}", headers=admin_headers)
        assert r.json()["view_count"] >= 3

    def test_view_count_in_list(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        from app.models.document import Document
        db_session.add(DocSpace(name="列表浏览空间"))
        db_session.commit()
        doc = Document(space_id=1, title="list_view.txt", content="content", content_type="txt", version=1, owner_id=1, view_count=5)
        db_session.add(doc)
        db_session.commit()
        r = client.get("/api/documents", headers=admin_headers)
        items = [d for d in r.json() if d["title"] == "list_view.txt"]
        assert items[0]["view_count"] == 5


class TestGapMerge:
    def test_merge_gaps(self, client, admin_headers, db_session):
        g1 = KnowledgeGap(question="问题A", user_id=1, status="pending", question_count=3)
        g2 = KnowledgeGap(question="问题B", user_id=1, status="pending", question_count=2)
        db_session.add_all([g1, g2])
        db_session.commit()
        r = client.post(f"/api/gaps/{g1.id}/merge", json={"target_gap_id": g2.id}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        assert r.json()["merged_into"] == g2.id

    def test_merge_self(self, client, admin_headers, db_session):
        gap = KnowledgeGap(question="问题C", user_id=1, status="pending")
        db_session.add(gap)
        db_session.commit()
        r = client.post(f"/api/gaps/{gap.id}/merge", json={"target_gap_id": gap.id}, headers=admin_headers)
        assert r.status_code == 400

    def test_merge_nonexistent(self, client, admin_headers, db_session):
        gap = KnowledgeGap(question="问题D", user_id=1, status="pending")
        db_session.add(gap)
        db_session.commit()
        r = client.post(f"/api/gaps/{gap.id}/merge", json={"target_gap_id": 999}, headers=admin_headers)
        assert r.status_code == 404

    def test_merge_non_admin(self, client, newbie_headers, db_session):
        g1 = KnowledgeGap(question="问题E", user_id=1, status="pending")
        g2 = KnowledgeGap(question="问题F", user_id=1, status="pending")
        db_session.add_all([g1, g2])
        db_session.commit()
        r = client.post(f"/api/gaps/{g1.id}/merge", json={"target_gap_id": g2.id}, headers=newbie_headers)
        assert r.status_code == 403


class TestRoleIsolation:
    def test_admin_sees_all_spaces(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        db_session.add_all([
            DocSpace(name="全员空间", role="all"),
            DocSpace(name="运维空间", role="ops"),
            DocSpace(name="新手空间", role="newbie"),
            DocSpace(name="管理空间", role="admin"),
        ])
        db_session.commit()
        r = client.get("/api/doc-spaces", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) == 4

    def test_ops_sees_all_and_ops(self, client, ops_headers, db_session):
        from app.models.doc_space import DocSpace
        db_session.add_all([
            DocSpace(name="全员空间2", role="all"),
            DocSpace(name="运维空间2", role="ops"),
            DocSpace(name="新手空间2", role="newbie"),
            DocSpace(name="管理空间2", role="admin"),
        ])
        db_session.commit()
        r = client.get("/api/doc-spaces", headers=ops_headers)
        assert r.status_code == 200
        names = [s["name"] for s in r.json()]
        assert "全员空间2" in names
        assert "运维空间2" in names
        assert "新手空间2" not in names
        assert "管理空间2" not in names

    def test_newbie_sees_all_and_newbie(self, client, newbie_headers, db_session):
        from app.models.doc_space import DocSpace
        db_session.add_all([
            DocSpace(name="全员空间3", role="all"),
            DocSpace(name="运维空间3", role="ops"),
            DocSpace(name="新手空间3", role="newbie"),
            DocSpace(name="管理空间3", role="admin"),
        ])
        db_session.commit()
        r = client.get("/api/doc-spaces", headers=newbie_headers)
        assert r.status_code == 200
        names = [s["name"] for s in r.json()]
        assert "全员空间3" in names
        assert "新手空间3" in names
        assert "运维空间3" not in names
        assert "管理空间3" not in names

    def test_ops_cannot_access_newbie_doc(self, client, ops_headers, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        from app.models.document import Document
        space = DocSpace(name="新手专属", role="newbie")
        db_session.add(space)
        db_session.commit()
        doc = Document(space_id=space.id, title="新手文档", content="content", content_type="txt", version=1, owner_id=1)
        db_session.add(doc)
        db_session.commit()
        r = client.get(f"/api/documents/{doc.id}", headers=ops_headers)
        assert r.status_code == 403

    def test_admin_can_access_any_doc(self, client, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        from app.models.document import Document
        space = DocSpace(name="管理专属", role="admin")
        db_session.add(space)
        db_session.commit()
        doc = Document(space_id=space.id, title="管理文档", content="content", content_type="txt", version=1, owner_id=1)
        db_session.add(doc)
        db_session.commit()
        r = client.get(f"/api/documents/{doc.id}", headers=admin_headers)
        assert r.status_code == 200

    def test_newbie_cannot_access_ops_doc(self, client, newbie_headers, admin_headers, db_session):
        from app.models.doc_space import DocSpace
        from app.models.document import Document
        space = DocSpace(name="运维专属", role="ops")
        db_session.add(space)
        db_session.commit()
        doc = Document(space_id=space.id, title="运维文档", content="content", content_type="txt", version=1, owner_id=1)
        db_session.add(doc)
        db_session.commit()
        r = client.get(f"/api/documents/{doc.id}", headers=newbie_headers)
        assert r.status_code == 403

    def test_create_space_with_role(self, client, admin_headers, db_session):
        r = client.post("/api/doc-spaces", json={"name": "测试角色空间", "role": "ops"}, headers=admin_headers)
        assert r.status_code == 200
        spaces = client.get("/api/doc-spaces", headers=admin_headers).json()
        created = [s for s in spaces if s["name"] == "测试角色空间"][0]
        assert created["role"] == "ops"


class TestDocCitations:
    def test_doc_citations_empty(self, client, admin_headers):
        r = client.get("/api/stats/doc-citations", headers=admin_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_doc_citations_after_chat(self, client, admin_headers, db_session):
        import json as json_mod
        from app.models.conversation import Conversation
        from app.models.message import Message
        conv = Conversation(user_id=1, title="引用测试")
        db_session.add(conv)
        db_session.commit()
        citations_json = json_mod.dumps([{"document_id": 1, "title": "doc1", "chunk_index": 0}])
        msg = Message(conversation_id=conv.id, role="assistant", content="reply", citations_json=citations_json, confidence="high")
        db_session.add(msg)
        db_session.commit()

        r = client.get("/api/stats/doc-citations", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1
        assert r.json()[0]["document_id"] == 1
        assert r.json()[0]["citations"] >= 1

    def test_doc_citations_top5(self, client, admin_headers, db_session):
        import json as json_mod
        from app.models.conversation import Conversation
        from app.models.message import Message
        conv = Conversation(user_id=1, title="Top5测试")
        db_session.add(conv)
        db_session.commit()
        for doc_id in [1, 1, 1, 2, 2, 3, 4, 5, 6]:
            citations_json = json_mod.dumps([{"document_id": doc_id, "title": f"doc{doc_id}", "chunk_index": 0}])
            msg = Message(conversation_id=conv.id, role="assistant", content="reply", citations_json=citations_json, confidence="high")
            db_session.add(msg)
        db_session.commit()

        r = client.get("/api/stats/doc-citations", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) <= 5
        assert data[0]["document_id"] == 1
        assert data[0]["citations"] == 3

    def test_doc_citations_non_admin(self, client, newbie_headers):
        r = client.get("/api/stats/doc-citations", headers=newbie_headers)
        assert r.status_code == 403
