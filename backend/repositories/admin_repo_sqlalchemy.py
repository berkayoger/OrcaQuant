"""SQLAlchemy-backed data access helpers for the admin dashboard views."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Query

from backend.db import db
from backend.db.models import SubscriptionPlan, User
from backend.models.plan import Plan

DEFAULT_SORT = "created_at:desc"
SORTABLE_COLUMNS = {
    "id": User.id,
    "created_at": User.created_at,
    "email": User.email,
    "username": User.username,
    "plan": Plan.name,
    "status": User.is_active,
}


def _apply_sort(query: Query, sort_expr: str) -> Query:
    """Return the query ordered by the supplied expression."""

    expr = (sort_expr or DEFAULT_SORT).strip()
    try:
        column_name, direction = expr.split(":", 1)
    except ValueError:
        column_name, direction = expr, "desc"
    direction = direction.lower()

    column = SORTABLE_COLUMNS.get(column_name, User.created_at)
    order_clause = desc(column) if direction == "desc" else asc(column)
    return query.order_by(order_clause)


def _normalise_plan(plan: Optional[str]) -> Optional[str]:
    if not plan:
        return None
    return plan.strip().lower() or None


def _match_plan(plan_value: Optional[str]) -> Tuple[Optional[Plan], Optional[SubscriptionPlan]]:
    """Return matching Plan row or SubscriptionPlan enum for the provided value."""

    if not plan_value:
        return None, None

    plan_value = plan_value.strip()
    if not plan_value:
        return None, None

    plan_row = (
        Plan.query.filter(func.lower(Plan.name) == plan_value.lower()).first()
        if Plan.query is not None
        else None
    )

    plan_enum = None
    try:
        plan_enum = SubscriptionPlan[plan_value.upper()]
    except KeyError:
        plan_enum = None

    return plan_row, plan_enum


def list_users_server_side(
    *,
    page: int = 1,
    per_page: int = 25,
    plan: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = DEFAULT_SORT,
) -> Tuple[List[Dict[str, Any]], int]:
    """Return paginated user data for the admin grid."""

    query: Query = User.query
    joined_plan = False

    plan_normalised = _normalise_plan(plan)
    if plan_normalised:
        plan_row, plan_enum = _match_plan(plan_normalised)
        if plan_row:
            query = query.join(Plan, isouter=True).filter(func.lower(Plan.name) == plan_normalised)
            joined_plan = True
        elif plan_enum is not None:
            query = query.filter(User.subscription_level == plan_enum)

    if search:
        search_like = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.email.ilike(search_like),
                User.username.ilike(search_like),
            )
        )

    if not joined_plan:
        query = query.outerjoin(Plan)
    query = _apply_sort(query, sort)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items: List[Dict[str, Any]] = []
    for user in pagination.items:
        plan_name = None
        if getattr(user, "plan", None):
            plan_name = user.plan.name
        elif getattr(user, "subscription_level", None) is not None:
            try:
                plan_name = user.subscription_level.name  # type: ignore[union-attr]
            except AttributeError:
                plan_name = str(user.subscription_level)

        items.append(
            {
                "id": user.id,
                "email": user.email or user.username,
                "username": user.username,
                "plan": plan_name,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "status": "active" if getattr(user, "is_active", False) else "inactive",
            }
        )

    return items, pagination.total


def update_user_plan(user_id: Any, new_plan: str) -> Dict[str, Any]:
    """Persist the plan update for the targeted user."""

    if not new_plan:
        raise ValueError("Plan is required")

    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    plan_row, plan_enum = _match_plan(new_plan)
    if not plan_row and plan_enum is None:
        raise ValueError("Unknown plan")

    if plan_row:
        user.plan = plan_row
        try:
            user.subscription_level = SubscriptionPlan[plan_row.name.upper()]
        except KeyError:
            pass
    elif plan_enum is not None:
        user.subscription_level = plan_enum
        if user.plan and user.plan.name.lower() != new_plan.lower():
            user.plan = None

    db.session.add(user)
    db.session.commit()

    return {
        "id": user.id,
        "email": user.email or user.username,
        "plan": (
            user.plan.name
            if getattr(user, "plan", None)
            else (user.subscription_level.name if getattr(user, "subscription_level", None) else None)
        ),
    }
