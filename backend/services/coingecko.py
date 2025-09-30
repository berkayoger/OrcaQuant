"""Thin CoinGecko API client with Redis-backed rate limiting."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import redis
import requests

COINGECKO_BASE = os.getenv("COINGECKO_BASE", "https://api.coingecko.com/api/v3")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_RPS = float(os.getenv("COINGECKO_RPS", 3))

_REDIS_CLIENT: Optional[redis.Redis] = None


def _get_client() -> redis.Redis:
    global _REDIS_CLIENT  # pylint: disable=global-statement
    if _REDIS_CLIENT is None:
        _REDIS_CLIENT = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    return _REDIS_CLIENT


def _rate_limit_ok(bucket: str) -> bool:
    if COINGECKO_RPS <= 0:
        return True

    now = int(time.time())
    key = f"cg:rl:{bucket}:{now}"
    try:
        client = _get_client()
        count = client.incr(key)
        if count == 1:
            client.expire(key, 2)
        return count <= int(COINGECKO_RPS)
    except Exception:
        # Fail-open if Redis is unavailable; request will go through but logged later.
        return True


def get_simple_price(symbol: str, vs_currency: str = "usd") -> Dict[str, Any]:
    """Fetch ``/simple/price`` for a symbol."""
    if not _rate_limit_ok("simple_price"):
        return {"error": "rate_limited", "detail": "CoinGecko RPS exceeded"}

    url = f"{COINGECKO_BASE}/simple/price"
    params = {"ids": symbol, "vs_currencies": vs_currency}
    headers = {}
    if COINGECKO_API_KEY:
        headers["x-cg-pro-api-key"] = COINGECKO_API_KEY

    response = requests.get(url, params=params, headers=headers, timeout=8)
    response.raise_for_status()
    return response.json()
