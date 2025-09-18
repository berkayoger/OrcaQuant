from time import time

import requests
from flask import Blueprint, jsonify, request
from pydantic import BaseModel, PositiveInt, ValidationError

bp = Blueprint("product_v2_market", __name__)
_CACHE: dict[str, tuple[float, list]] = {}


class TopQuery(BaseModel):
    limit: PositiveInt = 10


@bp.get("/top")
def top():
    try:
        q = TopQuery(**request.args)
    except ValidationError as e:
        return jsonify(error="validation_error", details=e.errors()), 400
    key, ttl, now = f"top::{q.limit}", 30, time()
    if key in _CACHE and now - _CACHE[key][0] < ttl:
        return jsonify(source="cache", data=_CACHE[key][1])
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": q.limit,
                "page": 1,
                "sparkline": "false",
            },
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        _CACHE[key] = (now, data)
        return jsonify(source="live", data=data)
    except requests.RequestException:
        return jsonify(error="upstream_unavailable"), 502
