import services
import utils


def _admin_headers():
    utils.AuthUtils.generate_new_signing_key("admin-route-key")
    token = utils.AuthUtils.issue_token_pair("SUPER_USER", access_claims={"roles": ["admin"], "role": "admin"})["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_audit_logs_requires_admin_token(client):
    response = client.get("/admin/audit-logs")

    assert response.status_code == 401


def test_admin_audit_logs_success(client, monkeypatch):
    async def fake_get_audit_logs(limit=100, actor_user_name=None, action=None):
        return [{"action": "auth.login", "status": "SUCCESS"}]

    monkeypatch.setattr(services.GovernanceService, "get_audit_logs", fake_get_audit_logs)

    response = client.get("/admin/audit-logs", headers=_admin_headers())
    body = response.json()

    assert response.status_code == 200
    assert body["data"][0]["action"] == "auth.login"


def test_admin_login_history_success(client, monkeypatch):
    async def fake_get_login_history(limit=100, user_name=None, success=None):
        return [{"user_name": "john", "success": True}]

    monkeypatch.setattr(services.GovernanceService, "get_login_history", fake_get_login_history)

    response = client.get("/admin/login-history", headers=_admin_headers())
    body = response.json()

    assert response.status_code == 200
    assert body["data"][0]["success"] is True


def test_admin_routes_reject_non_admin_token(client):
    utils.AuthUtils.generate_new_signing_key("non-admin-route-key")
    token = utils.AuthUtils.issue_token_pair("john", access_claims={"roles": ["user"], "role": "user"})["access_token"]

    response = client.get("/admin/audit-logs", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
