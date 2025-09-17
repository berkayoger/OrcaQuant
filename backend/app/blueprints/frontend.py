"""SPA entrypoint blueprint with optional JWT protection."""

from __future__ import annotations

from typing import Any, Callable

from flask import Blueprint, current_app

try:  # pragma: no cover - optional dependency
    from flask_jwt_extended import jwt_required
except Exception:  # pragma: no cover
    def jwt_required(*args, **kwargs):  # type: ignore
        def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn

        if args and callable(args[0]) and not kwargs:
            return args[0]
        return _decorator

frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/dashboard")
@jwt_required()
def dashboard() -> Any:
    """Serve the SPA dashboard index while preserving auth requirements."""

    return current_app.send_static_file("index.html")
