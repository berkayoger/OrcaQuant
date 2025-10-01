"""Unit tests targeting lightweight JWT helpers."""

from __future__ import annotations

import pytest
from flask import Flask
import jwt

from tests.fixtures.adapter import get_jwt_api

pytestmark = [pytest.mark.unit]


def _make_app() -> Flask:
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    app.config.setdefault("SECRET_KEY", "test-secret-key")
    return app


def test_token_manager_is_available():
    api = get_jwt_api()
    assert hasattr(api.token_manager, "generate_tokens")


def test_generate_tokens_produces_access_and_refresh():
    api = get_jwt_api()
    app = _make_app()
    with app.app_context():
        tokens = api.token_manager.generate_tokens(user_id=1, additional_claims={"username": "demo"})
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["access_token"] != tokens["refresh_token"]
    assert tokens["access_expires"] < tokens["refresh_expires"]


def test_generate_tokens_include_custom_claims():
    api = get_jwt_api()
    app = _make_app()
    with app.app_context():
        tokens = api.token_manager.generate_tokens(user_id=7, additional_claims={"username": "tester"})
        access_token = tokens["access_token"]

    payload = jwt.decode(
        access_token,
        app.config["JWT_SECRET_KEY"],
        algorithms=["HS256"],
        audience="orcaquant-users",
        issuer="orcaquant-app",
    )
    assert payload["username"] == "tester"
    assert payload["user_id"] == 7
