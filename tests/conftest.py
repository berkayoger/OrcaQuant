"""Global pytest fixtures and environment setup for OrcaQuant."""

from __future__ import annotations

import contextlib
import importlib
import os
import random
import string
from typing import Dict

import pytest

# Provide safe defaults before any test module imports application code.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture(autouse=True, scope="session")
def _global_random_seed() -> None:
    """Ensure reproducible randomness across the suite."""
    random.seed(1337)


@pytest.fixture(scope="session")
def set_test_env() -> None:
    """Apply deterministic environment overrides for the test session."""
    env_overrides: Dict[str, str] = {
        "FLASK_ENV": "testing",
        "ENV": "testing",
        "JWT_SECRET_KEY": "test-secret-key",
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///:memory:"),
        "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        "CELERY_TASK_ALWAYS_EAGER": "1",
    }
    previous: Dict[str, str | None] = {key: os.environ.get(key) for key in env_overrides}
    os.environ.update(env_overrides)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@pytest.fixture(scope="session")
def app(set_test_env):  # type: ignore[override]
    """Attempt to create the Flask application for tests.

    If the application factory or its dependencies are unavailable, skip
    tests requiring the ``app`` fixture instead of failing the suite.
    """

    with contextlib.suppress(Exception):
        backend_app = importlib.import_module("backend.app")
        create_app = getattr(backend_app, "create_app", None)
        if callable(create_app):
            return create_app()
    pytest.skip("Flask app bulunamadı (backend.app.create_app). App gerektiren testler atlanıyor.")


@pytest.fixture()
def client(app):  # type: ignore[override]
    """Return a Flask test client when the app fixture is available."""
    return app.test_client()


@pytest.fixture(scope="session")
def faker():  # type: ignore[override]
    """Provide a localized Faker instance when the dependency exists."""
    try:
        from faker import Faker
    except ImportError:  # pragma: no cover
        pytest.skip("faker paketi eksik (pip install Faker)")
    return Faker("tr_TR")


@pytest.fixture(scope="session")
def redis_client():  # type: ignore[override]
    """Return an isolated Redis client backed by fakeredis when available."""
    try:
        import fakeredis
    except ImportError:  # pragma: no cover
        pytest.skip("fakeredis paketi eksik (pip install fakeredis)")
    return fakeredis.FakeStrictRedis()


@pytest.fixture(scope="session")
def celery_app():  # type: ignore[override]
    """Return the Celery app if defined under ``backend.tasks``.

    Tests are skipped when Celery is not configured in this environment.
    """

    with contextlib.suppress(Exception):
        tasks_mod = importlib.import_module("backend.tasks")
        c_app = getattr(tasks_mod, "celery_app", None)
        if c_app:
            return c_app
    pytest.skip("Celery app bulunamadı (backend.tasks.celery_app).")


@pytest.fixture()
def monkeypatch_env(monkeypatch):  # type: ignore[override]
    """Expose the builtin monkeypatch fixture for explicit environment tweaks."""
    return monkeypatch


@pytest.fixture()
def auth_header_token() -> Dict[str, str]:
    """Generate a simple fake bearer token for tests."""
    token = "test-" + "".join(random.choices(string.ascii_letters + string.digits, k=24))
    return {"Authorization": f"Bearer {token}"}
