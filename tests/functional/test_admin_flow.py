"""Functional smoke tests for admin-related endpoints."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.functional, pytest.mark.admin]


def test_admin_users_list(app, client):
    if not any(str(rule.rule).startswith("/api/admin/users") for rule in app.url_map.iter_rules()):
        pytest.skip("Admin users ucu bulunamadı.")

    response = client.get("/api/admin/users")
    assert response.status_code in (200, 401, 403)
