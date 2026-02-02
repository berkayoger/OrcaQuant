import json

import pytest
from flask import g, jsonify

from backend import create_app, db
from backend.db.models import User, UserRole
from backend.utils.rbac import require_roles


@pytest.fixture
def rbac_app(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def normal_user(rbac_app):
    with rbac_app.app_context():
        user = User(username="basic", email="b@example.com", role=UserRole.USER)
        user.set_password("passpasspass1!")
        user.generate_api_key()
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(rbac_app):
    with rbac_app.app_context():
        admin = User(username="admin", email="a@example.com", role=UserRole.ADMIN)
        admin.set_password("passpasspass1!")
        admin.generate_api_key()
        db.session.add(admin)
        db.session.commit()
        return admin


def test_require_roles_blocks_basic(rbac_app, normal_user):
    app = rbac_app

    @app.route("/secured")
    @require_roles()
    def secured():
        return jsonify({"ok": True})

    with app.test_client() as client:
        with app.app_context():
            g.user = db.session.merge(normal_user)
            resp = client.get("/secured")
            assert resp.status_code == 403
            body = json.loads(resp.data.decode())
            assert "error" in body


def test_require_roles_allows_admin(rbac_app, admin_user):
    app = rbac_app

    @app.route("/secured-admin")
    @require_roles()
    def secured_admin():
        return jsonify({"ok": True})

    with app.test_client() as client:
        with app.app_context():
            g.user = db.session.merge(admin_user)
            resp = client.get("/secured-admin")
            assert resp.status_code == 200
            body = json.loads(resp.data.decode())
            assert body["ok"] is True
