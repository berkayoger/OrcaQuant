from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Iterable, Optional

from flask import Blueprint, Response, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from werkzeug.exceptions import HTTPException

# Custom registry so we can export only our app metrics if needed
REGISTRY = CollectorRegistry()
METRICS_START_KEY = "orcaquant.metrics.start"

HTTP_REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests processed by Flask",
    ["method", "endpoint", "status"],
    registry=REGISTRY,
)

HTTP_REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    registry=REGISTRY,
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)


def _latency_buckets_from_env() -> Optional[Iterable[float]]:
    raw = os.getenv("METRICS_LATENCY_BUCKETS", "").strip()
    if not raw:
        return None
    try:
        return [float(x) for x in raw.split(",") if x.strip()]
    except Exception:
        return None


_latency_buckets = _latency_buckets_from_env()

REQUEST_LATENCY = Histogram(
    "draks_request_latency_seconds",
    "Request latency in seconds.",
    ["route"],
    registry=REGISTRY,
    buckets=_latency_buckets
    or (
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.2,
        0.3,
        0.5,
        0.75,
        1.0,
        2.0,
        3.0,
        5.0,
        8.0,
        13.0,
    ),
)

DECISION_REQ_TOTAL = Counter(
    "draks_decision_requests_total",
    "Total number of decision/run requests.",
    ["status"],
    registry=REGISTRY,
)

COPY_REQ_TOTAL = Counter(
    "draks_copy_requests_total",
    "Total number of copy/evaluate requests.",
    ["status"],
    registry=REGISTRY,
)

ERRORS_TOTAL = Counter(
    "draks_errors_total",
    "Total number of DRAKS errors.",
    ["type"],
    registry=REGISTRY,
)

# ---------------- Batch Metrics ----------------
BATCH_SUBMIT_TOTAL = Counter(
    "draks_batch_submit_total",
    "Total number of batch submits.",
    ["status"],
    registry=REGISTRY,
)

BATCH_ITEM_TOTAL = Counter(
    "draks_batch_items_total",
    "Total number of batch items processed.",
    ["asset", "status"],
    registry=REGISTRY,
)

BATCH_JOB_DURATION = Histogram(
    "draks_batch_job_duration_seconds",
    "Duration of batch job processing from submit to complete.",
    registry=REGISTRY,
    buckets=(1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1200),
)

OHLCV_CACHE_HIT = Counter(
    "draks_ohlcv_cache_hit_total",
    "OHLCV cache hits.",
    ["asset"],
    registry=REGISTRY,
)

OHLCV_CACHE_MISS = Counter(
    "draks_ohlcv_cache_miss_total",
    "OHLCV cache misses.",
    ["asset"],
    registry=REGISTRY,
)


def inc_decision(status: str) -> None:
    DECISION_REQ_TOTAL.labels(status=str(status)).inc()


def inc_copy(status: str) -> None:
    COPY_REQ_TOTAL.labels(status=str(status)).inc()


def inc_error(err_type: str) -> None:
    ERRORS_TOTAL.labels(type=str(err_type)).inc()


def inc_batch_submit(status: str) -> None:
    BATCH_SUBMIT_TOTAL.labels(status=str(status)).inc()


def inc_batch_item(asset: str, status: str) -> None:
    BATCH_ITEM_TOTAL.labels(asset=str(asset), status=str(status)).inc()


def observe_batch_duration(seconds: float) -> None:
    BATCH_JOB_DURATION.observe(float(seconds))


def inc_cache_hit(asset: str) -> None:
    OHLCV_CACHE_HIT.labels(asset=str(asset)).inc()


def inc_cache_miss(asset: str) -> None:
    OHLCV_CACHE_MISS.labels(asset=str(asset)).inc()


@contextmanager
def observe(route: str):
    """Context manager to time a section and observe into REQUEST_LATENCY."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt = time.perf_counter() - t0
        REQUEST_LATENCY.labels(route=route).observe(dt)


def prometheus_wsgi_app(environ, start_response):
    """Minimal WSGI app returning metrics content. Use with Flask via a wrapper route."""
    data = generate_latest(REGISTRY)
    status = "200 OK"
    headers = [
        ("Content-Type", CONTENT_TYPE_LATEST),
        ("Content-Length", str(len(data))),
    ]
    start_response(status, headers)
    return [data]


def _is_truthy(value: Optional[object]) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def _label_endpoint(endpoint: Optional[str]) -> str:
    return (endpoint or "unknown").replace(".", "_")


def _observe_request_metrics(method: Optional[str], endpoint: Optional[str], status: int, duration: Optional[float]) -> None:
    method_label = (method or "UNKNOWN").upper()
    endpoint_label = _label_endpoint(endpoint)
    if duration is not None:
        HTTP_REQUEST_LATENCY.labels(method=method_label, endpoint=endpoint_label).observe(duration)
    HTTP_REQUEST_COUNT.labels(method=method_label, endpoint=endpoint_label, status=str(status)).inc()


def register_metrics(app):  # pragma: no cover - integration wiring
    if "orcaquant_metrics" in app.blueprints:
        return

    metrics_path = (
        app.config.get("PROMETHEUS_METRICS_PATH")
        or os.getenv("PROMETHEUS_METRICS_PATH", "/metrics")
    )
    if not str(metrics_path).startswith("/"):
        metrics_path = f"/{metrics_path}"

    metrics_bp = Blueprint("orcaquant_metrics", __name__)

    def _enabled() -> bool:
        value = app.config.get("ENABLE_METRICS")
        if value is None:
            value = os.getenv("ENABLE_METRICS", "true")
        return _is_truthy(value)

    def _metrics_view():
        if not _enabled():
            return Response("metrics disabled\n", status=404, mimetype="text/plain")
        return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)

    metrics_bp.add_url_rule(metrics_path, "metrics", _metrics_view)

    @app.before_request
    def _metrics_before_request():
        if not _enabled():
            return
        request.environ[METRICS_START_KEY] = time.perf_counter()

    @app.after_request
    def _metrics_after_request(response):
        if not _enabled():
            return response
        start = request.environ.pop(METRICS_START_KEY, None)
        duration = None
        if start is not None:
            duration = time.perf_counter() - start
        _observe_request_metrics(request.method, request.endpoint, response.status_code, duration)
        return response

    @app.teardown_request
    def _metrics_teardown(exc):
        if not _enabled() or exc is None:
            return
        start = request.environ.pop(METRICS_START_KEY, None)
        duration = None
        if start is not None:
            duration = time.perf_counter() - start
        status = 500
        if isinstance(exc, HTTPException) and getattr(exc, "code", None):
            status = exc.code  # type: ignore[assignment]
        _observe_request_metrics(request.method, request.endpoint, status, duration)

    app.register_blueprint(metrics_bp)
    app.logger.info("Prometheus metrics blueprint registered at %s", metrics_path)
