"""Modern API blueprint with optional JWT and rate limiting fallbacks."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Optional

from flask import Blueprint, current_app, jsonify, request

try:  # pragma: no cover - optional dependency
    from flask_jwt_extended import get_jwt_identity, jwt_required
except Exception:  # pragma: no cover
    def jwt_required(*args, **kwargs):  # type: ignore
        def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn

        if args and callable(args[0]) and not kwargs:
            return args[0]
        return _decorator

    def get_jwt_identity() -> Optional[str]:  # type: ignore
        return None

try:  # pragma: no cover - optional dependency
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address)
except Exception:  # pragma: no cover
    limiter = None

api_modern_bp = Blueprint("api_modern", __name__)


def rate_limit_per_minute(limit: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a rate limit decorator or no-op when limiter is unavailable."""

    if limiter is None:
        def _noop(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn

        return _noop

    return limiter.limit(f"{limit}/minute")


def _safe_import(dotted_path: str) -> Any:
    """Import attribute given a dotted path, returning None on failure."""

    try:
        module_path, attr = dotted_path.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, attr)
    except Exception:  # pragma: no cover - best effort import
        return None


AnalysisService = _safe_import("backend.services.analysis.AnalysisService") or _safe_import(
    "app.services.analysis.AnalysisService"
)
PredictionService = _safe_import("backend.services.prediction.PredictionService") or _safe_import(
    "app.services.prediction.PredictionService"
)
get_user_portfolio_summary = _safe_import(
    "backend.services.portfolio.get_user_portfolio_summary"
)
get_active_positions = _safe_import("backend.services.portfolio.get_active_positions")
calculate_prediction_accuracy = _safe_import(
    "backend.services.prediction.calculate_prediction_accuracy"
)
get_active_alerts = _safe_import("backend.services.alerts.get_active_alerts")


@api_modern_bp.route("/dashboard/summary", methods=["GET"])
@jwt_required()
@rate_limit_per_minute(30)
def get_dashboard_summary() -> Any:
    """Return dashboard summary payload with safe fallbacks."""

    user_id = get_jwt_identity()
    try:
        portfolio_data = (
            get_user_portfolio_summary(user_id)
            if get_user_portfolio_summary
            else {"value": 0, "delta": 0}
        )
        positions = get_active_positions(user_id) if get_active_positions else []
        prediction_accuracy = (
            calculate_prediction_accuracy(user_id)
            if calculate_prediction_accuracy
            else 0.0
        )
        alerts = get_active_alerts(user_id) if get_active_alerts else []
        return jsonify(
            {
                "portfolio": portfolio_data,
                "positions": {"active": len(positions)},
                "predictions": {"accuracy": prediction_accuracy},
                "alerts": {"active": len(alerts)},
            }
        )
    except Exception as exc:  # pragma: no cover - best effort
        current_app.logger.error(
            "Dashboard summary error", extra={"user_id": user_id, "error": str(exc)}
        )
        return jsonify({"error": "Veri alınamadı"}), 500


@api_modern_bp.route("/analysis/<symbol>", methods=["GET"])
@jwt_required()
@rate_limit_per_minute(60)
def get_symbol_analysis(symbol: str) -> Any:
    """Return detailed analysis for a symbol, with demo fallback."""

    timeframe = request.args.get("timeframe", "1h")
    try:
        if AnalysisService is None:
            return jsonify(
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamps": [],
                    "prices": [],
                    "indicators": {
                        "ema_12": [],
                        "ema_26": [],
                        "rsi": [],
                        "macd": [],
                    },
                    "volume": [],
                    "analysis": {"note": "AnalysisService bulunamadı; demo dönüş."},
                }
            )
        service = AnalysisService()
        data = service.get_full_analysis(symbol, timeframe)  # type: ignore[attr-defined]
        return jsonify(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamps": data.get("timestamps", []),
                "prices": data.get("prices", []),
                "indicators": {
                    "ema_12": data.get("ema_12", []),
                    "ema_26": data.get("ema_26", []),
                    "rsi": data.get("rsi", []),
                    "macd": data.get("macd", []),
                },
                "volume": data.get("volume", []),
                "analysis": data.get("analysis", {}),
            }
        )
    except Exception as exc:  # pragma: no cover - best effort
        current_app.logger.error(
            "Analysis error", extra={"symbol": symbol, "error": str(exc)}
        )
        return jsonify({"error": f"{symbol} analizi alınamadı"}), 500


@api_modern_bp.route("/predictions/recent", methods=["GET"])
@jwt_required()
@rate_limit_per_minute(30)
def get_recent_predictions() -> Any:
    """Return five most recent predictions for the authenticated user."""

    user_id = get_jwt_identity()
    try:
        if PredictionService is None:
            return jsonify([])
        predictions = PredictionService().get_user_recent_predictions(  # type: ignore[attr-defined]
            user_id, limit=5
        )
        formatted = []
        for prediction in predictions or []:
            formatted.append(
                {
                    "symbol": getattr(prediction, "symbol", ""),
                    "prediction": getattr(prediction, "prediction_text", ""),
                    "confidence": getattr(prediction, "confidence", 0.0),
                    "horizon": f"{getattr(prediction, 'horizon_days', 0)} gün",
                    "created_at": getattr(prediction, "created_at", ""),
                }
            )
        return jsonify(formatted)
    except Exception as exc:  # pragma: no cover - best effort
        current_app.logger.error(
            "Recent predictions error", extra={"user_id": user_id, "error": str(exc)}
        )
        return jsonify([])


@api_modern_bp.route("/health/frontend", methods=["GET"])
def frontend_health() -> Any:
    """Return placeholder frontend health metrics for observability dashboards."""

    return jsonify(
        {
            "build_time": None,
            "bundle_size": None,
            "cache_hit_rate": None,
            "chart_load_times": None,
        }
    )
