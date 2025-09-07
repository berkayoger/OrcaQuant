from __future__ import annotations
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError
from .service import predict as ml_predict, warmup
from .train import train as ml_train
from .metrics import record_prediction, aggregate
from .abtest import pick_model_variant

ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")

class PredictSchema(Schema):
    symbol = fields.Str(required=True)
    user_id = fields.Str(required=False)
    realized = fields.Float(required=False, allow_none=True)

@ml_bp.route("/predict", methods=["POST"])
def predict():
    try:
        data = PredictSchema().load(request.get_json() or {})
    except ValidationError as ve:
        return jsonify({"error": ve.messages}), 400
    symbol = data["symbol"]
    user_id = data.get("user_id")
    variant = pick_model_variant(user_id)
    out = ml_predict(symbol=symbol, user_id=user_id)
    if "variant" not in out:
        out["variant"] = variant
    if data.get("realized") is not None:
        correct = (data["realized"] > 0 and out["prob_up"] >= 0.5) or (data["realized"] <= 0 and out["prob_up"] < 0.5)
        record_prediction({"uid": user_id, "variant": out["variant"], "correct": bool(correct)})
    return jsonify(out), 200

@ml_bp.route("/metrics", methods=["GET"])
def metrics():
    return jsonify(aggregate()), 200

@ml_bp.route("/train", methods=["POST"])
def train():
    payload = request.get_json() or {}
    symbol = payload.get("symbol", "BTC/USDT")
    horizon = int(payload.get("horizon", 7))
    res = ml_train(symbol=symbol, horizon=horizon)
    return jsonify({"status": "ok", "metrics": res}), 200

@ml_bp.route("/warmup", methods=["POST"])
def warm():
    return jsonify({"ready": warmup()}), 200

