import os
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("POSTGRES_DB_URL", "postgresql+asyncpg://atlas:atlas_dev_password@localhost:5432/atlas")
os.environ.setdefault("POSTGRES_MIGRATION_URL", "postgresql+psycopg2://atlas:atlas_dev_password@localhost:5432/atlas")
os.environ.setdefault("JWT_ALGORITHM", "RS256")
os.environ.setdefault("ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")

import routers
import services
import utils


@pytest.fixture(autouse=True)
def configure_auth_settings(monkeypatch):
    test_root = Path(tempfile.gettempdir()) / "atlas-auth-tests"
    test_root.mkdir(parents=True, exist_ok=True)
    base_dir = test_root / f"case-{uuid4().hex}"
    base_dir.mkdir(parents=True, exist_ok=False)
    keys_dir = base_dir / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)

    settings = utils.AuthUtils.auth_settings
    monkeypatch.setattr(settings, "KEYS_DIR", str(keys_dir), raising=False)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "RS256", raising=False)
    monkeypatch.setattr(settings, "ACCESS_TOKEN_TTL_MINUTES", 15, raising=False)
    monkeypatch.setattr(settings, "REFRESH_TOKEN_TTL_DAYS", 30, raising=False)

    async def _noop_async(*args, **kwargs):
        return None

    monkeypatch.setattr(services.GovernanceService, "record_login_attempt", _noop_async)
    monkeypatch.setattr(services.GovernanceService, "record_audit_log", _noop_async)

    yield

    shutil.rmtree(base_dir, ignore_errors=True)


@pytest.fixture()
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(routers.root_route)
    return application


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class DummyHelper:
    def __init__(self, payload: dict):
        self._payload = payload

    def to_dict(self) -> dict:
        return self._payload


@pytest.fixture()
def dummy_helper() -> DummyHelper:
    return DummyHelper({"id": "11111111-1111-1111-1111-111111111111", "user_name": "john"})
