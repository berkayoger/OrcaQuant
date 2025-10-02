"""Integration-level smoke tests for HTTP endpoints."""

from __future__ import annotations

import pytest

from tests.fixtures.fake_data import login_payload, prediction_payload, user_payload

pytestmark = [pytest.mark.integration, pytest.mark.api]


def _has_endpoint(app, rule_prefix: str) -> bool:
    return any(str(rule.rule).startswith(rule_prefix) for rule in app.url_map.iter_rules())


def test_auth_endpoints(app, client):
    required = ["/api/auth/register", "/api/auth/login", "/api/auth/logout"]
    missing = [endpoint for endpoint in required if not _has_endpoint(app, endpoint)]
    if missing:
        pytest.skip(f"Eksik auth uçları: {missing}")

    response = client.post("/api/auth/register", json=user_payload(1))
    assert response.status_code in (200, 201, 409)

    response = client.post("/api/auth/login", json=login_payload(1))
    assert response.status_code in (200, 201)
    token = (response.get_json() or {}).get("access_token")
    assert token


def test_api_prediction(app, client):
    if not _has_endpoint(app, "/api/predict"):
        pytest.skip("Prediction ucu bulunamadı /api/predict")

    response = client.post("/api/predict", json=prediction_payload("BTCUSDT"))
    assert response.status_code in (200, 202)
    assert response.get_json() is not None


def test_admin_panel_endpoints(app, client):
    if not _has_endpoint(app, "/api/admin"):
        pytest.skip("Admin panel API kökü yok /api/admin")

    response = client.get("/api/admin/users")
    assert response.status_code in (200, 401, 403)
