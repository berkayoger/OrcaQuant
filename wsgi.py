#!/usr/bin/env python3
import logging
import os
from importlib import import_module

from loguru import logger


def _safe_setup_observability(flask_app):
    """Enable metrics/logging without breaking boot if optional deps fail."""
    try:
        from backend.observability.metrics import register_metrics

        register_metrics(flask_app)
    except Exception as exc:  # pragma: no cover - defensive around optional deps
        flask_app.logger.warning("Metrics setup skipped: %s", exc)

    try:
        from backend.logging_conf import configure_logging

        configure_logging(flask_app)
    except Exception as exc:  # pragma: no cover
        flask_app.logger.warning("Logging setup skipped: %s", exc)


def _auto_register_admin_blueprints(flask_app):
    """Best-effort registration for admin blueprints (defensive)."""

    def _import_first(*module_paths):
        for path in module_paths:
            try:
                return import_module(path)
            except Exception:
                continue
        return None

    def _resolve_blueprint(module, *candidate_names):
        if module is None:
            return None
        for name in candidate_names:
            obj = getattr(module, name, None)
            try:
                from flask import Blueprint  # local import to avoid optional dep issues

                if isinstance(obj, Blueprint):
                    return obj
            except Exception:
                # Fall back to duck typing
                if hasattr(obj, "register") or hasattr(obj, "name"):
                    return obj
        return None

    try:
        admin_module = _import_first("backend.blueprints.admin_api", "app.blueprints.admin_api")
        csrf_module = _import_first("backend.blueprints.csrf_api", "app.blueprints.csrf_api")

        admin_bp = _resolve_blueprint(admin_module, "admin_bp", "bp", "blueprint")
        csrf_bp = _resolve_blueprint(csrf_module, "csrf_bp", "bp", "blueprint")

        if admin_bp:
            if admin_bp.name not in flask_app.blueprints:
                url_prefix = None if getattr(admin_bp, "url_prefix", None) else "/api/admin"
                flask_app.register_blueprint(admin_bp, url_prefix=url_prefix)
        if csrf_bp:
            if csrf_bp.name not in flask_app.blueprints:
                url_prefix = None if getattr(csrf_bp, "url_prefix", None) else "/api"
                flask_app.register_blueprint(csrf_bp, url_prefix=url_prefix)
    except Exception as exc:  # pragma: no cover - defensive auto-registration
        logging.getLogger(__name__).warning("Admin blueprints not registered: %s", exc)


try:
    from backend import create_app, socketio

    app = create_app()
    _safe_setup_observability(app)
    _auto_register_admin_blueprints(app)

    if __name__ == "__main__":
        logger.info("Flask uygulaması başlatılıyor.")

        # Development ortamında basit HTTP server kullan
        if os.getenv("FLASK_ENV") == "development":
            print("🚀 Development mode - HTTP server başlatılıyor...")
            print("📡 Sunucu: http://localhost:5000")
            print("⚠️  SocketIO devre dışı (geliştirme için)")

            # SocketIO olmadan çalıştır
            app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
        else:
            # Production'da SocketIO ile çalıştır
            logger.info("Production mode - SocketIO server başlatılıyor...")
            socketio.run(
                app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True
            )

except ImportError as e:
    logger.error(f"Import hatası: {e}")
    print("❌ Backend modülleri yüklenemedi!")
    exit(1)
except Exception as e:
    logger.error(f"Uygulama başlatma hatası: {e}")
    print(f"❌ Hata: {e}")
    exit(1)
