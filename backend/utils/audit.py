import json
import os
import smtplib
from collections.abc import Mapping, Sequence
from email.mime.text import MIMEText
from types import SimpleNamespace
from typing import Any

import requests
from flask import g, has_request_context, request

from backend.db import db
from backend.db.models import AuditLog

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ADMIN_ALERT_EMAIL = os.getenv("ADMIN_ALERT_EMAIL")

# Aksiyon listesi kritik olaylari belirtir
CRITICAL_ACTIONS = [
    "admin_user_deleted",
    "admin_user_banned",
    "admin_login",
    "critical_error",
]

_ADMIN_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_ADMIN_PATH_PREFIXES: tuple[str, ...] = ("/api/admin", "/admin")
_SENSITIVE_KEYS = {
    "password",
    "pass",
    "pwd",
    "token",
    "secret",
    "authorization",
    "api_key",
    "apikey",
    "access_token",
}


def _serialize_details(details: Any) -> str | None:
    if details is None:
        return None
    if isinstance(details, str):
        return details
    if isinstance(details, bytes):
        try:
            return details.decode("utf-8")
        except Exception:
            return details.decode("latin1", errors="ignore")
    try:
        return json.dumps(details, default=str, sort_keys=True)
    except Exception:
        return str(details)


def _sanitize_payload(payload: Any) -> Any:
    if isinstance(payload, Mapping):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            lowered = key.lower()
            if lowered in _SENSITIVE_KEYS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = _sanitize_payload(value)
        return sanitized
    if isinstance(payload, (list, tuple, set)):
        return [
            _sanitize_payload(item) for item in (payload if isinstance(payload, Sequence) else list(payload))
        ]
    return payload


def _gather_request_details(req, resp, extra: Any = None) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if not req:
        if isinstance(extra, Mapping):
            return dict(extra)
        if extra is not None:
            return {"extra": extra}
        return details

    try:
        details["method"] = req.method
    except Exception:
        pass

    path = getattr(req, "path", None)
    if path:
        details["path"] = path

    endpoint = getattr(req, "endpoint", None)
    if endpoint:
        details["endpoint"] = endpoint

    if getattr(resp, "status_code", None) is not None:
        try:
            details["status_code"] = int(resp.status_code)
        except Exception:
            details["status_code"] = resp.status_code

    query = getattr(req, "query_string", b"")
    if query:
        try:
            details["query_string"] = query.decode("utf-8", errors="ignore")
        except Exception:
            details["query_string"] = str(query)

    forwarded = req.headers.get("X-Forwarded-For") if hasattr(req, "headers") else None
    remote_addr = forwarded or getattr(req, "remote_addr", None)
    if remote_addr:
        details["ip"] = remote_addr

    user_agent = None
    if hasattr(req, "headers"):
        user_agent = req.headers.get("User-Agent")
    if user_agent:
        details["user_agent"] = user_agent[:256]

    payload = None
    try:
        if getattr(req, "is_json", False):
            payload = req.get_json(silent=True)
    except Exception:
        payload = None

    if payload is None:
        try:
            form = getattr(req, "form", None)
            if form:
                payload = {key: form.getlist(key) for key in form}
        except Exception:
            payload = None

    if payload:
        details["payload"] = _sanitize_payload(payload)

    if extra is None:
        return details

    if isinstance(extra, Mapping):
        merged = dict(details)
        merged.update(extra)
        return merged

    details["extra"] = extra
    return details


def _resolve_user(explicit: Any = None) -> Any:
    if explicit is not None:
        return explicit
    if not has_request_context():
        return None
    try:
        for attr in ("user", "current_user"):
            candidate = getattr(g, attr, None)
            if candidate:
                return candidate
    except RuntimeError:
        return None
    candidate = getattr(request, "current_user", None)
    if candidate:
        return candidate
    return None


def _derive_action_name(req) -> str:
    if not req:
        return "admin_auto"
    method = getattr(req, "method", "").upper() or "REQUEST"
    endpoint = getattr(req, "endpoint", None)
    if endpoint:
        return f"admin_auto:{method}:{endpoint}"
    path = getattr(req, "path", None)
    if path:
        return f"admin_auto:{method} {path}"
    return f"admin_auto:{method}"


def _should_auto_audit(req, prefixes: tuple[str, ...]) -> bool:
    if not req:
        return False
    method = getattr(req, "method", "").upper()
    if method not in _ADMIN_MUTATING_METHODS:
        return False
    path = getattr(req, "path", "") or ""
    return any(path.startswith(prefix) for prefix in prefixes)


def log_action(user=None, action: str = "", details=None) -> None:
    """Record an audit log entry for the given user action."""
    log = AuditLog(
        user_id=getattr(user, "id", None),
        username=getattr(user, "email", None) or getattr(user, "username", None),
        action=action,
        ip_address=request.remote_addr if request else None,
        details=details,
    )
    db.session.add(log)
    db.session.commit()

    # OTOMATIK UYARI SISTEMI
    if action in CRITICAL_ACTIONS:
        msg = (
            f"[ALERT] {action} by {log.username} from {log.ip_address} at "
            f"{log.created_at}\nDetails: {details}"
        )

        if SLACK_WEBHOOK_URL:
            try:
                requests.post(SLACK_WEBHOOK_URL, json={"text": msg}, timeout=3)
            except Exception:
                pass

        if ADMIN_ALERT_EMAIL:
            try:
                mail = MIMEText(msg)
                mail["Subject"] = f"ALERT: {action}"
                mail["From"] = "noreply@ytdcrypto.com"
                mail["To"] = ADMIN_ALERT_EMAIL
                with smtplib.SMTP(
                    os.getenv("MAIL_SERVER", "localhost"),
                    int(os.getenv("MAIL_PORT", 25)),
                ) as server:
                    if os.getenv("MAIL_USE_TLS", "false").lower() == "true":
                        server.starttls()
                    username = os.getenv("MAIL_USERNAME")
                    password = os.getenv("MAIL_PASSWORD")
                    if username and password:
                        server.login(username, password)
                    server.send_message(mail)
            except Exception:
                pass


def log_admin_mutation(
    *,
    user: Any = None,
    action: str | None = None,
    req=None,
    resp=None,
    details: Any = None,
) -> None:
    """Log an administrative mutation while preserving legacy behaviour."""

    resolved_user = _resolve_user(user)
    if resolved_user is None:
        return

    request_obj = req
    if request_obj is None and has_request_context():
        request_obj = request

    user_for_logging = resolved_user
    raw_user_id = getattr(resolved_user, "id", None)
    if isinstance(raw_user_id, str):
        try:
            coerced = int(raw_user_id)
        except (TypeError, ValueError):
            coerced = None
        user_for_logging = SimpleNamespace(
            id=coerced,
            email=getattr(resolved_user, "email", None),
            username=getattr(resolved_user, "username", None),
        )
    elif raw_user_id is not None and not isinstance(raw_user_id, int):
        try:
            coerced = int(raw_user_id)
        except (TypeError, ValueError):
            coerced = None
        user_for_logging = SimpleNamespace(
            id=coerced,
            email=getattr(resolved_user, "email", None),
            username=getattr(resolved_user, "username", None),
        )

    derived_action = action or _derive_action_name(request_obj)
    detail_payload: Any
    if request_obj is not None:
        detail_payload = _gather_request_details(request_obj, resp, details)
    else:
        detail_payload = details

    serialized = _serialize_details(detail_payload)
    log_action(user_for_logging, derived_action, serialized)


def bind_auto_audit(app) -> None:
    """Attach an after-request hook that automatically audits admin mutations."""

    if getattr(app, "_auto_admin_audit_bound", False):
        return

    app.config.setdefault("ENABLE_ADMIN_AUTO_AUDIT", True)
    raw_prefixes = app.config.get("ADMIN_AUDIT_PATH_PREFIXES")
    if raw_prefixes:
        if isinstance(raw_prefixes, str):
            prefixes = tuple(
                segment.strip() for segment in raw_prefixes.split(",") if segment.strip()
            )
        else:
            prefixes = tuple(raw_prefixes)
    else:
        prefixes = _ADMIN_PATH_PREFIXES

    @app.after_request
    def _auto_admin_audit(response):
        if not app.config.get("ENABLE_ADMIN_AUTO_AUDIT", True):
            return response
        if not has_request_context():
            return response
        try:
            req = request
            if not _should_auto_audit(req, prefixes):
                return response
            user = _resolve_user()
            if user is None:
                return response
            log_admin_mutation(user=user, req=req, resp=response)
        except Exception:
            try:
                app.logger.debug("Auto audit hook suppressed an exception", exc_info=True)
            except Exception:
                pass
        return response

    app._auto_admin_audit_bound = True
