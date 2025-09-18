from flask_socketio import SocketIO
import time, random, threading
import logging

logger = logging.getLogger(__name__)

# Production'da gevent kullanın
socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")
_price_feeder_started = False
_feeder_lock = threading.Lock()

def _register_events(sock: SocketIO) -> None:
    @sock.on('connect')
    def handle_connect():  # type: ignore[func-returns-value]
        logger.info("Client connected")

    @sock.on('disconnect')
    def handle_disconnect():  # type: ignore[func-returns-value]
        logger.info("Client disconnected")

def _start_price_feeder():
    """Demo price feeder - Production'da gerçek data source kullanın"""
    def run():
        btc_price = 50000 + random.random() * 1000
        try:
            while True:
                # Realistic price movement
                btc_price += (random.random() - 0.5) * 200
                btc_price = max(30000, min(80000, btc_price))
                
                payload = {
                    "symbol": "BTCUSDT",
                    "price": round(btc_price, 2),
                    "ts": int(time.time() * 1000),
                    "volume": random.randint(100, 1000)
                }
                socketio.emit("price", payload)
                time.sleep(1)
        except Exception as e:
            logger.error(f"Price feeder error: {e}")
    
    threading.Thread(target=run, daemon=True).start()

def init_realtime(app):
    """SocketIO initialization"""
    global _price_feeder_started, socketio

    try:
        from backend.websocket.socket_manager import websocket_manager
        manager_socket = getattr(websocket_manager, 'socketio', None)
    except Exception:  # pragma: no cover - defensive
        manager_socket = None
    
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    
    if manager_socket is not None:
        socketio = manager_socket
    else:
        socketio.init_app(app, cors_allowed_origins=cors_origins)
    
    _register_events(socketio)
    
    # Start price feeder once
    with _feeder_lock:
        if not _price_feeder_started:
            _start_price_feeder()
            _price_feeder_started = True
            
    return socketio
