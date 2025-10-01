"""Unit-level smoke tests for SQLAlchemy models."""

from __future__ import annotations

import pytest
from flask import Flask

from tests.fixtures.adapter import get_models_api

pytestmark = [pytest.mark.unit, pytest.mark.db]


def _make_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app


def test_models_metadata_tables_create():
    api = get_models_api()
    app = _make_app()
    api.db.init_app(app)
    with app.app_context():
        api.db.drop_all()
        api.db.create_all()
        assert api.db.Model.metadata.tables


def test_user_model_insert_roundtrip():
    api = get_models_api()
    user_model = api.models.get("User")
    if user_model is None:
        pytest.skip("User modeli bulunamadı.")

    app = _make_app()
    api.db.init_app(app)
    with app.app_context():
        api.db.drop_all()
        api.db.create_all()

        user = user_model(
            username="unit-user",
            email="u1@example.com",
            password_hash="hashed",
            api_key="api-key-1",
        )
        api.db.session.add(user)
        api.db.session.commit()

        fetched = user_model.query.filter_by(username="unit-user").first()
        assert fetched is not None
        assert fetched.email == "u1@example.com"
