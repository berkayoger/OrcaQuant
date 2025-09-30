"""Utility helpers for Redis-backed caching of Flask responses."""
from __future__ import annotations

import functools
import hashlib
import json
import os
from typing import Any, Callable, Optional

import redis
from flask import Response, current_app, make_response, request


_redis_client: Optional[redis.Redis] = None


def _get_client() -> redis.Redis:
    """Return a cached Redis client instance."""
    global _redis_client  # pylint: disable=global-statement
    if _redis_client is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(url, decode_responses=False)
    return _redis_client


def _build_cache_key() -> str:
    payload = {
        "path": request.path,
        "query": request.query_string.decode("utf-8"),
        "method": request.method,
    }
    cache_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8"))
    return f"cache:{cache_hash.hexdigest()}"


def cache_response(ttl_seconds: int = 30) -> Callable[[Callable[..., Any]], Callable[..., Response]]:
    """Cache JSON GET responses for ``ttl_seconds``.

    Only ``GET`` requests are cached; other HTTP methods pass through. Responses are
    cached when they are JSON (``mimetype == 'application/json'``) and have a 200 status.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Response]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Response:
            if request.method.upper() != "GET":
                return make_response(func(*args, **kwargs))

            key = _build_cache_key()
            client = _get_client()
            cached_payload = client.get(key)
            if cached_payload is not None:
                return Response(cached_payload, mimetype="application/json")

            response = make_response(func(*args, **kwargs))
            if response.status_code == 200 and response.mimetype == "application/json":
                try:
                    client.setex(key, ttl_seconds, response.get_data())
                except Exception as exc:  # pragma: no cover - best effort logging
                    current_app.logger.warning("Failed to store cache entry: %s", exc)
            return response

        return wrapper

    return decorator
