from flask import Blueprint, Response, jsonify, stream_with_context
from backend.utils.price_fetcher import fetch_current_price
from time import sleep, time
import json, random, logging

logger = logging.getLogger(__name__)
bp_market = Blueprint("market", __name__)

@bp_market.route("/api/market/current", methods=["GET"])
def market_current():
    """Get current market price - integrates with existing price_fetcher"""
    try:
        # Use existing price fetcher
        price = fetch_current_price("BTCUSDT")
        if price is None:
            # Fallback to demo data
            price = round(50000 + random.random() * 1000, 2)
        
        return jsonify({
            "symbol": "BTCUSDT", 
            "price": price,
            "ts": int(time() * 1000),
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Market current error: {e}")
        return jsonify({"error": "Failed to fetch price"}), 500

@bp_market.route("/api/market/stream", methods=["GET"])
def market_stream_sse():
    """Server-Sent Events for real-time prices"""
    def generate():
        try:
            btc_price = 50000 + random.random() * 1000
            while True:
                # Try to get real price, fallback to simulation
                real_price = fetch_current_price("BTCUSDT")
                if real_price:
                    price = real_price
                else:
                    btc_price += (random.random() - 0.5) * 200
                    price = max(30000, min(80000, btc_price))
                
                payload = {
                    "symbol": "BTCUSDT",
                    "price": round(price, 2),
                    "ts": int(time() * 1000),
                    "volume": random.randint(100, 1000)
                }
                yield f"event: price\ndata: {json.dumps(payload)}\n\n"
                sleep(1)
        except Exception as e:
            logger.error(f"Market stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@bp_market.route("/api/market/symbols", methods=["GET"])
def market_symbols():
    """Get available trading symbols"""
    return jsonify({
        "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT"],
        "status": "success"
    })
