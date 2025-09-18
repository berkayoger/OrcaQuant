from flask import Blueprint, jsonify, request
from backend.auth.middlewares import require_jwt
from backend.db.models import User
import random

bp_portfolio = Blueprint("portfolio", __name__)

@bp_portfolio.route("/api/portfolio", methods=["GET"])
@require_jwt
def get_portfolio(current_user):
    """Get user portfolio - integrates with existing auth system"""
    try:
        # TODO: Get real portfolio from database
        # For now, return demo data
        total_value = round(20000 + random.random() * 10000, 2)
        
        return jsonify({
            "user_id": current_user.id,
            "total_value_usd": total_value,
            "positions": [
                {
                    "symbol": "BTC",
                    "amount": 0.35,
                    "avg_price": 48500,
                    "current_price": 50000 + random.random() * 1000,
                    "pnl_pct": round((random.random() - 0.5) * 10, 2)
                },
                {
                    "symbol": "ETH", 
                    "amount": 5.2,
                    "avg_price": 3200,
                    "current_price": 3100 + random.random() * 200,
                    "pnl_pct": round((random.random() - 0.5) * 8, 2)
                }
            ],
            "performance": {
                "today_pnl": round((random.random() - 0.5) * 1000, 2),
                "total_pnl": round((random.random() - 0.3) * 5000, 2),
                "win_rate": round(0.6 + random.random() * 0.2, 2)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp_portfolio.route("/api/portfolio/transactions", methods=["GET"])
@require_jwt  
def get_transactions(current_user):
    """Get user transactions history"""
    return jsonify({
        "transactions": [
            {
                "id": "tx_001",
                "type": "buy",
                "symbol": "BTCUSDT",
                "amount": 0.1,
                "price": 49500,
                "timestamp": "2025-01-15T10:30:00Z"
            }
        ]
    })
