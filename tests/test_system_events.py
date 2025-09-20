import os
import sys
import types
from datetime import datetime, timedelta

from flask import request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if "cachetools" not in sys.modules:  # pragma: no cover - test shim for optional dependency
    cachetools_stub = types.ModuleType("cachetools")

    class _TTLCache(dict):  # minimal stub for tests
        def __init__(self, maxsize=1024, ttl=60):
            super().__init__()
            self.maxsize = maxsize
            self.ttl = ttl

    cachetools_stub.TTLCache = _TTLCache
    sys.modules["cachetools"] = cachetools_stub

if "flask_caching" not in sys.modules:  # pragma: no cover - optional dependency shim
    flask_caching_stub = types.ModuleType("flask_caching")

    class _Cache:  # minimal cache stub for tests
        def __init__(self, app=None, config=None):
            self.app = app
            self.config = config or {}
            self.cache = types.SimpleNamespace(_write_client=None)
            if app is not None:
                self.init_app(app, config=config)

        def init_app(self, app, config=None):
            self.app = app
            if config:
                self.config.update(config)

        def get(self, _key):
            return None

        def set(self, _key, _value, timeout=None):
            return None

    flask_caching_stub.Cache = _Cache
    sys.modules["flask_caching"] = flask_caching_stub

from backend import create_app, db
from backend.db.models import SystemEvent
from backend.utils.system_events import log_event


def setup_app(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    app = create_app()
    return app


def test_log_and_list_events(monkeypatch):
    monkeypatch.setattr(
        "flask_jwt_extended.jwt_required", lambda *a, **k: (lambda f: f)
    )
    monkeypatch.setattr(
        "backend.auth.middlewares.admin_required", lambda: (lambda f: f)
    )
    app = setup_app(monkeypatch)
    client = app.test_client()

    with app.app_context():
        log_event("test", "INFO", "hello", {"a": 1})

    resp = client.get("/api/admin/events")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data and data[0]["message"] == "hello"


def test_retention_cleanup(monkeypatch):
    monkeypatch.setattr(
        "flask_jwt_extended.jwt_required", lambda *a, **k: (lambda f: f)
    )
    monkeypatch.setattr(
        "backend.auth.middlewares.admin_required", lambda: (lambda f: f)
    )
    app = setup_app(monkeypatch)
    client = app.test_client()

    with app.app_context():
        old_evt = SystemEvent(
            event_type="old",
            level="INFO",
            message="old",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        db.session.add(old_evt)
        db.session.commit()

    resp = client.post("/api/admin/events/retention-cleanup", json={"days": 5})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["deleted"] == 1


def test_system_status(monkeypatch):
    monkeypatch.setattr(
        "flask_jwt_extended.jwt_required", lambda *a, **k: (lambda f: f)
    )
    monkeypatch.setattr(
        "backend.auth.middlewares.admin_required", lambda: (lambda f: f)
    )
    app = setup_app(monkeypatch)
    client = app.test_client()

    resp = client.get("/api/admin/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "database" in data


def test_stream_events_supports_eventsource_tokens(monkeypatch):
    monkeypatch.setattr(
        "flask_jwt_extended.jwt_required", lambda *a, **k: (lambda f: f)
    )

    calls = {"admin": 0, "verify_sources": []}

    def fake_admin_required():
        def decorator(fn):
            def wrapper(*args, **kwargs):
                calls["admin"] += 1
                return fn(*args, **kwargs)

            return wrapper

        return decorator

    monkeypatch.setattr("backend.auth.middlewares.admin_required", fake_admin_required)

    app = setup_app(monkeypatch)
    client = app.test_client()

    # Ensure the blueprint uses the testing double for admin checks.
    monkeypatch.setattr(
        "backend.api.admin.system_events.admin_required", fake_admin_required
    )

    def fake_verify_jwt_in_request(*, locations):
        assert locations == ["headers", "query_string", "cookies"]
        token = None
        source = None
        if "headers" in locations:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                source = "headers"
        if token is None and "query_string" in locations:
            token = request.args.get("access_token") or request.args.get("jwt")
            if token:
                source = "query_string"
        if token is None and "cookies" in locations:
            token = (
                request.cookies.get("access_token")
                or request.cookies.get("accessToken")
                or request.cookies.get("jwt")
            )
            if token:
                source = "cookies"
        if not token:
            raise AssertionError("Token missing from allowed locations")
        calls["verify_sources"].append(source)
        return token

    monkeypatch.setattr(
        "backend.api.admin.system_events.verify_jwt_in_request",
        fake_verify_jwt_in_request,
    )

    with app.app_context():
        log_event("stream", "INFO", "hello-stream", {"sample": True})

    resp = client.get("/api/admin/events/stream?access_token=querytoken")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/event-stream")
    assert "hello-stream" in resp.data.decode()
    assert calls["verify_sources"][0] == "query_string"
    assert calls["admin"] == 1

    client.set_cookie("access_token", "cookietoken")
    resp_cookie = client.get("/api/admin/events/stream")
    assert resp_cookie.status_code == 200
    assert "hello-stream" in resp_cookie.data.decode()
    assert calls["verify_sources"][1] == "cookies"
    assert calls["admin"] == 2
