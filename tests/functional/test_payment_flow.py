"""Functional payment flow smoke tests."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.functional, pytest.mark.payment]


def test_payment_flow_smoke(app, client):
    if not any(str(rule.rule).startswith("/api/pay") for rule in app.url_map.iter_rules()):
        pytest.skip("Ödeme uçları tanımlı değil.")

    response = client.post("/api/pay/checkout", json={"plan": "pro"})
    assert response.status_code in (200, 201, 202)
