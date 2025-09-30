"""Market data API endpoints backed by CoinGecko."""
from __future__ import annotations

import os

from flask import Blueprint, jsonify, request
from flask.typing import ResponseReturnValue

from backend.services.cache import cache_response
from backend.services.coingecko import get_simple_price

bp = Blueprint("market_api", __name__)


def _cache_ttl() -> int:
    try:
        return int(os.getenv("COINGECKO_CACHE_TTL", "30"))
    except ValueError:
        return 30


@bp.get("/api/market/price")
@cache_response(ttl_seconds=_cache_ttl())
def price() -> ResponseReturnValue:
    """Return a cached price snapshot for a symbol."""
    symbol = request.args.get("symbol", "bitcoin")
    vs_currency = request.args.get("vs", "usd")
    payload = get_simple_price(symbol, vs_currency)
    status = 200 if "error" not in payload else 429
    return jsonify(payload), status
