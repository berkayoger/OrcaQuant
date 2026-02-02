import json

from flask import Blueprint, g, jsonify
from flask_jwt_extended import jwt_required

from backend.auth.jwt_utils import require_csrf
from backend.utils.usage_limits import get_usage_count

limits_bp = Blueprint("limits", __name__, url_prefix="/api/limits")


@limits_bp.route("/status", methods=["GET"])
@jwt_required()
@require_csrf
def get_limit_status():
    user = g.user
    plan = getattr(user, "plan", None)
    features = getattr(plan, "features", {})
    if isinstance(features, str):
        try:
            features = json.loads(features)
        except Exception:
            return jsonify({"error": "Plan özellikleri okunamadı."}), 500

    result = {}
    for key, limit in features.items():
        used = get_usage_count(user, key)
        remaining = max(limit - used, 0)
        percent = int((used / limit) * 100) if limit > 0 else 0
        result[key] = {
            "limit": limit,
            "used": used,
            "remaining": remaining,
            "percent_used": percent,
            "warn_75": percent >= 75,
            "warn_90": percent >= 90,
            "exhausted": remaining <= 0,
        }

    payload = {
        "plan": getattr(plan, "name", None),
        "limits": result,
    }
    return jsonify(payload)
