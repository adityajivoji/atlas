import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

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


def test_create_user_hashes_password_and_calls_repository(monkeypatch):
    _patch_session(monkeypatch)

    captured = {}

    async def fake_create_user(session, user_helper):
        captured["password"] = user_helper.password
        return user_helper

    monkeypatch.setattr(repositories.UserRepository, "create_user", fake_create_user)

    result = asyncio.run(
        services.UserService.create_user(
            name="John",
            user_name="john",
            password="Strong@123",
            email="john@example.com",
            meta={"x": 1},
        )
    )

    assert utils.AuthUtils.verify_hash(captured["password"], "Strong@123") is True
    assert result.user_name == "john"


def test_get_user_with_user_id_raises_when_missing(monkeypatch):
    _patch_session(monkeypatch)

    async def fake_get_one_by_filter(session, filters):
        return None

    monkeypatch.setattr(repositories.UserRepository, "get_one_by_filter", fake_get_one_by_filter)

    with pytest.raises(helpers.Error, match="User not found"):
        asyncio.run(services.UserService.get_user_with_user_id(str(uuid4())))


def test_update_password_raises_when_user_missing(monkeypatch):
    _patch_session(monkeypatch)

    async def fake_get_one_by_filter(session, filters):
        return None

    monkeypatch.setattr(repositories.UserRepository, "get_one_by_filter", fake_get_one_by_filter)

    with pytest.raises(helpers.Error, match="User not found"):
        asyncio.run(
            services.UserService.update_password(
                id=None,
                email="john@example.com",
                new_password="Strong@123",
                old_password="OldStrong@123",
            )
        )


def test_get_all_by_filter_returns_repository_payload(monkeypatch):
    _patch_session(monkeypatch)

    fake_user = helpers.UserHelper(
        id=uuid4(),
        name="John",
        user_name="john",
        password="hashed",
        email="john@example.com",
        status=helpers.STATUS.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deactivated=False,
        meta={},
    )

    async def fake_get_all_by_filter(session, filters):
        assert filters == {"status": "ACTIVE"}
        return [fake_user]

    monkeypatch.setattr(repositories.UserRepository, "get_all_by_filter", fake_get_all_by_filter)

    result = asyncio.run(services.UserService.get_all_by_filter(filter={"status": "ACTIVE"}))

    assert len(result) == 1
    assert result[0].email == "john@example.com"
