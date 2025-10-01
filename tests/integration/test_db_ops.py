"""Integration tests for database operations using SQLAlchemy."""

from __future__ import annotations

import pytest
from flask import Flask

from tests.fixtures.adapter import get_models_api

pytestmark = [pytest.mark.integration, pytest.mark.db]


def _make_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app


def test_transaction_commit_rollback():
    api = get_models_api()
    model = api.models.get("User") or next(iter(api.models.values()), None)
    if model is None:
        pytest.skip("Veritabanı modeli bulunamadı.")

    app = _make_app()
    api.db.init_app(app)
    with app.app_context():
        api.db.drop_all()
        api.db.create_all()

        try:
            instance = model(
                username="txn-user",
                email="txn@example.com",
                password_hash="hashed",
                api_key="api-key-2",
            ) if hasattr(model, "username") else model()
        except Exception as exc:  # pragma: no cover - model specific requirements
            pytest.skip(f"Model örneği oluşturulamadı: {exc}")

        api.db.session.add(instance)
        api.db.session.commit()

        api.db.session.delete(instance)
        api.db.session.rollback()

        remaining = api.db.session.query(model).first()
        assert remaining is not None
