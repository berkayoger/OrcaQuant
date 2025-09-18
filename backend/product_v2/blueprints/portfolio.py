import csv
import io

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from backend.db import db
from ..models import OQAsset, OQPortfolioHolding

bp = Blueprint("product_v2_portfolio", __name__)


def _user_ref():
    """
    Mevcut JWT yapısına dokunmadan kullanıcıyı belirle:
    - Öncelik: uid claim
    - Yoksa: identity (email gibi) fallback
    """

    claims = get_jwt()
    return str(claims.get("uid") or get_jwt_identity())


@bp.post("/import")
@jwt_required(locations=["cookies", "headers"])
def import_csv():
    if "file" not in request.files:
        return jsonify(error="file_required"), 400
    f = request.files["file"].read()
    reader = csv.DictReader(io.StringIO(f.decode("utf-8")))
    imported, skipped = 0, 0
    user_ref = _user_ref()
    for row in reader:
        try:
            sym = row["symbol"].upper().strip()
            qty = float(row["qty"])
            cost = float(row.get("buy_price", 0) or 0)
        except Exception:
            skipped += 1
            continue
        asset = OQAsset.query.filter_by(symbol=sym).first()
        if not asset:
            asset = OQAsset(symbol=sym, name=sym)
            db.session.add(asset)
            db.session.flush()
        holding = OQPortfolioHolding.query.filter_by(
            user_ref=user_ref, asset_id=asset.id
        ).first()
        if holding:
            total_qty = holding.qty + qty
            if total_qty > 0:
                holding.avg_cost = (
                    holding.qty * holding.avg_cost + qty * cost
                ) / total_qty
            holding.qty = total_qty
        else:
            db.session.add(
                OQPortfolioHolding(
                    user_ref=user_ref,
                    asset_id=asset.id,
                    qty=qty,
                    avg_cost=cost,
                )
            )
        imported += 1
    db.session.commit()
    return jsonify(imported=imported, skipped=skipped), 201


@bp.get("/summary")
@jwt_required(locations=["cookies", "headers"])
def summary():
    user_ref = _user_ref()
    rows = OQPortfolioHolding.query.filter_by(user_ref=user_ref).all()
    positions = []
    for r in rows:
        sym = OQAsset.query.get(r.asset_id).symbol
        positions.append({"symbol": sym, "qty": r.qty, "avg_cost": r.avg_cost})
    total_cost = sum(p["qty"] * (p["avg_cost"] or 0) for p in positions)
    return jsonify(total_value=total_cost, pnl_day=0.0, positions=positions)
