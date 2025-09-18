"""CSRF token management for web applications."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, jsonify, make_response, current_app, request, g
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import generate_csrf
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.extensions import limiter, redis_client
from backend.settings import get_settings

logger = logging.getLogger(__name__)

csrf_bp = Blueprint("csrf", __name__, url_prefix="/auth")

DEFAULT_TTL = 60 * 60  # 1 saat


def _serializer() -> URLSafeTimedSerializer:
    secret = current_app.config.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY missing")
    salt = current_app.config.get("CSRF_TOKEN_SALT", "csrf-v1")
    return URLSafeTimedSerializer(secret_key=secret, salt=salt)


def issue_csrf(user_id: str | int = "admin") -> str:
    serializer = _serializer()
    payload = {"u": str(user_id), "t": int(time.time()), "n": os.urandom(8).hex()}
    return serializer.dumps(payload)


def verify_csrf(token: str, max_age: int | None = None) -> dict:
    serializer = _serializer()
    ttl = max_age or current_app.config.get("CSRF_TOKEN_TTL", DEFAULT_TTL)
    return serializer.loads(token, max_age=ttl)


def require_csrf(fn):
    """Decorator enforcing CSRF header for mutating requests."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        method = request.method.upper()
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            token = request.headers.get("X-CSRF-Token", "")
            if not token:
                return jsonify({"error": "csrf_missing"}), 403
            try:
                data = verify_csrf(token)
                g.csrf = data
            except SignatureExpired:
                return jsonify({"error": "csrf_expired"}), 403
            except BadSignature:
                return jsonify({"error": "csrf_bad"}), 403
        return fn(*args, **kwargs)

    return wrapper


@csrf_bp.route("/csrf-token", methods=["GET"])
def get_csrf_token():
    """Issue CSRF token for SPA/AJAX applications."""
    s = get_settings()
    try:
        token = generate_csrf()
        expires_at = datetime.utcnow() + timedelta(seconds=s.csrf_time_limit_seconds)
        resp = make_response(
            jsonify(
                {
                    "csrfToken": token,
                    "expiresAt": expires_at.isoformat() + "Z",
                    "headerName": s.csrf_header_name,
                }
            )
        )
        resp.set_cookie(
            key=s.csrf_cookie_name,
            value=token,
            max_age=s.csrf_time_limit_seconds,
            secure=s.session_cookie_secure,
            httponly=False,
            samesite=s.session_cookie_samesite,
            path="/",
        )
        if redis_client:
            client_ip = get_remote_address()
            redis_client.incr(f"csrf_tokens_issued:{client_ip}")
            redis_client.expire(f"csrf_tokens_issued:{client_ip}", 3600)
        logger.info("CSRF token issued for client %s", get_remote_address())
        return resp
    except Exception as exc:
        print("CSRF ERROR:", exc); import traceback; traceback.print_exc()
        return {"error": "csrf_generation_failed"}, 500


if limiter:
    limiter.limit("100/minute")(get_csrf_token)
