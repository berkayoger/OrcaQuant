"""Lightweight sanity checks for ``backend.core.services``."""

from __future__ import annotations

import pytest
from requests import Session

from tests.fixtures.adapter import get_services_api

pytestmark = [pytest.mark.unit]


def test_services_module_importable():
    api = get_services_api()
    assert api.module is not None
    assert api.fns


def test_http_client_session_is_singleton():
    api = get_services_api()
    http_client = getattr(api.module, "HTTPClient", None)
    if http_client is None:
        pytest.skip("HTTPClient sınıfı bulunamadı.")
    first = http_client.session()
    second = http_client.session()
    assert isinstance(first, Session)
    assert first is second
