from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from ..indicators_utils import ema, macd, rsi, sma
from ..schemas import PricesModel

bp = Blueprint("product_v2_indicators", __name__)


@bp.post("/basic")
def basic():
    try:
        payload = PricesModel(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify(error="validation_error", details=e.errors()), 400
    out = {
        "sma20": sma(payload.prices, 20),
        "sma50": sma(payload.prices, 50),
        "ema12": ema(payload.prices, 12),
        "ema26": ema(payload.prices, 26),
        "rsi14": rsi(payload.prices, 14),
    }
    m = macd(payload.prices)
    if m:
        out["macd"] = {"value": m[0], "signal": m[1]}
    return jsonify(out)
