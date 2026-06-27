import services
import utils


def test_root_health_check(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_auth_route_online_check(client):
    response = client.get("/auth/")
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Auth route working"


def test_get_jwks_exposes_multiple_keys(client):
    first = utils.AuthUtils.generate_signing_key("kid-one")
    second = utils.AuthUtils.generate_signing_key("kid-two")
    utils.AuthUtils.activate_signing_key(first["kid"])
    utils.AuthUtils.activate_signing_key(second["kid"])

    response = client.get("/auth/jwks")
    body = response.json()

    assert response.status_code == 200
    kids = {item["kid"] for item in body["keys"]}
    assert first["kid"] not in kids
    assert second["kid"] in kids


def test_rotate_key_generates_new_key(client):
    utils.AuthUtils.generate_new_signing_key("rotate-admin-key")
    admin_token = utils.AuthUtils.issue_token_pair("SUPER_USER", access_claims={"roles": ["admin"], "role": "admin"})["access_token"]

    response = client.post(
        "/auth/keys/rotate",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    body = response.json()

    assert response.status_code == 201
    assert body["message"] == "New signing key generated"
    assert body["data"]["kid"]


def test_generate_activate_and_revoke_key_endpoints(client):
    utils.AuthUtils.generate_new_signing_key("lifecycle-admin-key")
    admin_token = utils.AuthUtils.issue_token_pair("SUPER_USER", access_claims={"roles": ["admin"], "role": "admin"})["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    generate_response = client.post("/auth/keys/generate", json={"kid": "generated-only"}, headers=headers)
    activate_response = client.post("/auth/keys/activate", json={"kid": "generated-only"}, headers=headers)
    refreshed_headers = {
        "Authorization": (
            f"Bearer {utils.AuthUtils.issue_token_pair('SUPER_USER', access_claims={'roles': ['admin'], 'role': 'admin'})['access_token']}"
        )
    }
    revoke_response = client.post("/auth/keys/revoke", json={"kid": "generated-only"}, headers=refreshed_headers)

    assert generate_response.status_code == 201
    assert generate_response.json()["data"]["status"] == "generated"
    assert activate_response.status_code == 200
    assert activate_response.json()["data"]["status"] == "active"
    assert revoke_response.status_code == 200
    assert revoke_response.json()["data"]["status"] == "revoked"


def test_login_success_returns_token_pair(client, monkeypatch):
    async def fake_login(password, user_name=None, email=None):
        return {
            "access_token": "access.jwt",
            "refresh_token": "refresh.jwt",
            "token_type": "bearer",
        }

    monkeypatch.setattr(services.AuthService, "login", fake_login)

    response = client.post(
        "/auth/login",
        json={"email": "john@example.com", "password": "Strong@123"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Login Successful"
    assert body["data"]["token_type"] == "bearer"


def test_login_error_returns_error_payload(client, monkeypatch):
    async def fake_login(password, user_name=None, email=None):
        raise Exception("login exploded")

    monkeypatch.setattr(services.AuthService, "login", fake_login)

    response = client.post(
        "/auth/login",
        json={"email": "john@example.com", "password": "Strong@123"},
    )
    body = response.json()

    assert response.status_code == 500
    assert body["error"] == "Internal Server Error"


def test_refresh_success_returns_new_pair(client, monkeypatch):
    async def fake_refresh(refresh_token):
        return {
            "access_token": "new-access.jwt",
            "refresh_token": "new-refresh.jwt",
            "token_type": "bearer",
        }

    monkeypatch.setattr(services.AuthService, "refresh", fake_refresh)

    response = client.post("/auth/refresh", json={"refresh_token": "x.y.z"})
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Token refreshed"
    assert body["data"]["access_token"] == "new-access.jwt"


def test_refresh_error_returns_error_payload(client, monkeypatch):
    async def fake_refresh(refresh_token):
        raise Exception("refresh exploded")

    monkeypatch.setattr(services.AuthService, "refresh", fake_refresh)

    response = client.post("/auth/refresh", json={"refresh_token": "x.y.z"})
    body = response.json()

    assert response.status_code == 500
    assert body["error"] == "Internal Server Error"


def test_logout_success_revokes_current_refresh_session(client, monkeypatch):
    utils.AuthUtils.generate_new_signing_key("logout-route-key")
    access_token = utils.AuthUtils.issue_token_pair(
        "john",
        access_claims={"roles": ["user"], "role": "user"},
    )["access_token"]

    captured = {}

    async def fake_logout(refresh_token, access_subject):
        captured["refresh_token"] = refresh_token
        captured["access_subject"] = access_subject

    monkeypatch.setattr(services.AuthService, "logout", fake_logout)

    response = client.post(
        "/auth/logout",
        json={"refresh_token": "refresh.jwt"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Logout successful"
    assert captured == {"refresh_token": "refresh.jwt", "access_subject": "john"}


def test_logout_all_success_revokes_all_user_sessions(client, monkeypatch):
    utils.AuthUtils.generate_new_signing_key("logout-all-route-key")
    access_token = utils.AuthUtils.issue_token_pair(
        "john",
        access_claims={"roles": ["user"], "role": "user"},
    )["access_token"]

    async def fake_logout_all(access_subject):
        assert access_subject == "john"
        return 2

    monkeypatch.setattr(services.AuthService, "logout_all", fake_logout_all)

    response = client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Logout from all sessions successful"
    assert body["data"]["revoked_sessions"] == 2


def test_signup_success_returns_serialized_user(client, monkeypatch, dummy_helper):
    async def fake_create_user(**kwargs):
        return dummy_helper

    monkeypatch.setattr(services.UserService, "create_user", fake_create_user)

    payload = {
        "name": "John Doe",
        "user_name": "john_doe",
        "email": "john@example.com",
        "password": "Strong@123",
        "meta": {},
    }
    response = client.post("/auth/signup", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Signup Successful"
    assert body["data"]["user_name"] == "john"


def test_signup_error_returns_error_payload(client, monkeypatch):
    async def fake_create_user(**kwargs):
        raise Exception("signup exploded")

    monkeypatch.setattr(services.UserService, "create_user", fake_create_user)

    payload = {
        "name": "John Doe",
        "user_name": "john_doe",
        "email": "john@example.com",
        "password": "Strong@123",
        "meta": {},
    }
    response = client.post("/auth/signup", json=payload)
    body = response.json()

    assert response.status_code == 500
    assert body["error"] == "Internal Server Error"
