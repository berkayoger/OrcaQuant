from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import BaseModel, Field, ValidationError

from backend.db import db
from ..models import OQAlert

bp = Blueprint("product_v2_alerts", __name__)


def _user_ref():
    claims = get_jwt()
    return str(claims.get("uid") or get_jwt_identity())


class AlertRule(BaseModel):
    type: str = Field(pattern="^(price_below|price_above|rsi_below|rsi_above)$")
    symbol: str
    threshold: float
    cooldown_sec: int = 1800


@bp.post("")
@jwt_required(locations=["cookies", "headers"])
def create_alert():
    try:
        payload = AlertRule(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify(error="validation_error", details=e.errors()), 400
    a = OQAlert(user_ref=_user_ref(), rule=payload.model_dump(), status="active")
    db.session.add(a)
    db.session.commit()
    return jsonify(id=a.id), 201


@bp.get("")
@jwt_required(locations=["cookies", "headers"])
def list_alerts():
    rows = (
        OQAlert.query.filter_by(user_ref=_user_ref())
        .order_by(OQAlert.id.desc())
        .all()
    )
    return jsonify(
        [
            {
                "id": r.id,
                "rule": r.rule,
                "status": r.status,
                "last_fired_at": r.last_fired_at,
            }
            for r in rows
        ]
    )
