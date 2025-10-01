"""Helpers to adapt optional backend APIs for the lightweight test-suite."""

from __future__ import annotations

import importlib
import inspect
import types
from typing import Any, Callable, Dict

import pytest


def _import_optional(modname: str):
    try:
        return importlib.import_module(modname)
    except Exception:  # pragma: no cover - missing optional deps
        return None


def get_jwt_api():
    """Locate JWT helper primitives if the module can be imported."""

    mod = _import_optional("backend.auth.jwt_utils")
    if not mod:
        pytest.skip("backend.auth.jwt_utils bulunamadı.")

    token_manager = getattr(mod, "TokenManager", None)
    generate_tokens = getattr(token_manager, "generate_tokens", None) if token_manager else None

    if not (token_manager and callable(generate_tokens)):
        pytest.skip("jwt_utils içinde beklenen TokenManager.generate_tokens API'i bulunamadı.")

    return types.SimpleNamespace(module=mod, token_manager=token_manager)


def get_services_api():
    """Inspect backend.core.services for exportable callables."""

    mod = _import_optional("backend.core.services")
    if not mod:
        pytest.skip("backend.core.services bulunamadı.")

    callables: Dict[str, Callable[..., Any]] = {
        name: obj for name, obj in inspect.getmembers(mod, inspect.isfunction)
    }
    if not callables:
        pytest.skip("services içinde testlenecek fonksiyon yok görünüyor.")

    return types.SimpleNamespace(module=mod, fns=callables)


def get_models_api():
    """Collect SQLAlchemy models defined in backend.db.models."""

    mod = _import_optional("backend.db.models")
    if not mod:
        pytest.skip("backend.db.models bulunamadı.")

    db = getattr(mod, "db", None)
    if db is None:
        try:
            from backend.db import db as global_db  # type: ignore import-not-found
        except Exception:  # pragma: no cover - missing optional deps
            pytest.skip("SQLAlchemy db nesnesi bulunamadı (backend.db.db).")
        else:
            db = global_db

    models = {
        name: obj
        for name, obj in vars(mod).items()
        if inspect.isclass(obj) and getattr(obj, "__tablename__", None)
    }
    if not models:
        pytest.skip("Modülde tabloya karşılık gelen SQLAlchemy modeli bulunamadı.")

    return types.SimpleNamespace(module=mod, db=db, models=models)


def get_helpers_api():
    """Return helper functions declared in backend.utils.helpers."""

    mod = _import_optional("backend.utils.helpers")
    if not mod:
        pytest.skip("backend.utils.helpers bulunamadı.")

    functions: Dict[str, Callable[..., Any]] = {
        name: obj for name, obj in vars(mod).items() if callable(obj)
    }
    if not functions:
        pytest.skip("helpers içinde testlenecek fonksiyon yok.")

    return types.SimpleNamespace(module=mod, fns=functions)
