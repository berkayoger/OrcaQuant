"""Local blueprints for lightweight admin APIs."""

# Namespace initializer for blueprints

from __future__ import annotations

from importlib import import_module

__all__ = ["admin_api", "csrf_api"]

# Lazy import to avoid heavy dependencies during tooling
admin_api = import_module("backend.blueprints.admin_api")
csrf_api = import_module("backend.blueprints.csrf_api")


def iter_blueprints():
    """Yield blueprint objects exposed by this namespace."""

    for module in (admin_api, csrf_api):
        for candidate in ("admin_bp", "csrf_bp", "bp"):
            obj = getattr(module, candidate, None)
            if obj is not None:
                yield obj
                break
