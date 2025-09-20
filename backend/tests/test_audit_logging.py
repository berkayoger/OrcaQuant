from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask, g, jsonify, request

from backend.db.models import AuditLog
from backend.utils.audit import bind_auto_audit, log_action


@pytest.fixture
def audit_app():
    from backend.db import db as audit_db
    import backend.db.models  # noqa: F401 - ensure models registered
    import backend.models.plan  # noqa: F401 - ensure plan table exists

    app = Flask("audit-tests")
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    audit_db.init_app(app)

    @app.before_request
    def _inject_user():
        if not getattr(g, "user", None):
            g.user = SimpleNamespace(
                id=7,
                email="auto@example.com",
                username="auto-admin",
                is_admin=True,
            )

    bind_auto_audit(app)

    with app.app_context():
        audit_db.drop_all()
        audit_db.create_all()

    try:
        yield app
    finally:
        with app.app_context():
            audit_db.session.remove()
            audit_db.drop_all()


@pytest.fixture
def audit_client(audit_app):
    with audit_app.test_client() as client:
        yield client


def test_log_action_persists_record(audit_app, audit_client):
    @audit_app.route("/manual-log", methods=["POST"], endpoint="manual_audit_test")
    def _manual_audit_route():
        user = SimpleNamespace(id=42, email="manual@example.com", username="manual")
        log_action(user=user, action="manual_test_action", details="manual detail message")
        return jsonify({"ok": True})

    response = audit_client.post(
        "/manual-log",
        json={"trigger": True},
        environ_overrides={"REMOTE_ADDR": "203.0.113.5"},
    )
    assert response.status_code == 200

    with audit_app.app_context():
        entry = AuditLog.query.filter_by(action="manual_test_action").one()
        assert entry.username == "manual@example.com"
        assert entry.details == "manual detail message"
        assert entry.ip_address == "203.0.113.5"


def test_auto_admin_audit_records_mutations(audit_app, audit_client):
    @audit_app.route(
        "/api/admin/__audit_auto",
        methods=["POST"],
        endpoint="audit_auto_test_endpoint",
    )
    def _audit_target():
        payload = request.get_json(silent=True) or {}
        return jsonify({"ok": True, "payload": payload})

    with audit_app.app_context():
        initial = AuditLog.query.count()

    response = audit_client.post(
        "/api/admin/__audit_auto",
        json={"flag": "value", "token": "should-hide"},
    )

    assert response.status_code == 200

    with audit_app.app_context():
        records = AuditLog.query.order_by(AuditLog.id.asc()).all()
        assert len(records) == initial + 1
        entry = records[-1]

    assert entry.action.startswith("admin_auto:POST")
    assert entry.username in {"auto-admin", "auto@example.com"}
    assert entry.details is not None
    assert '"path": "/api/admin/__audit_auto"' in entry.details
    # Sensitive fields should be redacted
    assert "should-hide" not in entry.details
