"""End-to-end style flow covering registration, login, prediction, and logout."""

from __future__ import annotations

import pytest

from tests.fixtures.fake_data import login_payload, prediction_payload, user_payload

pytestmark = [pytest.mark.functional, pytest.mark.e2e]


def _missing_routes(app, paths):
    return [path for path in paths if not any(str(rule.rule).startswith(path) for rule in app.url_map.iter_rules())]


def test_user_register_login_predict_logout(app, client):
    required = ["/api/auth/register", "/api/auth/login", "/api/predict", "/api/auth/logout"]
    missing = _missing_routes(app, required)
    if missing:
        pytest.skip(f"Flow için eksik uçlar: {missing}")

    response = client.post("/api/auth/register", json=user_payload(2))
    assert response.status_code in (200, 201, 409)

    response = client.post("/api/auth/login", json=login_payload(2))
    assert response.status_code in (200, 201)
    token = (response.get_json() or {}).get("access_token")
    assert token

    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/predict", json=prediction_payload("ETHUSDT"), headers=headers)
    assert response.status_code in (200, 202)

    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code in (200, 204)
