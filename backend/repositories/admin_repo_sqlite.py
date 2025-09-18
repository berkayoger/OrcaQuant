"""SQLAlchemy Core based repository for admin panel data."""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from flask import current_app
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    asc,
    desc,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import or_

metadata = MetaData()

users = Table(
    "admin_users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(120), nullable=False),
    Column("email", String(240), nullable=False, unique=True),
    Column("plan", String(64), nullable=False, default="Free"),
    Column("status", String(24), nullable=False, default="active"),
)

plans = Table(
    "admin_plans",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(64), nullable=False, unique=True),
    Column("price", Integer, nullable=False, default=0),
    Column("limits", String(256), nullable=False, default=""),
    Column("active", Boolean, nullable=False, default=True),
)

limits = Table(
    "admin_limits",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("key", String(64), nullable=False, unique=True),
    Column("used", Integer, nullable=False, default=0),
    Column("limit", Integer, nullable=False, default=0),
)

features = Table(
    "admin_features",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("scope", String(64), nullable=False, unique=True),
    Column("payload", JSON, nullable=False),
)

logs = Table(
    "admin_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ts", String(32), nullable=False),
    Column("level", String(16), nullable=False),
    Column("source", String(64), nullable=False),
    Column("msg", Text, nullable=False),
)

_engine_cache: Engine | None = None


def _engine() -> Engine:
    """Return a cached SQLAlchemy engine for the admin store."""
    global _engine_cache
    if _engine_cache is None:
        uri = current_app.config.get("ADMIN_DATABASE_URI", "sqlite:///admin_store.db")
        _engine_cache = create_engine(uri, future=True)
    return _engine_cache


def ensure_schema_and_seed() -> None:
    """Create tables if necessary and load initial demo data."""
    eng = _engine()
    metadata.create_all(eng)
    with eng.begin() as conn:
        if conn.execute(select(plans.c.id)).first() is None:
            conn.execute(
                insert(plans),
                [
                    {"name": "Free", "price": 0, "limits": "günlük 50 istek", "active": True},
                    {"name": "Basic", "price": 99, "limits": "günlük 500 istek", "active": True},
                    {"name": "Premium", "price": 299, "limits": "günlük 5.000 istek", "active": True},
                    {"name": "Enterprise", "price": 0, "limits": "özel", "active": True},
                ],
            )
        if conn.execute(select(users.c.id)).first() is None:
            conn.execute(
                insert(users),
                [
                    {"name": "Ali Veli", "email": "ali@example.com", "plan": "Premium", "status": "active"},
                    {"name": "Ayşe Demir", "email": "ayse@example.com", "plan": "Basic", "status": "banned"},
                    {"name": "Mehmet Kaya", "email": "mehmet@example.com", "plan": "Enterprise", "status": "active"},
                ],
            )
        if conn.execute(select(limits.c.id)).first() is None:
            conn.execute(
                insert(limits),
                [
                    {"key": "api_requests_day", "used": 18422, "limit": 50000},
                    {"key": "websocket_concurrent", "used": 120, "limit": 500},
                    {"key": "prediction_jobs_day", "used": 64, "limit": 300},
                ],
            )
        if conn.execute(select(features.c.id)).first() is None:
            conn.execute(
                insert(features),
                [
                    {
                        "scope": "global",
                        "payload": {
                            "rbac": {"enabled": True, "roles": ["admin", "analyst", "viewer"]},
                            "flags": {
                                "new_dashboard": True,
                                "ai_explanations": True,
                                "legacy_api": False,
                            },
                        },
                    }
                ],
            )
        if conn.execute(select(logs.c.id)).first() is None:
            now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                insert(logs),
                [
                    {"ts": now, "level": "INFO", "source": "api", "msg": "GET /limits/status 200"},
                    {"ts": now, "level": "WARNING", "source": "worker", "msg": "Queue delay 1.2s"},
                    {"ts": now, "level": "ERROR", "source": "db", "msg": "Timeout on query id=482"},
                ],
            )


def get_overview() -> Dict[str, Any]:
    eng = _engine()
    with eng.connect() as conn:
        user_count = conn.execute(select(users.c.id)).all()
        plan_count = conn.execute(select(plans.c.id)).all()
        api_row = conn.execute(
            select(limits.c.used).where(limits.c.key == "api_requests_day")
        ).first()
        api_used = int(api_row[0]) if api_row else 0
        return {
            "users": len(user_count),
            "usersDelta": "+0.0%",
            "plans": len(plan_count),
            "plansDelta": "+0",
            "api": api_used,
            "errors": "0.67%",
        }


def get_health() -> List[Dict[str, Any]]:
    try:
        eng = _engine()
        with eng.connect() as conn:
            conn.execute(select(1))
        return [{"name": "DB", "status": "healthy", "latencyMs": 17}]
    except SQLAlchemyError:
        return [{"name": "DB", "status": "down", "latencyMs": 0}]


def list_users(
    q: Optional[str] = None,
    limit_n: int = 100,
    offset_n: int = 0,
    sort: str = "id",
    order: str = "desc",
) -> List[Dict[str, Any]]:
    eng = _engine()
    safe_columns = {
        "id": users.c.id,
        "name": users.c.name,
        "email": users.c.email,
        "plan": users.c.plan,
        "status": users.c.status,
    }
    order_col = safe_columns.get(sort, users.c.id)
    direction = desc if order.lower() == "desc" else asc
    stmt = select(users).order_by(direction(order_col)).limit(limit_n).offset(offset_n)
    if q:
        like = f"%{q.lower()}%"
        stmt = (
            select(users)
            .where(or_(users.c.name.ilike(like), users.c.email.ilike(like)))
            .order_by(direction(order_col))
            .limit(limit_n)
            .offset(offset_n)
        )
    with eng.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(stmt)]


def update_user_status(user_id: int, status: str) -> bool:
    eng = _engine()
    with eng.begin() as conn:
        result = conn.execute(
            update(users).where(users.c.id == user_id).values(status=status)
        )
        return result.rowcount > 0


def list_plans() -> List[Dict[str, Any]]:
    eng = _engine()
    with eng.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(select(plans))]


def set_plan_active(name: str, active: bool) -> bool:
    eng = _engine()
    with eng.begin() as conn:
        result = conn.execute(
            update(plans).where(plans.c.name == name).values(active=bool(active))
        )
        return result.rowcount > 0


def list_limits_status() -> List[Dict[str, Any]]:
    eng = _engine()
    with eng.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(select(limits))]


def get_features(scope: str = "global") -> Dict[str, Any]:
    eng = _engine()
    with eng.connect() as conn:
        row = conn.execute(select(features.c.payload).where(features.c.scope == scope)).first()
        return row._mapping["payload"] if row else {}


def set_features(payload: Dict[str, Any], scope: str = "global") -> bool:
    eng = _engine()
    with eng.begin() as conn:
        existing = conn.execute(select(features.c.id).where(features.c.scope == scope)).first()
        if existing:
            result = conn.execute(
                update(features).where(features.c.id == existing[0]).values(payload=payload)
            )
            return result.rowcount > 0
        conn.execute(insert(features).values(scope=scope, payload=payload))
        return True


def list_logs(
    limit_n: int = 200,
    level: Optional[str] = None,
    offset_n: int = 0,
    sort: str = "id",
    order: str = "desc",
) -> List[Dict[str, Any]]:
    eng = _engine()
    safe_columns = {
        "id": logs.c.id,
        "ts": logs.c.ts,
        "level": logs.c.level,
        "source": logs.c.source,
    }
    order_col = safe_columns.get(sort, logs.c.id)
    direction = desc if order.lower() == "desc" else asc
    stmt = select(logs).order_by(direction(order_col)).limit(limit_n).offset(offset_n)
    if level:
        stmt = (
            select(logs)
            .where(logs.c.level == level.upper())
            .order_by(direction(order_col))
            .limit(limit_n)
            .offset(offset_n)
        )
    with eng.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(stmt)]
