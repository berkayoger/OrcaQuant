"""admin support tables & promotion_code columns

Revision ID: 20250917_admin_support
Revises: 20251201_01
Create Date: 2025-09-17

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = "20250917_admin_support"
down_revision = "20251201_01"
branch_labels = None
depends_on = None


def _table_exists(inspector: Inspector, table_name: str) -> bool:
    try:
        return inspector.has_table(table_name)
    except Exception:
        return False


def _column_exists(inspector: Inspector, table_name: str, column_name: str) -> bool:
    try:
        return any(col["name"] == column_name for col in inspector.get_columns(table_name))
    except Exception:
        return False


def _index_exists(inspector: Inspector, table_name: str, index_name: str) -> bool:
    try:
        return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "audit_events"):
        op.create_table(
            "audit_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("occurred_at", sa.DateTime(), nullable=False),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), nullable=True),
            sa.Column("target_user_id", sa.Integer(), nullable=True),
            sa.Column("ip", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=256), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
        )
        inspector = sa.inspect(bind)
    if not _index_exists(inspector, "audit_events", "ix_audit_event_type_time"):
        op.create_index(
            "ix_audit_event_type_time",
            "audit_events",
            ["event_type", "occurred_at"],
        )

    if not _table_exists(inspector, "rate_limit_hits"):
        op.create_table(
            "rate_limit_hits",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("occurred_at", sa.DateTime(), nullable=False),
            sa.Column("route", sa.String(length=128), nullable=False),
            sa.Column("ip", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=256), nullable=True),
            sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        )
        inspector = sa.inspect(bind)
    if not _index_exists(inspector, "rate_limit_hits", "ix_rl_route_time"):
        op.create_index(
            "ix_rl_route_time",
            "rate_limit_hits",
            ["route", "occurred_at"],
        )

    if _table_exists(inspector, "promotion_codes"):
        with op.batch_alter_table("promotion_codes", schema=None) as batch_op:
            if not _column_exists(inspector, "promotion_codes", "valid_from"):
                batch_op.add_column(sa.Column("valid_from", sa.DateTime(), nullable=True))
            if not _column_exists(inspector, "promotion_codes", "valid_until"):
                batch_op.add_column(sa.Column("valid_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "promotion_codes"):
        with op.batch_alter_table("promotion_codes", schema=None) as batch_op:
            if _column_exists(inspector, "promotion_codes", "valid_from"):
                batch_op.drop_column("valid_from")
            if _column_exists(inspector, "promotion_codes", "valid_until"):
                batch_op.drop_column("valid_until")

    if _table_exists(inspector, "rate_limit_hits"):
        if _index_exists(inspector, "rate_limit_hits", "ix_rl_route_time"):
            op.drop_index("ix_rl_route_time", table_name="rate_limit_hits")
        op.drop_table("rate_limit_hits")

    if _table_exists(inspector, "audit_events"):
        if _index_exists(inspector, "audit_events", "ix_audit_event_type_time"):
            op.drop_index("ix_audit_event_type_time", table_name="audit_events")
        op.drop_table("audit_events")
