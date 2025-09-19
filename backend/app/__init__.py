from __future__ import annotations

import logging
import os

from flask import Flask, current_app, request
from flask.testing import FlaskClient
from sqlalchemy.pool import StaticPool
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.api.admin.logs import admin_logs_bp
from backend.draks import draks_bp

from .logging_config import configure_json_logging
from .middleware.request_id import request_id_middleware
from .security import security_headers


def create_app(config_object: str | None = None) -> Flask:
    """Flask uygulamasını oluşturur ve çekirdek bileşenleri bağlar."""
    static_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
    app = Flask(__name__, static_folder=static_root, static_url_path="/static")

    # Provide legacy-compatible test client for set_cookie signature
    class _CompatClient(FlaskClient):
        def set_cookie(self, *args, **kwargs):  # type: ignore[override]
            # Support both Flask<3 (domain, key, value, ...) and Flask>=3 (key, value, ...)
            if len(args) >= 3 and isinstance(args[0], str) and isinstance(args[1], str):
                domain, key, value = args[:3]
                return super().set_cookie(key, value, domain=domain, **kwargs)
            return super().set_cookie(*args, **kwargs)

    app.test_client_class = _CompatClient

    # --- Config ---
    if config_object:
        app.config.from_object(config_object)
    else:
        # Varsayılan olarak ortam bazlı backend.Config kullan
        from backend import Config

        app.config.from_object(Config)

    # Test ortamı varsayılanları
    if os.getenv("FLASK_ENV", "development").lower() == "testing":
        app.config.setdefault("TESTING", True)
        app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
        # Ensure a single shared in-memory DB across requests/sessions
        app.config.setdefault(
            "SQLALCHEMY_ENGINE_OPTIONS",
            {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}},
        )
        app.config.setdefault("PRICE_CACHE_TTL", 0)

    # --- Logging (JSON) ---
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_json_logging(log_level)
    logging.getLogger(__name__).info("app_boot", extra={"stage": "init"})

    # --- Sentry (optional) ---
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration

        dsn = os.getenv("SENTRY_DSN", "")
        if dsn:
            sentry_sdk.init(
                dsn=dsn,
                integrations=[FlaskIntegration(), CeleryIntegration()],
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
                profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
                send_default_pii=False,
            )
    except Exception:
        pass

    # --- Request-ID middleware ---
    request_id_middleware(app)

    # --- Admin RBAC guard for /api/admin/* paths ---
    try:
        from backend.auth.roles import ensure_admin_for_admin_paths

        app.before_request(ensure_admin_for_admin_paths)
    except Exception:
        pass

    # --- Güvenlik başlıkları ---
    security_headers(app)

    # --- SQLAlchemy & Migrate ---
    from backend.db import db, migrate

    db.init_app(app)
    migrate.init_app(app, db)

    # Test ortamında şema oluştur
    if app.config.get("TESTING", False):
        with app.app_context():
            from backend.db import models  # ensure models loaded
            from backend.models.plan import Plan  # ensure plans table loaded

            db.create_all()
            # Seed essential roles for tests if missing
            try:
                from backend.db.models import Permission, Role

                created = False
                if not Role.query.filter_by(name="user").first():
                    db.session.add(Role(name="user"))
                    created = True
                if not Role.query.filter_by(name="admin").first():
                    db.session.add(Role(name="admin"))
                    created = True
                if not Permission.query.filter_by(name="admin_access").first():
                    db.session.add(
                        Permission(
                            name="admin_access", description="Admin panel access"
                        )
                    )
                    created = True
                # Ensure admin role has admin_access permission
                try:
                    admin_role = Role.query.filter_by(name="admin").first()
                    admin_perm = Permission.query.filter_by(name="admin_access").first()
                    if (
                        admin_role
                        and admin_perm
                        and admin_perm not in admin_role.permissions
                    ):
                        admin_role.permissions.append(admin_perm)
                        created = True
                except Exception:
                    pass
                if created:
                    db.session.commit()
            except Exception:
                db.session.rollback()

    # --- ProxyFix ---
    if os.getenv("ENABLE_PROXY_FIX", "false").lower() == "true":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # --- Blueprints ---
    # Sağlık uçları (/health, /ready)
    from .health import bp as health_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(draks_bp)
    try:
        from backend.api.routes import api_bp

        app.register_blueprint(api_bp, url_prefix="/api")
    except Exception:
        pass

    # Admin: logs, system events, tests, promos, plans
    app.register_blueprint(admin_logs_bp)
    try:
        from backend.api.admin.system_events import events_bp

        app.register_blueprint(events_bp)
    except Exception:
        pass
    try:
        from backend.api.admin.tests import admin_tests_bp

        app.register_blueprint(admin_tests_bp)
    except Exception:
        pass
    try:
        from backend.api.admin.promo_codes import admin_promo_bp

        app.register_blueprint(admin_promo_bp)
    except Exception:
        pass
    try:
        from backend.api.admin.promotion_codes import admin_promotion_bp

        app.register_blueprint(admin_promotion_bp)
    except Exception:
        pass
    try:
        from backend.api.admin.users import user_admin_bp

        app.register_blueprint(user_admin_bp)
    except Exception:
        pass
    try:
        from backend.api.admin.draks_monitor import admin_draks_bp

        app.register_blueprint(admin_draks_bp)
    except Exception:
        pass
    try:
        from backend.api.admin.plans import plan_admin_bp

        app.register_blueprint(plan_admin_bp, url_prefix="/api")
    except Exception:
        pass
    try:
        from backend.api.admin.predictions import \
            predictions_bp as admin_predictions_bp

        app.register_blueprint(admin_predictions_bp)
    except Exception:
        pass
    try:
        from backend.auth import auth_bp  # blueprint
        from backend.auth import \
            routes as _auth_routes  # ensure routes are registered

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
    except Exception:
        pass
    try:
        from backend.api.plan_admin_limits import plan_admin_limits_bp

        app.register_blueprint(plan_admin_limits_bp)
    except Exception:
        pass

    # Lightweight admin dashboard & CSRF helpers
    try:
        from backend.blueprints import admin_api as dashboard_bp
        from backend.blueprints import csrf_api as csrf_bp

        if "csrf_api" not in app.blueprints:
            app.register_blueprint(csrf_bp.bp)
        if "admin_api" not in app.blueprints:
            admin_bp = getattr(dashboard_bp, "admin_bp", getattr(dashboard_bp, "bp", None))
            if admin_bp is not None:
                url_prefix = None if getattr(admin_bp, "url_prefix", None) else "/api/admin"
                app.register_blueprint(admin_bp, url_prefix=url_prefix)
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "dashboard blueprints not registered: %s", exc
        )

    # ML Blueprint (opsiyonel)
    try:
        from backend.ml.routes import ml_bp
        app.register_blueprint(ml_bp)
    except Exception as e:
        logging.getLogger(__name__).warning(f"ML routes not registered: {e}")

    # Modern API blueprint (opsiyonel, fallback destekli)
    try:
        from .blueprints.api_modern import api_modern_bp, limiter as api_modern_limiter

        if "api_modern" not in app.blueprints:
            app.register_blueprint(api_modern_bp, url_prefix="/api")
        if api_modern_limiter:
            try:
                api_modern_limiter.init_app(app)
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    "api_modern limiter init skipped: %s", exc
                )
    except Exception as exc:
        logging.getLogger(__name__).warning("api_modern blueprint not registered: %s", exc)

    # Frontend SPA blueprint (opsiyonel)
    try:
        from .blueprints.frontend import frontend_bp

        if "frontend" not in app.blueprints:
            app.register_blueprint(frontend_bp)
    except Exception as exc:
        logging.getLogger(__name__).warning("frontend blueprint not registered: %s", exc)

    # --- RESTX API v1 (versioned) ---
    try:
        from backend.api.restx_v1 import create_v1_blueprint

        base = os.getenv("API_BASE_PREFIX", "/api/v1")
        title = os.getenv("API_TITLE", "OrcaQuant Crypto Analysis API")
        version = os.getenv("API_VERSION", "1.0.0")
        v1_bp, _ = create_v1_blueprint(base_url=base, title=title, version=version)
        app.register_blueprint(v1_bp)
    except Exception:
        # RESTX is optional; skip if not installed
        pass

    @app.after_request
    def _set_cache_headers(resp):
        try:
            path = request.path or ""
            endpoint = request.endpoint or ""
            if path.startswith("/api/") or endpoint.startswith("api"):
                resp.headers["Cache-Control"] = "no-store"
                resp.headers.setdefault("X-Content-Type-Options", "nosniff")
            elif path.startswith("/static/"):
                resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        except Exception:
            pass
        return resp

    def _serve_spa_index():
        static_folder = app.static_folder or ""
        index_path = os.path.join(static_folder, "index.html") if static_folder else ""
        if static_folder and os.path.exists(index_path):
            return current_app.send_static_file("index.html")
        return {"error": "SPA build not found"}, 503

    @app.route("/")
    @app.route("/analysis")
    @app.route("/portfolio")
    def serve_spa():
        return _serve_spa_index()

    return app
