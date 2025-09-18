"""Local blueprints for lightweight admin APIs."""

from __future__ import annotations

from importlib import import_module

__all__ = ["admin_api", "csrf_api"]

# Lazy import to avoid heavy dependencies during tooling
admin_api = import_module("backend.blueprints.admin_api")
csrf_api = import_module("backend.blueprints.csrf_api")
