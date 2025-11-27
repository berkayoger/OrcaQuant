import json
from datetime import date
from functools import wraps
from typing import Any, Dict

from flask import current_app, g, jsonify, request

from backend.db.models import User, UserRole
from backend.utils.plan_limits import get_user_effective_limits
from backend.utils.usage_limits import check_usage_limit


def _resolve_user() -> User | None:
    user = getattr(request, "current_user", None) or getattr(g, "user", None)
    if isinstance(user, User):
        return user

    api_key = request.headers.get("X-API-KEY")
    if api_key:
        found = User.query.filter_by(api_key=api_key).first()
        if found:
            g.user = found
            return found
    return None


def _feature_quota(user: User, feature_key: str) -> Dict[str, Any]:
    limits = get_user_effective_limits(user_id=str(user.id), feature_key=feature_key)
    quota = limits.get("daily_quota")
    return {"quota": int(quota) if quota is not None else None, "plan": limits.get("plan_name")}


def enforce_plan_limit(limit_key: str):
    """Decorator to enforce subscription plan feature limits with consistent quotas."""

    usage_wrapper = check_usage_limit(limit_key)

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = _resolve_user()
            if not user:
                return jsonify({"error": "Auth required"}), 401

            if getattr(user, "role", None) in {UserRole.ADMIN, UserRole.SYSTEM_ADMIN}:
                return f(*args, **kwargs)

            features = getattr(getattr(user, "plan", None), "features", {})
            if isinstance(features, str):
                try:
                    features = json.loads(features)
                except Exception:
                    return jsonify({"error": "Plan özellikleri okunamadı."}), 500

            feature_meta = _feature_quota(user, limit_key)
            quota = feature_meta.get("quota")
            if (quota is None or quota <= 0) and limit_key in features:
                try:
                    quota = int(features.get(limit_key))
                except Exception:
                    quota = None

            if quota is None or quota <= 0 or limit_key not in features:
                return jsonify({"error": f"{limit_key} limiti tanımlı değil."}), 403

            try:
                from backend.db.models import DailyUsage

                today_usage = DailyUsage.query.filter_by(
                    user_id=user.id, feature_key=limit_key, usage_date=date.today()
                ).first()
                if today_usage and today_usage.used_count >= quota:
                    return (
                        jsonify({"error": f"{limit_key} limiti aşıldı. ({quota})"}),
                        429,
                    )
            except Exception:
                pass

            try:
                current_count = user.get_usage_count(limit_key)
            except Exception:
                current_count = 0
            if current_count >= quota:
                return (
                    jsonify({"error": f"{limit_key} limiti aşıldı. ({quota})"}),
                    429,
                )

            wrapped_fn = usage_wrapper(f)
            return wrapped_fn(*args, **kwargs)

        return wrapped

    return decorator
