"""Unit tests for helper utilities."""

from __future__ import annotations

import pytest

from tests.fixtures.adapter import get_helpers_api

pytestmark = [pytest.mark.unit]


def test_helpers_importable():
    api = get_helpers_api()
    assert api.fns


def test_sanitize_dict_removes_control_characters():
    api = get_helpers_api()
    sanitize_dict = api.fns.get("sanitize_dict")
    if sanitize_dict is None:
        pytest.skip("sanitize_dict fonksiyonu bulunamadı.")

    dirty = {"key\n": "value\t"}
    clean = sanitize_dict(dirty)
    assert "\n" not in next(iter(clean.keys()))
    assert "\t" not in next(iter(clean.values()))
