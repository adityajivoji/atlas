import asyncio

import services
import utils.initialize as init_module


class DummyInitSettings:
    SUPER_USER_ID = "00000000-0000-0000-0000-000000000001"
    SUPER_USER_NAME = "SUPER"
    SUPER_USER_USER_NAME = "super"
    SUPER_USER_PASSWORD = "Strong@123"
    SUPER_USER_EMAIL = "super@example.com"


def test_seed_db_skips_creation_when_super_user_exists(monkeypatch):
    called = {"create": 0}

    async def fake_get_one_by_filter(filters):
        return {"id": DummyInitSettings.SUPER_USER_ID}

    async def fake_create_user_with_id(**kwargs):
        called["create"] += 1

    monkeypatch.setattr(init_module, "InitSettings", DummyInitSettings)
    monkeypatch.setattr(services.UserService, "get_one_by_filter", fake_get_one_by_filter)
    monkeypatch.setattr(services.UserService, "create_user_with_id", fake_create_user_with_id)

    asyncio.run(init_module.InitUtils.seed_db())

    assert called["create"] == 0


def test_seed_db_creates_super_user_when_missing(monkeypatch):
    created = {}

    async def fake_get_one_by_filter(filters):
        return None

    async def fake_create_user_with_id(**kwargs):
        created.update(kwargs)

    monkeypatch.setattr(init_module, "InitSettings", DummyInitSettings)
    monkeypatch.setattr(services.UserService, "get_one_by_filter", fake_get_one_by_filter)
    monkeypatch.setattr(services.UserService, "create_user_with_id", fake_create_user_with_id)

    asyncio.run(init_module.InitUtils.seed_db())

    assert created["id"] == DummyInitSettings.SUPER_USER_ID
    assert created["user_name"] == DummyInitSettings.SUPER_USER_USER_NAME
    assert created["email"] == DummyInitSettings.SUPER_USER_EMAIL
    assert created["meta"] == {"role": "admin"}
