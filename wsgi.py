#!/usr/bin/env python3
import os

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


try:
    from backend import create_app, socketio

    app = create_app()
    _safe_setup_observability(app)

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
