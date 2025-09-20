import json
from datetime import datetime, timedelta

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from flask_jwt_extended import jwt_required, verify_jwt_in_request

from backend.auth.middlewares import admin_required
from backend.db.models import SystemEvent, db
from backend.utils.system_events import log_event

events_bp = Blueprint("events_bp", __name__, url_prefix="/api/admin")


def _filtered_events_query():
    q = SystemEvent.query
    event_type = request.args.get("event_type")
    level = request.args.get("level")
    user_id = request.args.get("user_id")
    search = request.args.get("search")
    start = request.args.get("start")
    end = request.args.get("end")
    if event_type:
        q = q.filter(SystemEvent.event_type == event_type)
    if level:
        q = q.filter(SystemEvent.level == level)
    if user_id:
        try:
            q = q.filter(SystemEvent.user_id == int(user_id))
        except (TypeError, ValueError):
            pass
    if search:
        q = q.filter(SystemEvent.message.ilike(f"%{search}%"))
    if start:
        try:
            start_dt = datetime.fromisoformat(start)
            q = q.filter(SystemEvent.created_at >= start_dt)
        except ValueError:
            pass
    if end:
        try:
            end_dt = datetime.fromisoformat(end)
            q = q.filter(SystemEvent.created_at <= end_dt)
        except ValueError:
            pass
    return q


def _serialize_event(event: SystemEvent) -> dict:
    return {
        "id": event.id,
        "event_type": event.event_type,
        "level": event.level,
        "message": event.message,
        "meta": json.loads(event.meta) if event.meta else {},
        "created_at": event.created_at.isoformat(),
        "user_id": event.user_id,
    }


@events_bp.route("/events", methods=["GET"])
@jwt_required()
@admin_required()
def list_events():
    q = _filtered_events_query()
    limit = int(request.args.get("limit", 100))
    events = q.order_by(SystemEvent.created_at.desc()).limit(limit).all()
    return jsonify(
        [
            _serialize_event(e)
            for e in events
        ]
    )


@events_bp.route("/events/stream", methods=["GET"])
def stream_events():
    verify_jwt_in_request(locations=["headers", "query_string", "cookies"])

    def _stream_impl():
        q = _filtered_events_query()
        after_id = request.args.get("after_id")
        if after_id:
            try:
                q = q.filter(SystemEvent.id > int(after_id))
            except ValueError:
                pass
        limit = request.args.get("limit", 100)
        try:
            limit_value = int(limit)
        except (TypeError, ValueError):
            limit_value = 100
        events = (
            q.order_by(SystemEvent.created_at.asc())
            .limit(limit_value)
            .all()
        )

        def generate():
            for event in events:
                payload = _serialize_event(event)
                yield (
                    f"id: {payload['id']}\n"
                    f"event: system_event\n"
                    f"data: {json.dumps(payload)}\n\n"
                )

        response = Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
        )
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        return response

    protected_stream = admin_required()(_stream_impl)
    return protected_stream()


@events_bp.route("/events/retention-cleanup", methods=["POST"])
@jwt_required()
@admin_required()
def retention_cleanup():
    days = int(request.json.get("days", 30)) if request.is_json else 30
    threshold = datetime.utcnow() - timedelta(days=days)
    deleted = SystemEvent.query.filter(SystemEvent.created_at < threshold).delete()
    db.session.commit()
    admin_id = request.headers.get("X-Admin-ID")
    log_event(
        "retention_cleanup",
        "INFO",
        f"{deleted} events removed",
        {"days": days},
        user_id=admin_id,
    )
    return jsonify({"deleted": deleted})


@events_bp.route("/status", methods=["GET"])
@jwt_required()
@admin_required()
def system_status():
    db_status = "online"
    redis_status = "online"
    try:
        db.session.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {e}"
    try:
        current_app.extensions["redis_client"].ping()
    except Exception as e:
        redis_status = f"error: {e}"
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
    except Exception:
        cpu = mem = None
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    job_count = SystemEvent.query.filter(
        SystemEvent.event_type == "job", SystemEvent.created_at >= one_hour_ago
    ).count()
    return jsonify(
        {
            "database": db_status,
            "redis": redis_status,
            "cpu_percent": cpu,
            "memory_percent": mem,
            "jobs_last_hour": job_count,
        }
    )
