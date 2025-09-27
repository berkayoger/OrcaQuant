"""
WSGI entrypoint (Gunicorn için).
- Sentry, logging, metrics, CORS, rate limiting ve Socket.IO bağlar.
- Uygulama fabrika deseni varsa kullanır; yoksa 'app' fallback'i dener.
"""
import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.config import get_config

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
except Exception:
    sentry_sdk = None

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest
except Exception:
    CONTENT_TYPE_LATEST = "text/plain"
    Gauge = None
    generate_latest = None

try:
    from flask_socketio import SocketIO
except Exception:
    SocketIO = None

socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*") if SocketIO else None
APP_READY = Gauge("orcaquant_app_ready", "App readiness") if Gauge else None


def _create_app() -> Flask:
    try:
        from backend import create_app as factory  # type: ignore

        return factory()
    except Exception:
        try:
            from backend import app as exported  # type: ignore

            application = exported
            application.config.from_object(get_config(os.getenv("FLASK_ENV", "production")))
            return application
        except Exception:
            minimal = Flask(__name__)
            config_cls = get_config(os.getenv("FLASK_ENV", "production"))
            minimal.config.from_object(config_cls)

            @minimal.get("/api/ping")
            def ping():
                return jsonify(ok=True, env=minimal.config.get("ENV"), sha=minimal.config.get("GIT_SHA"))

            return minimal


def _init_observability(app: Flask) -> None:
    if app.config.get("SENTRY_DSN") and sentry_sdk:
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.2,
            send_default_pii=False,
            environment=os.getenv("FLASK_ENV", "production"),
            release=app.config.get("GIT_SHA", "dev"),
        )

    level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    origins = app.config.get("ALLOWED_ORIGINS", ["*"])
    CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=False)

    limits = [limit.strip() for limit in str(app.config.get("RATE_LIMITS", "")).split(";") if limit.strip()]
    limiter_attached = getattr(app, "extensions", {}).get("limiter")
    storage_uri = app.config.get("RATELIMIT_STORAGE_URI", app.config.get("REDIS_URL"))
    if not limiter_attached:
        Limiter(
            key_func=get_remote_address,
            default_limits=limits or None,
            storage_uri=storage_uri,
            strategy="fixed-window-elastic-expiry",
            app=app,
        )

    @app.get("/healthz")
    def healthz():
        if APP_READY:
            APP_READY.set(1)
        return jsonify(status="ok", sha=app.config.get("GIT_SHA", "dev"))

    if app.config.get("ENABLE_METRICS") and generate_latest:

        @app.get("/metrics")
        def metrics():
            data = generate_latest()
            return data, 200, {"Content-Type": CONTENT_TYPE_LATEST}

    if socketio:

        @socketio.on("connect")
        def _on_connect():
            socketio.emit("server_welcome", {"msg": "connected"})


app = _create_app()

# Ensure the real client IP/HTTPS scheme is preserved when running behind
# reverse proxies such as Nginx or a load balancer.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

_init_observability(app)

if socketio:
    app = socketio.WSGIApp(app)
