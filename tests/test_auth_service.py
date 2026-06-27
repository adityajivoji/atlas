import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import jwt
import pytest

import database
import helpers
import repositories
import services
import utils


def _patch_session(monkeypatch):
    @asynccontextmanager
    async def fake_get_session():
        yield object()

    monkeypatch.setattr(database.Postgres, "get_session", staticmethod(fake_get_session))


def test_login_with_email_returns_access_and_refresh_tokens(monkeypatch):
    _patch_session(monkeypatch)
    utils.AuthUtils.generate_new_signing_key("service-login")

    hashed = utils.AuthUtils.hash_password("Strong@123")
    fake_user = SimpleNamespace(id=uuid4(), password=hashed, user_name="john", meta={"role": "admin"})
    created_sessions = []

    async def fake_get_one_by_filter(session, filters):
        assert filters == {"email": "john@example.com"}
        return fake_user

    async def fake_create_refresh_session(session, user_id, user_name, expires_at, session_id):
        created_sessions.append((user_id, user_name, expires_at, session_id))
        return SimpleNamespace(id=session_id)

    monkeypatch.setattr(repositories.UserRepository, "get_one_by_filter", fake_get_one_by_filter)
    monkeypatch.setattr(repositories.RefreshSessionRepository, "create_refresh_session", fake_create_refresh_session)

    result = asyncio.run(
        services.AuthService.login(
            password="Strong@123",
            email="john@example.com",
        )
    )

    assert result["token_type"] == "bearer"
    access_payload = utils.AuthUtils.verify_token(result["access_token"], expected_type="access")
    refresh_payload = utils.AuthUtils.verify_token(result["refresh_token"], expected_type="refresh")
    assert access_payload["sub"] == "john"
    assert access_payload["roles"] == ["admin"]
    assert refresh_payload["sub"] == "john"
    assert UUID(refresh_payload["jti"])
    assert len(created_sessions) == 1
    assert created_sessions[0][0] == fake_user.id


def test_login_raises_when_user_missing(monkeypatch):
    _patch_session(monkeypatch)

    async def fake_get_one_by_filter(session, filters):
        return None

    monkeypatch.setattr(repositories.UserRepository, "get_one_by_filter", fake_get_one_by_filter)

    with pytest.raises(helpers.Error, match="Invalid credentials"):
        asyncio.run(services.AuthService.login(password="Strong@123", user_name="john"))


def test_login_raises_on_invalid_password(monkeypatch):
    _patch_session(monkeypatch)

    hashed = utils.AuthUtils.hash_password("Different@123")
    fake_user = SimpleNamespace(password=hashed, user_name="john")

    async def fake_get_one_by_filter(session, filters):
        return fake_user

    monkeypatch.setattr(repositories.UserRepository, "get_one_by_filter", fake_get_one_by_filter)

    with pytest.raises(helpers.Error, match="Invalid credentials"):
        asyncio.run(services.AuthService.login(password="Strong@123", user_name="john"))


def test_refresh_returns_new_pair(monkeypatch):
    _patch_session(monkeypatch)
    utils.AuthUtils.generate_new_signing_key("service-refresh")
    existing_session_id = uuid4()
    refresh_token = utils.AuthUtils.issue_token(
        subject="john",
        token_type="refresh",
        expires_delta=timedelta(minutes=5),
        extra_claims={"jti": str(existing_session_id)},
    )

    fake_user = SimpleNamespace(
        id=uuid4(),
        password="hashed",
        user_name="john",
        deactivated=False,
        status=helpers.STATUS.ACTIVE,
        meta={"roles": ["user"]},
    )
    created_session_ids = []
    revoked_calls = []

    async def fake_get_one_by_filter(session, filters):
        assert filters == {"user_name": "john"}
        return fake_user

    async def fake_get_refresh_session(session, session_id):
        assert session_id == existing_session_id
        return SimpleNamespace(
            id=session_id,
            revoked=False,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            user_name="john",
        )

    async def fake_create_refresh_session(session, user_id, user_name, expires_at, session_id):
        created_session_ids.append(session_id)
        return SimpleNamespace(id=session_id)

    async def fake_revoke_refresh_session(session, session_id, revoked_reason, replaced_by_session_id=None):
        revoked_calls.append((session_id, revoked_reason, replaced_by_session_id))
        return SimpleNamespace(id=session_id)

    monkeypatch.setattr(repositories.UserRepository, "get_one_by_filter", fake_get_one_by_filter)
    monkeypatch.setattr(repositories.RefreshSessionRepository, "get_refresh_session", fake_get_refresh_session)
    monkeypatch.setattr(repositories.RefreshSessionRepository, "create_refresh_session", fake_create_refresh_session)
    monkeypatch.setattr(repositories.RefreshSessionRepository, "revoke_refresh_session", fake_revoke_refresh_session)

    result = asyncio.run(services.AuthService.refresh(refresh_token=refresh_token))

    assert result["token_type"] == "bearer"
    payload = utils.AuthUtils.verify_token(result["access_token"], expected_type="access")
    refresh_payload = utils.AuthUtils.verify_token(result["refresh_token"], expected_type="refresh")
    assert payload["sub"] == "john"
    assert payload["roles"] == ["user"]
    assert created_session_ids
    assert UUID(refresh_payload["jti"]) == created_session_ids[0]
    assert revoked_calls == [(existing_session_id, "rotated", created_session_ids[0])]


def test_refresh_rejects_access_token(monkeypatch):
    _patch_session(monkeypatch)
    utils.AuthUtils.generate_new_signing_key("service-refresh-type")
    access_token = utils.AuthUtils.issue_token(
        subject="john",
        token_type="access",
        expires_delta=timedelta(minutes=5),
    )

    with pytest.raises(helpers.Error, match="Invalid token type"):
        asyncio.run(services.AuthService.refresh(refresh_token=access_token))


def test_refresh_requires_subject(monkeypatch):
    utils.AuthUtils.generate_new_signing_key("service-refresh-sub")
    key_record = utils.AuthUtils.get_latest_key_record()

    token = jwt.encode(
        payload={
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        key=key_record["private_key"],
        algorithm=utils.AuthUtils.auth_settings.JWT_ALGORITHM,
        headers={"kid": key_record["kid"]},
    )

    with pytest.raises(helpers.Error, match="missing subject"):
        asyncio.run(services.AuthService.refresh(refresh_token=token))


def test_refresh_rejects_missing_user(monkeypatch):
    _patch_session(monkeypatch)
    utils.AuthUtils.generate_new_signing_key("service-refresh-missing-user")
    existing_session_id = uuid4()
    refresh_token = utils.AuthUtils.issue_token(
        subject="john",
        token_type="refresh",
        expires_delta=timedelta(minutes=5),
        extra_claims={"jti": str(existing_session_id)},
    )

    async def fake_get_one_by_filter(session, filters):
        return None

    async def fake_get_refresh_session(session, session_id):
        return SimpleNamespace(
            id=session_id,
            revoked=False,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            user_name="john",
        )

    monkeypatch.setattr(repositories.UserRepository, "get_one_by_filter", fake_get_one_by_filter)
    monkeypatch.setattr(repositories.RefreshSessionRepository, "get_refresh_session", fake_get_refresh_session)

    with pytest.raises(helpers.Error, match="no longer valid"):
        asyncio.run(services.AuthService.refresh(refresh_token=refresh_token))


def test_refresh_rejects_deactivated_user(monkeypatch):
    _patch_session(monkeypatch)
    utils.AuthUtils.generate_new_signing_key("service-refresh-deactivated")
    existing_session_id = uuid4()
    refresh_token = utils.AuthUtils.issue_token(
        subject="john",
        token_type="refresh",
        expires_delta=timedelta(minutes=5),
        extra_claims={"jti": str(existing_session_id)},
    )

    fake_user = SimpleNamespace(
        id=uuid4(),
        password="hashed",
        user_name="john",
        deactivated=True,
        status=helpers.STATUS.ACTIVE,
    )

    async def fake_get_one_by_filter(session, filters):
        return fake_user

    async def fake_get_refresh_session(session, session_id):
        return SimpleNamespace(
            id=session_id,
            revoked=False,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            user_name="john",
        )

    monkeypatch.setattr(repositories.UserRepository, "get_one_by_filter", fake_get_one_by_filter)
    monkeypatch.setattr(repositories.RefreshSessionRepository, "get_refresh_session", fake_get_refresh_session)

    with pytest.raises(helpers.Error, match="no longer valid"):
        asyncio.run(services.AuthService.refresh(refresh_token=refresh_token))


def test_refresh_rejects_missing_jti(monkeypatch):
    _patch_session(monkeypatch)
    utils.AuthUtils.generate_new_signing_key("service-refresh-no-jti")
    refresh_token = utils.AuthUtils.issue_token(
        subject="john",
        token_type="refresh",
        expires_delta=timedelta(minutes=5),
    )

    with pytest.raises(helpers.Error, match="no longer valid"):
        asyncio.run(services.AuthService.refresh(refresh_token=refresh_token))


def test_refresh_rejects_revoked_session(monkeypatch):
    _patch_session(monkeypatch)
    utils.AuthUtils.generate_new_signing_key("service-refresh-revoked")
    existing_session_id = uuid4()
    refresh_token = utils.AuthUtils.issue_token(
        subject="john",
        token_type="refresh",
        expires_delta=timedelta(minutes=5),
        extra_claims={"jti": str(existing_session_id)},
    )

    async def fake_get_refresh_session(session, session_id):
        return SimpleNamespace(
            id=session_id,
            revoked=True,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            user_name="john",
        )

    monkeypatch.setattr(repositories.RefreshSessionRepository, "get_refresh_session", fake_get_refresh_session)

    with pytest.raises(helpers.Error, match="no longer valid"):
        asyncio.run(services.AuthService.refresh(refresh_token=refresh_token))


def test_logout_revokes_current_refresh_session(monkeypatch):
    _patch_session(monkeypatch)
    utils.AuthUtils.generate_new_signing_key("service-logout")
    current_session_id = uuid4()
    refresh_token = utils.AuthUtils.issue_token(
        subject="john",
        token_type="refresh",
        expires_delta=timedelta(minutes=5),
        extra_claims={"jti": str(current_session_id)},
    )
    revoked_calls = []

    async def fake_revoke_refresh_session(session, session_id, revoked_reason, replaced_by_session_id=None):
        revoked_calls.append((session_id, revoked_reason, replaced_by_session_id))
        return SimpleNamespace(id=session_id)

    monkeypatch.setattr(repositories.RefreshSessionRepository, "revoke_refresh_session", fake_revoke_refresh_session)

    asyncio.run(services.AuthService.logout(refresh_token=refresh_token, access_subject="john"))

    assert revoked_calls == [(current_session_id, "user_logout", None)]


def test_logout_rejects_subject_mismatch(monkeypatch):
    _patch_session(monkeypatch)
    utils.AuthUtils.generate_new_signing_key("service-logout-mismatch")
    refresh_token = utils.AuthUtils.issue_token(
        subject="john",
        token_type="refresh",
        expires_delta=timedelta(minutes=5),
        extra_claims={"jti": str(uuid4())},
    )

    with pytest.raises(helpers.Error, match="does not belong"):
        asyncio.run(services.AuthService.logout(refresh_token=refresh_token, access_subject="jane"))


def test_logout_all_revokes_all_refresh_sessions_for_authenticated_user(monkeypatch):
    _patch_session(monkeypatch)
    fake_user = SimpleNamespace(id=uuid4(), user_name="john")

    async def fake_get_one_by_filter(session, filters):
        assert filters == {"user_name": "john"}
        return fake_user

    async def fake_revoke_all_refresh_sessions_for_user(session, user_id, revoked_reason, exclude_session_id=None):
        assert user_id == fake_user.id
        assert revoked_reason == "user_logout_all"
        assert exclude_session_id is None
        return 3

    monkeypatch.setattr(repositories.UserRepository, "get_one_by_filter", fake_get_one_by_filter)
    monkeypatch.setattr(
        repositories.RefreshSessionRepository,
        "revoke_all_refresh_sessions_for_user",
        fake_revoke_all_refresh_sessions_for_user,
    )

    revoked_count = asyncio.run(services.AuthService.logout_all(access_subject="john"))

    assert revoked_count == 3
