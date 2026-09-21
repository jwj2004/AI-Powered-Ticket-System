"""认证与用户管理接口测试"""
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

    def test_login_pending_user(self, client):
        client.post("/api/auth/register", json={"username": "pendinguser", "password": "123456", "role": "ops"})
        r = client.post("/api/auth/login", json={"username": "pendinguser", "password": "123456"})
        assert r.status_code == 403
        assert "待审核" in r.json()["detail"]

    def test_login_rejected_user(self, client, admin_headers):
        client.post("/api/auth/register", json={"username": "rejecteduser", "password": "123456", "role": "ops"})
        pending = client.get("/api/users/pending", headers=admin_headers)
        uid = [u for u in pending.json() if u["username"] == "rejecteduser"][0]["id"]
        client.post(f"/api/users/{uid}/reject", headers=admin_headers)
        r = client.post("/api/auth/login", json={"username": "rejecteduser", "password": "123456"})
        assert r.status_code == 403
        assert "拒绝" in r.json()["detail"]

    def test_login_disabled_user(self, client, admin_headers):
        client.post("/api/users/2/disable", headers=admin_headers)
        r = client.post("/api/auth/login", json={"username": "testops", "password": "ops123"})
        assert r.status_code == 403
        assert "禁用" in r.json()["detail"]


class TestRegister:
    def test_register_success(self, client):
        r = client.post("/api/auth/register", json={"username": "newuser", "password": "123456", "role": "ops"})
        assert r.status_code == 200
        assert r.json()["ok"] is True
        assert "审核" in r.json()["msg"]

    def test_register_duplicate(self, client):
        r = client.post("/api/auth/register", json={"username": "testadmin", "password": "123456"})
        assert r.status_code == 400

    def test_register_default_role(self, client):
        r = client.post("/api/auth/register", json={"username": "defrole", "password": "123456"})
        assert r.status_code == 200

    def test_register_pending_cannot_login(self, client):
        client.post("/api/auth/register", json={"username": "pending2", "password": "123456"})
        r = client.post("/api/auth/login", json={"username": "pending2", "password": "123456"})
        assert r.status_code == 403


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


class TestUserManagement:
    def test_pending_list(self, client, admin_headers):
        client.post("/api/auth/register", json={"username": "pend1", "password": "123456", "role": "ops"})
        r = client.get("/api/users/pending", headers=admin_headers)
        assert r.status_code == 200
        assert any(u["username"] == "pend1" for u in r.json())

    def test_pending_list_non_admin(self, client, newbie_headers):
        r = client.get("/api/users/pending", headers=newbie_headers)
        assert r.status_code == 403

    def test_approve_user(self, client, admin_headers):
        client.post("/api/auth/register", json={"username": "approve1", "password": "123456", "role": "ops"})
        pending = client.get("/api/users/pending", headers=admin_headers)
        uid = [u for u in pending.json() if u["username"] == "approve1"][0]["id"]
        r = client.post(f"/api/users/{uid}/approve", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        login_r = client.post("/api/auth/login", json={"username": "approve1", "password": "123456"})
        assert login_r.status_code == 200

    def test_reject_user(self, client, admin_headers):
        client.post("/api/auth/register", json={"username": "reject1", "password": "123456", "role": "ops"})
        pending = client.get("/api/users/pending", headers=admin_headers)
        uid = [u for u in pending.json() if u["username"] == "reject1"][0]["id"]
        r = client.post(f"/api/users/{uid}/reject", headers=admin_headers)
        assert r.status_code == 200
        login_r = client.post("/api/auth/login", json={"username": "reject1", "password": "123456"})
        assert login_r.status_code == 403

    def test_make_admin(self, client, admin_headers):
        r = client.post("/api/users/3/make-admin", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_make_admin_self(self, client, admin_headers):
        r = client.post("/api/users/1/make-admin", headers=admin_headers)
        assert r.status_code == 400
        assert "自己" in r.json()["detail"]

    def test_approve_nonexistent(self, client, admin_headers):
        r = client.post("/api/users/999/approve", headers=admin_headers)
        assert r.status_code == 404

    def test_reject_nonexistent(self, client, admin_headers):
        r = client.post("/api/users/999/reject", headers=admin_headers)
        assert r.status_code == 404

    def test_make_admin_nonexistent(self, client, admin_headers):
        r = client.post("/api/users/999/make-admin", headers=admin_headers)
        assert r.status_code == 404

    def test_approve_already_active(self, client, admin_headers):
        r = client.post("/api/users/2/approve", headers=admin_headers)
        assert r.status_code == 400


class TestChangePassword:
    def test_change_password_success(self, client, admin_headers):
        r = client.post("/api/auth/change-password", json={"old_password": "admin123", "new_password": "newpass456"}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        login_r = client.post("/api/auth/login", json={"username": "testadmin", "password": "newpass456"})
        assert login_r.status_code == 200

    def test_change_password_wrong_old(self, client, admin_headers):
        r = client.post("/api/auth/change-password", json={"old_password": "wrong", "new_password": "newpass456"}, headers=admin_headers)
        assert r.status_code == 400
        assert "原密码" in r.json()["detail"]

    def test_change_password_too_short(self, client, admin_headers):
        r = client.post("/api/auth/change-password", json={"old_password": "admin123", "new_password": "123"}, headers=admin_headers)
        assert r.status_code == 400

    def test_change_password_no_token(self, client):
        r = client.post("/api/auth/change-password", json={"old_password": "x", "new_password": "123456"})
        assert r.status_code in (401, 403, 422)


class TestDisableUser:
    def test_disable_user(self, client, admin_headers):
        r = client.post("/api/users/2/disable", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        login_r = client.post("/api/auth/login", json={"username": "testops", "password": "ops123"})
        assert login_r.status_code == 403
        assert "禁用" in login_r.json()["detail"]

    def test_disable_self(self, client, admin_headers):
        r = client.post("/api/users/1/disable", headers=admin_headers)
        assert r.status_code == 400
        assert "自己" in r.json()["detail"]

    def test_disable_nonexistent(self, client, admin_headers):
        r = client.post("/api/users/999/disable", headers=admin_headers)
        assert r.status_code == 404

    def test_disable_already_disabled(self, client, admin_headers):
        client.post("/api/users/2/disable", headers=admin_headers)
        r = client.post("/api/users/2/disable", headers=admin_headers)
        assert r.status_code == 400

    def test_disable_non_admin(self, client, newbie_headers):
        r = client.post("/api/users/2/disable", headers=newbie_headers)
        assert r.status_code == 403

    def test_disable_pending_should_fail(self, client, admin_headers):
        client.post("/api/auth/register", json={"username": "pend_disable", "password": "123456", "role": "ops"})
        pending = client.get("/api/users/pending", headers=admin_headers)
        uid = [u for u in pending.json() if u["username"] == "pend_disable"][0]["id"]
        r = client.post(f"/api/users/{uid}/disable", headers=admin_headers)
        assert r.status_code == 400
        assert "待审核" in r.json()["detail"]


class TestEnableUser:
    def test_enable_disabled_user(self, client, admin_headers):
        client.post("/api/users/2/disable", headers=admin_headers)
        r = client.post("/api/users/2/enable", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        login_r = client.post("/api/auth/login", json={"username": "testops", "password": "ops123"})
        assert login_r.status_code == 200

    def test_enable_rejected_user(self, client, admin_headers):
        client.post("/api/auth/register", json={"username": "reject_enable", "password": "123456", "role": "ops"})
        pending = client.get("/api/users/pending", headers=admin_headers)
        uid = [u for u in pending.json() if u["username"] == "reject_enable"][0]["id"]
        client.post(f"/api/users/{uid}/reject", headers=admin_headers)
        r = client.post(f"/api/users/{uid}/enable", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        login_r = client.post("/api/auth/login", json={"username": "reject_enable", "password": "123456"})
        assert login_r.status_code == 200

    def test_enable_already_active(self, client, admin_headers):
        r = client.post("/api/users/2/enable", headers=admin_headers)
        assert r.status_code == 400

    def test_enable_nonexistent(self, client, admin_headers):
        r = client.post("/api/users/999/enable", headers=admin_headers)
        assert r.status_code == 404

    def test_enable_non_admin(self, client, newbie_headers):
        r = client.post("/api/users/2/enable", headers=newbie_headers)
        assert r.status_code == 403


class TestListUsers:
    def test_list_all_users(self, client, admin_headers):
        r = client.get("/api/users", headers=admin_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 3

    def test_list_active_users_by_status(self, client, admin_headers):
        r = client.get("/api/users?status=active", headers=admin_headers)
        assert r.status_code == 200
        for u in r.json():
            assert u["status"] == "active"

    def test_list_pending_users_by_status(self, client, admin_headers):
        client.post("/api/auth/register", json={"username": "status_pend", "password": "123456"})
        r = client.get("/api/users?status=pending", headers=admin_headers)
        assert r.status_code == 200
        names = [u["username"] for u in r.json()]
        assert "status_pend" in names
        for u in r.json():
            assert u["status"] == "pending"

    def test_list_disabled_users_by_status(self, client, admin_headers):
        client.post("/api/users/2/disable", headers=admin_headers)
        r = client.get("/api/users?status=disabled", headers=admin_headers)
        assert r.status_code == 200
        names = [u["username"] for u in r.json()]
        assert "testops" in names
        for u in r.json():
            assert u["status"] == "disabled"

    def test_list_rejected_users_by_status(self, client, admin_headers):
        client.post("/api/auth/register", json={"username": "status_reject", "password": "123456", "role": "ops"})
        pending = client.get("/api/users/pending", headers=admin_headers)
        uid = [u for u in pending.json() if u["username"] == "status_reject"][0]["id"]
        client.post(f"/api/users/{uid}/reject", headers=admin_headers)
        r = client.get("/api/users?status=rejected", headers=admin_headers)
        assert r.status_code == 200
        names = [u["username"] for u in r.json()]
        assert "status_reject" in names
        for u in r.json():
            assert u["status"] == "rejected"

    def test_list_users_invalid_status(self, client, admin_headers):
        r = client.get("/api/users?status=invalid", headers=admin_headers)
        assert r.status_code == 400

    def test_list_users_non_admin(self, client, newbie_headers):
        r = client.get("/api/users", headers=newbie_headers)
        assert r.status_code == 403


class TestUpdateRole:
    def test_change_role_to_ops(self, client, admin_headers):
        r = client.patch("/api/users/3", json={"role": "ops"}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_change_role_to_newbie(self, client, admin_headers):
        r = client.patch("/api/users/2", json={"role": "newbie"}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_change_role_self(self, client, admin_headers):
        r = client.patch("/api/users/1", json={"role": "ops"}, headers=admin_headers)
        assert r.status_code == 400
        assert "自己" in r.json()["detail"]

    def test_change_role_invalid(self, client, admin_headers):
        r = client.patch("/api/users/2", json={"role": "superadmin"}, headers=admin_headers)
        assert r.status_code == 400

    def test_change_role_nonexistent(self, client, admin_headers):
        r = client.patch("/api/users/999", json={"role": "ops"}, headers=admin_headers)
        assert r.status_code == 404

    def test_change_role_non_admin(self, client, newbie_headers):
        r = client.patch("/api/users/2", json={"role": "ops"}, headers=newbie_headers)
        assert r.status_code == 403
