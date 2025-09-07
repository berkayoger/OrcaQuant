import os
import pytest
import requests

pytestmark = pytest.mark.integration

BASE_URL = os.getenv("INTEGRATION_BASE_URL")  # ör: http://127.0.0.1:8000

@pytest.mark.skipif(not BASE_URL, reason="INTEGRATION_BASE_URL sağlanmadı")
def test_healthz_returns_ok():
    """
    Canlı backend servisinden /healthz beklenen yanıta döner mi?
    CI'da docker-compose.ci ile ayağa kaldırılan servise vurur.
    """
    r = requests.get(f"{BASE_URL.rstrip('/')}/healthz", timeout=10)
    assert r.status_code in (200, 204)

