"""Integration checks for Redis-like operations."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.redis]


def test_redis_basic_set_get(redis_client):
    key, value = "k1", "v1"
    assert redis_client.set(key, value)
    assert redis_client.get(key).decode() == value
