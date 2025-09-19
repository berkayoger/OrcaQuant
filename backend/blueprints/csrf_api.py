"""CSRF token issuance endpoint for admin clients."""

from __future__ import annotations

from flask import Blueprint, jsonify, g, make_response

try:
    from backend.auth.jwt_utils import require_admin
except Exception:  # pragma: no cover
    def require_admin(func):  # type: ignore
        return func

try:
    from backend.security.csrf import issue_csrf
except Exception:  # pragma: no cover
    issue_csrf = lambda user_id=None: "dev-csrf-token"  # type: ignore

try:
    from backend.extensions import limiter
except Exception:  # pragma: no cover
    limiter = None  # type: ignore

bp = Blueprint("csrf_api", __name__, url_prefix="/api")
csrf_bp = bp  # Expose alias for auto-registration


@bp.get("/csrf")
@require_admin
@limiter.limit("30 per minute") if hasattr(limiter, "limit") else lambda f: f
def get_csrf():
    # Optional: if require_admin attaches user info to g, reuse it in the token
    user_id = getattr(g, "admin_id", None) or getattr(g, "user_id", "admin")
    token = issue_csrf(user_id=user_id)
    resp = make_response(jsonify({"ok": True, "token": token}))
    resp.headers["X-CSRF-Token"] = token
    resp.headers["Cache-Control"] = "no-store"
    return resp
