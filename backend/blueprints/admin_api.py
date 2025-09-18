"""Admin API surface backed by SQLAlchemy Core repository."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, request, g

from backend.auth.jwt_utils import require_admin, require_csrf
from backend.repositories import admin_repo_sqlite as repo

bp = Blueprint("admin_api", __name__, url_prefix="/api/admin/panel")


@bp.get("/me")
@require_admin
def me() -> Response:
    """Return minimal identity information for the admin shell."""
    user = getattr(g, "current_user", None)
    email = None
    roles = ["admin"]
    if isinstance(user, dict):
        email = user.get("email")
        roles = user.get("roles") or roles
    return jsonify({"email": email or "admin@orcaquant.local", "roles": roles})


@bp.get("/overview")
@require_admin
def overview() -> Response:
    data = repo.get_overview()
    return jsonify(data)


@bp.get("/health")
@require_admin
def health() -> Response:
    return jsonify(repo.get_health())


@bp.get("/users")
@require_admin
def list_users() -> Response:
    query = request.args.get("q") or None
    try:
        limit = int(request.args.get("limit", "100"))
    except ValueError:
        limit = 100
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    page = max(1, page)
    sort = (request.args.get("sort") or "id").lower()
    order = (request.args.get("order") or "desc").lower()
    offset = (page - 1) * limit
    records = repo.list_users(q=query, limit_n=limit, offset_n=offset, sort=sort, order=order)
    return jsonify({"items": records, "page": page, "page_size": limit})


@bp.patch("/users/<int:user_id>")
@require_admin
@require_csrf
def update_user(user_id: int) -> Response:
    body = request.get_json(silent=True) or {}
    status = body.get("status")
    if status not in {"active", "banned"}:
        return jsonify({"ok": False, "error": "invalid_status"}), 400
    if not repo.update_user_status(user_id, status):
        return jsonify({"ok": False, "error": "user_not_found"}), 404
    return jsonify({"ok": True, "id": user_id, "status": status})


@bp.get("/plans")
@require_admin
def list_plans() -> Response:
    return jsonify(repo.list_plans())


@bp.patch("/plans/<string:name>")
@require_admin
@require_csrf
def toggle_plan(name: str) -> Response:
    body = request.get_json(silent=True) or {}
    raw_active = body.get("active")
    if isinstance(raw_active, str):
        active = raw_active.lower() in {"1", "true", "yes", "on"}
    else:
        active = bool(raw_active)
    if not repo.set_plan_active(name, active):
        return jsonify({"ok": False, "error": "plan_not_found"}), 404
    return jsonify({"ok": True, "name": name, "active": active})


@bp.get("/limits/status")
@require_admin
def limits_status() -> Response:
    return jsonify(repo.list_limits_status())


@bp.get("/features")
@require_admin
def get_features() -> Response:
    return jsonify(repo.get_features())


@bp.put("/features")
@require_admin
@require_csrf
def put_features() -> Response:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "invalid_json"}), 400
    repo.set_features(payload)
    return jsonify({"ok": True})


@bp.get("/logs")
@require_admin
def get_logs() -> Response:
    level = request.args.get("level") or None
    try:
        limit = int(request.args.get("limit", "200"))
    except ValueError:
        limit = 200
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    page = max(1, page)
    sort = (request.args.get("sort") or "id").lower()
    order = (request.args.get("order") or "desc").lower()
    offset = (page - 1) * limit
    rows = repo.list_logs(limit_n=limit, level=level, offset_n=offset, sort=sort, order=order)
    return jsonify({"items": rows, "page": page, "page_size": limit})
