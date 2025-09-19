"""Administrative helper APIs for lightweight dashboards."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import asc, desc, func, or_

try:
    from backend.auth.jwt_utils import require_admin, require_csrf
except Exception:  # pragma: no cover - fallback for relaxed environments
    def require_admin(func):  # type: ignore
        return func

    def require_csrf(func):  # type: ignore
        return func

try:
    from backend.db import db
    from backend.db.models import AuditLog, SubscriptionPlan, User
except Exception:  # pragma: no cover - fallback for alternate layouts
    db = None  # type: ignore
    AuditLog = None  # type: ignore
    SubscriptionPlan = None  # type: ignore
    User = None  # type: ignore

try:
    from backend.extensions import limiter
except Exception:  # pragma: no cover - limiter optional
    limiter = None  # type: ignore


admin_bp = Blueprint("admin_api", __name__)
bp = admin_bp  # Backwards compatibility for older imports


def _serialize_plan(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if hasattr(value, "name"):
        return value.name
    return str(value)


def _serialize_datetime(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat() + ("Z" if value.tzinfo is None else "")
    try:
        return str(value)
    except Exception:  # pragma: no cover - defensive
        return None


def _subscription_from_string(raw: str) -> Any:
    cleaned = (raw or "").strip()
    if not cleaned:
        return None
    if SubscriptionPlan is None:
        return cleaned
    for opt in SubscriptionPlan:
        if opt.name.lower() == cleaned.lower() or str(opt.value).lower() == cleaned.lower():
            return opt
    return cleaned


def _require_models():
    if db is None or User is None:
        return (
            jsonify(
                {
                    "error": True,
                    "message": "SQLAlchemy models not available; ensure backend.db is configured.",
                }
            ),
            503,
        )
    return None


def _select_attr(obj: Any, *candidates: str) -> Any:
    for name in candidates:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


@admin_bp.get("/health")
@require_admin
def health() -> Any:
    return jsonify({"ok": True, "ts": datetime.utcnow().isoformat() + "Z"})


@admin_bp.get("/metrics")
@require_admin
def metrics() -> Any:
    missing = _require_models()
    if missing:
        return missing

    session = db.session  # type: ignore[union-attr]
    now = datetime.utcnow()

    total_users = session.query(func.count(User.id)).scalar() or 0

    created_col = _select_attr(User, "created_at", "created")
    if created_col is not None:
        new_30d = (
            session.query(func.count(User.id))
            .filter(created_col >= now - timedelta(days=30))
            .scalar()
            or 0
        )
    else:
        new_30d = 0

    last_login_col = _select_attr(User, "last_login_at", "last_seen_at", "updated_at")
    if last_login_col is not None:
        active_7d = (
            session.query(func.count(User.id))
            .filter(last_login_col >= now - timedelta(days=7))
            .scalar()
            or 0
        )
    else:
        active_col = _select_attr(User, "is_active", "active")
        if active_col is not None:
            active_7d = session.query(func.count(User.id)).filter(active_col.is_(True)).scalar() or 0
        else:
            active_7d = 0

    plan_col = _select_attr(User, "plan", "subscription_level")
    plan_rows: Iterable[tuple[Any, int]] = []
    if plan_col is not None:
        plan_rows = session.query(plan_col, func.count(User.id)).group_by(plan_col).all()
    by_plan = {}
    for raw_plan, count in plan_rows:
        by_plan[_serialize_plan(raw_plan) or "unknown"] = int(count or 0)

    weekly_new = []
    if created_col is not None:
        base = now - timedelta(weeks=11)
        for i in range(12):
            start = (base + timedelta(weeks=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            cnt = (
                session.query(func.count(User.id))
                .filter(created_col >= start, created_col < end)
                .scalar()
                or 0
            )
            weekly_new.append(
                {"week_start": start.isoformat() + "Z", "new_users": int(cnt)}
            )

    return jsonify(
        {
            "total_users": int(total_users),
            "new_30d": int(new_30d),
            "active_7d": int(active_7d),
            "by_plan": by_plan,
            "weekly_new": weekly_new,
        }
    )


@admin_bp.get("/users")
@require_admin
def list_users() -> Any:
    missing = _require_models()
    if missing:
        return missing

    session = db.session  # type: ignore[union-attr]
    q = request.args.get("q", "").strip()
    plan = request.args.get("plan", "").strip()
    status = request.args.get("status", "").strip().lower()
    sort = request.args.get("sort", "created_at:desc", type=str)
    page = max(1, request.args.get("page", 1, type=int))
    page_size = max(1, min(request.args.get("page_size", 25, type=int), 200))

    query = session.query(User)

    if q:
        like = f"%{q}%"
        filters = []
        for fname in ("email", "username", "name", "full_name"):
            if hasattr(User, fname):
                filters.append(getattr(User, fname).ilike(like))
        if filters:
            query = query.filter(or_(*filters))

    if plan:
        plan_attr = _select_attr(User, "plan", "subscription_level")
        if plan_attr is not None:
            resolved = _subscription_from_string(plan)
            query = query.filter(plan_attr == resolved)

    if status:
        status_attr = _select_attr(User, "status", "state", "is_active")
        if status_attr is not None:
            if status in {"active", "1", "true"}:
                query = query.filter(status_attr.is_(True))
            elif status in {"inactive", "blocked", "0", "false"}:
                query = query.filter(status_attr.is_(False))
            else:
                query = query.filter(status_attr == status)

    order_col, _, order_dir = sort.partition(":")
    fallback = _select_attr(User, "created_at", "id")
    sort_col = getattr(User, order_col, fallback)
    if sort_col is None:
        sort_col = User.id

    query = query.order_by(desc(sort_col) if order_dir.lower() == "desc" else asc(sort_col))

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    def serialize_user(user: Any) -> Dict[str, Any]:
        created_value = _select_attr(user, "created_at", "created", "created_on")
        last_login_value = _select_attr(
            user,
            "last_login_at",
            "last_seen_at",
            "last_active_at",
            "updated_at",
        )
        plan_value = _select_attr(user, "plan", "subscription_level")
        status_value = _select_attr(user, "status", "state", "is_active")

        if isinstance(status_value, bool):
            status_repr = "active" if status_value else "inactive"
        else:
            status_repr = status_value

        return {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "username": getattr(user, "username", None),
            "name": getattr(user, "name", None) or getattr(user, "full_name", None),
            "plan": _serialize_plan(plan_value),
            "status": status_repr,
            "created_at": _serialize_datetime(created_value),
            "last_login_at": _serialize_datetime(last_login_value),
        }

    return (
        jsonify(
            {
                "page": page,
                "page_size": page_size,
                "total": total,
                "items": [serialize_user(item) for item in rows],
            }
        ),
        200,
    )


@admin_bp.post("/users/<int:user_id>/plan")
@require_admin
@require_csrf
def update_user_plan(user_id: int) -> Any:
    missing = _require_models()
    if missing:
        return missing

    session = db.session  # type: ignore[union-attr]
    data = request.get_json(silent=True) or {}
    new_plan = (data.get("plan") or "").strip()
    if not new_plan:
        return jsonify({"error": True, "message": "plan alanı zorunludur"}), 400

    user = session.get(User, user_id)
    if not user:
        return jsonify({"error": True, "message": "Kullanıcı bulunamadı"}), 404

    plan_attr_name: Optional[str] = None
    for candidate in ("plan", "subscription_level"):
        if hasattr(User, candidate):
            plan_attr_name = candidate
            break

    resolved = _subscription_from_string(new_plan)
    if plan_attr_name:
        setattr(user, plan_attr_name, resolved)
    else:
        setattr(user, "plan", resolved)

    session.add(user)
    session.commit()
    return jsonify({"ok": True})


@admin_bp.get("/audit-logs")
@require_admin
def audit_logs() -> Any:
    if db is None or AuditLog is None:
        return jsonify({"items": [], "total": 0, "page": 1, "page_size": 50})

    session = db.session  # type: ignore[union-attr]
    page = max(1, request.args.get("page", 1, type=int))
    page_size = max(1, min(request.args.get("page_size", 50, type=int), 200))

    order_column = _select_attr(AuditLog, "created_at", "occurred_at")
    if order_column is None:
        order_column = AuditLog.id
    query = session.query(AuditLog).order_by(desc(order_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    def serialize_log(entry: Any) -> Dict[str, Any]:
        return {
            "id": getattr(entry, "id", None),
            "actor_id": getattr(entry, "user_id", None),
            "action": getattr(entry, "action", None),
            "meta": getattr(entry, "details", None),
            "created_at": _serialize_datetime(_select_attr(entry, "created_at", "occurred_at")),
        }

    return jsonify(
        {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": [serialize_log(entry) for entry in items],
        }
    )


if hasattr(limiter, "limit"):
    limiter.limit("60/minute")(list_users)
    limiter.limit("20/minute")(update_user_plan)
    limiter.limit("30/minute")(audit_logs)
