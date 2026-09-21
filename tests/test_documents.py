"""文档管理接口测试"""
import io

from app.models.doc_space import DocSpace


class TestDocSpaces:
    def test_list_spaces(self, client, admin_headers, db_session):
        db_session.add(DocSpace(name="测试空间"))
        db_session.commit()

        r = client.get("/api/doc-spaces", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1


class TestDocuments:
    def test_list_empty(self, client, admin_headers):
        r = client.get("/api/documents", headers=admin_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_upload_txt(self, client, admin_headers, db_session):
        db_session.add(DocSpace(name="上传测试空间"))
        db_session.commit()

        content = "测试文档内容\n第二行"
        files = {"file": ("test.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
        data = {"space_id": "1"}
        r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        assert r.status_code == 200
        assert "id" in r.json()

    def test_upload_unsupported_type(self, client, admin_headers):
        files = {"file": ("test.exe", io.BytesIO(b"x"), "application/octet-stream")}
        data = {"space_id": "1"}
        r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        assert r.status_code == 400

    def test_get_nonexistent(self, client, admin_headers):
        r = client.get("/api/documents/999", headers=admin_headers)
        assert r.status_code == 404

    def test_upload_and_get(self, client, admin_headers, db_session):
        db_session.add(DocSpace(name="获取测试空间"))
        db_session.commit()

        content = "支付回调超时的解决方案"
        files = {"file": ("pay.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
        data = {"space_id": "1"}
        upload_r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        doc_id = upload_r.json()["id"]

        get_r = client.get(f"/api/documents/{doc_id}", headers=admin_headers)
        assert get_r.status_code == 200
        assert get_r.json()["title"] == "pay.txt"

    def test_list_after_upload(self, client, admin_headers, db_session):
        db_session.add(DocSpace(name="列表测试空间"))
        db_session.commit()

        content = "文档内容"
        files = {"file": ("doc.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
        data = {"space_id": "1"}
        client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)

        r = client.get("/api/documents", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1


class TestDocumentVersions:
    def test_list_versions(self, client, admin_headers, db_session):
        db_session.add(DocSpace(name="版本测试空间"))
        db_session.commit()

        content = "初始内容"
        files = {"file": ("v.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
        data = {"space_id": "1"}
        upload_r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        doc_id = upload_r.json()["id"]

        r = client.get(f"/api/documents/{doc_id}/versions", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["version"] == 1

    def test_versions_after_edit(self, client, admin_headers, db_session):
        db_session.add(DocSpace(name="版本编辑空间"))
        db_session.commit()

        files = {"file": ("edit.txt", io.BytesIO(b"first"), "text/plain")}
        data = {"space_id": "1"}
        upload_r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        doc_id = upload_r.json()["id"]

        client.put(f"/api/documents/{doc_id}", headers=admin_headers, json={"content": "second"})
        client.put(f"/api/documents/{doc_id}", headers=admin_headers, json={"content": "third"})

        r = client.get(f"/api/documents/{doc_id}/versions", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_rollback(self, client, admin_headers, db_session):
        db_session.add(DocSpace(name="回滚测试空间"))
        db_session.commit()

        files = {"file": ("rb.txt", io.BytesIO(b"original"), "text/plain")}
        data = {"space_id": "1"}
        upload_r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        doc_id = upload_r.json()["id"]

        client.put(f"/api/documents/{doc_id}", headers=admin_headers, json={"content": "modified"})

        r = client.post(f"/api/documents/{doc_id}/rollback", headers=admin_headers, json={"target_version": 1})
        assert r.status_code == 200
        assert r.json()["version"] == 3

        get_r = client.get(f"/api/documents/{doc_id}", headers=admin_headers)
        assert get_r.json()["content"] == "original"

    def test_rollback_nonexistent_version(self, client, admin_headers, db_session):
        db_session.add(DocSpace(name="回滚不存在版本"))
        db_session.commit()

        files = {"file": ("rb2.txt", io.BytesIO(b"content"), "text/plain")}
        data = {"space_id": "1"}
        upload_r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        doc_id = upload_r.json()["id"]

        r = client.post(f"/api/documents/{doc_id}/rollback", headers=admin_headers, json={"target_version": 99})
        assert r.status_code == 404

    def test_rollback_non_admin(self, client, admin_headers, newbie_headers, db_session):
        db_session.add(DocSpace(name="权限测试空间"))
        db_session.commit()

        files = {"file": ("perm.txt", io.BytesIO(b"content"), "text/plain")}
        data = {"space_id": "1"}
        upload_r = client.post("/api/documents/upload", headers=admin_headers, files=files, data=data)
        doc_id = upload_r.json()["id"]

        r = client.post(f"/api/documents/{doc_id}/rollback", headers=newbie_headers, json={"target_version": 1})
        assert r.status_code == 403
