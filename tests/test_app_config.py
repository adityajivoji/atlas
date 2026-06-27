import importlib

from fastapi.testclient import TestClient

import utils
from settings import AppSettings


def test_app_settings_parse_csv_env_values(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://a.example, https://b.example")
    monkeypatch.setenv("ALLOWED_HOSTS", "api.example.com, localhost")

    settings = AppSettings()

    assert settings.CORS_ALLOWED_ORIGINS == ["https://a.example", "https://b.example"]
    assert settings.ALLOWED_HOSTS == ["api.example.com", "localhost"]


def test_main_app_allows_configured_cors_origin(monkeypatch):
    async def fake_seed_db():
        return None

    monkeypatch.setattr(utils.InitUtils, "seed_db", fake_seed_db)

    import main as main_module

    importlib.reload(main_module)

    with TestClient(main_module.app) as client:
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_main_app_rejects_unconfigured_cors_origin(monkeypatch):
    async def fake_seed_db():
        return None

    monkeypatch.setattr(utils.InitUtils, "seed_db", fake_seed_db)

    import main as main_module

    importlib.reload(main_module)

    with TestClient(main_module.app) as client:
        response = client.options(
            "/",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_main_app_rejects_disallowed_host(monkeypatch):
    async def fake_seed_db():
        return None

    monkeypatch.setattr(utils.InitUtils, "seed_db", fake_seed_db)

    import main as main_module

    importlib.reload(main_module)

    with TestClient(main_module.app) as client:
        response = client.get("/", headers={"Host": "evil.example"})

    assert response.status_code == 400
    assert response.text == "Invalid host header"
