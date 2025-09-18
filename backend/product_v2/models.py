from datetime import datetime

from sqlalchemy import func

from backend.db import db


class OQAsset(db.Model):
    __tablename__ = "oq_assets"
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(16), unique=True, index=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class OQPortfolioHolding(db.Model):
    __tablename__ = "oq_portfolio_holdings"
    id = db.Column(db.BigInteger, primary_key=True)
    user_ref = db.Column(
        db.String(128), index=True, nullable=False
    )  # mevcut auth'a dokunmadan referans
    asset_id = db.Column(
        db.Integer, db.ForeignKey("oq_assets.id"), index=True, nullable=False
    )
    qty = db.Column(db.Float, nullable=False)
    avg_cost = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint("user_ref", "asset_id", name="u_oq_holding"),)


class OQAlert(db.Model):
    __tablename__ = "oq_alerts"
    id = db.Column(db.BigInteger, primary_key=True)
    user_ref = db.Column(db.String(128), index=True, nullable=False)
    rule = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="active")
    last_fired_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
