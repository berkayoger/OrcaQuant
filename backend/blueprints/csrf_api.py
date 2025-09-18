"""CSRF token issuance endpoint for admin clients."""

from __future__ import annotations

from flask import Blueprint, jsonify, g

from backend.auth.jwt_utils import require_admin
from backend.security.csrf import issue_csrf
from backend.extensions import limiter

bp = Blueprint("csrf_api", __name__)


@bp.get("/api/csrf")
@require_admin
@limiter.limit("30 per minute")
def get_csrf():
    # Optional: if require_admin attaches user info to g, reuse it in the token
    user_id = getattr(g, "admin_id", None) or getattr(g, "user_id", "admin")
    token = issue_csrf(user_id=user_id)
    return jsonify({"token": token})
