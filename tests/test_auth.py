"""认证接口测试"""
from app.services.auth_service import create_user


class TestLogin:
    def test_login_success(self, client):
        r = client.post("/api/auth/login", json={"username": "testadmin", "password": "admin123"})
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert data["role"] == "admin"
        assert data["username"] == "testadmin"

    def test_login_wrong_password(self, client):
        r = client.post("/api/auth/login", json={"username": "testadmin", "password": "wrong"})
        assert r.status_code == 401

    def test_login_nonexistent_user(self, client):
        r = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
        assert r.status_code == 401

    def test_login_empty_fields(self, client):
        r = client.post("/api/auth/login", json={"username": "", "password": ""})
        assert r.status_code in (401, 422)


class TestMe:
    def test_me_with_token(self, client, admin_headers):
        r = client.get("/api/auth/me", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "testadmin"
        assert data["role"] == "admin"

    def test_me_without_token(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code in (401, 403, 422)

    def test_me_with_invalid_token(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
        assert r.status_code == 401
