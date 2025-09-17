from flask import Blueprint

admin_bp = Blueprint("admin_panel", __name__)

from . import routes  # noqa: E402

admin_console_bp = routes.admin_console_bp

__all__ = ["admin_bp", "admin_console_bp"]
