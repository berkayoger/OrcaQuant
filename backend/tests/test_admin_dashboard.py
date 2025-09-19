"""Tests for the admin dashboard API surface."""

from __future__ import annotations

from datetime import datetime

import pytest

from backend.app import create_app
from backend.db import db
from backend.db.models import SubscriptionPlan, User
from backend.models.plan import Plan


@pytest.fixture()
def dashboard_app(monkeypatch):
    """Provide a clean app context with seeded data for each test."""

    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("FLASK_ENV", "testing")
    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        db.drop_all()
        db.create_all()

        basic = Plan(name="Basic", price=9.99, features="{}")
        premium = Plan(name="Premium", price=19.99, features="{}")
        db.session.add_all([basic, premium])
        db.session.flush()

        user = User(
            username="alice",
            email="alice@example.com",
            password_hash="test",
            api_key="test-api-key",
            subscription_level=SubscriptionPlan.BASIC,
            plan=basic,
            created_at=datetime.utcnow(),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


def test_list_users_returns_paginated_payload(dashboard_app):
    client = dashboard_app.test_client()

    response = client.get("/api/admin/dashboard/users")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] == 1
    assert payload["items"][0]["email"] == "alice@example.com"

    etag = response.headers.get("ETag")
    cached = client.get(
        "/api/admin/dashboard/users",
        headers={"If-None-Match": etag},
    )
    assert cached.status_code == 304


def test_patch_user_plan_updates_plan_and_logs_audit(dashboard_app):
    client = dashboard_app.test_client()

    csrf_resp = client.get("/api/csrf")
    csrf_token = csrf_resp.headers.get("X-CSRF-Token")
    assert csrf_token

    update_resp = client.patch(
        "/api/admin/dashboard/users/1/plan",
        json={"plan": "premium"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert update_resp.status_code == 200
    assert update_resp.get_json()["user"]["plan"].lower() == "premium"

    with dashboard_app.app_context():
        user = User.query.get(1)
        assert user.subscription_level == SubscriptionPlan.PREMIUM

    audit_resp = client.get("/api/admin/dashboard/audit-logs")
    assert audit_resp.status_code == 200
    log_items = audit_resp.get_json()["items"]
    assert log_items
    assert log_items[0]["action"] == "admin_user_plan_update"


def test_validation_errors_return_400(dashboard_app):
    client = dashboard_app.test_client()
    response = client.get(
        "/api/admin/dashboard/users",
        query_string={"page": 0},
    )
    assert response.status_code == 400

    csrf_resp = client.get("/api/csrf")
    csrf_token = csrf_resp.headers.get("X-CSRF-Token")

    bad_patch = client.patch(
        "/api/admin/dashboard/users/1/plan",
        json={"plan": ""},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert bad_patch.status_code == 400
