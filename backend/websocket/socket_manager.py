from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import redis
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime, timedelta
import threading
import time

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self, app=None, redis_client=None):
        self.socketio = None
        self.redis_client = redis_client
        self.active_connections: Dict[str, Set[str]] = {}
        self.connection_metadata: Dict[str, Dict] = {}
        self.rate_limits: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Flask uygulaması ile WebSocket manager'ı başlatır"""
        cors_origins = self._get_cors_origins(app)
        
        self.socketio = SocketIO(
            app,
            cors_allowed_origins=cors_origins,
            logger=True,
            engineio_logger=True,
            # Use threading async mode for broad compatibility in tests/CI
            async_mode='threading',
            ping_timeout=60,
            ping_interval=25,
            max_http_buffer_size=1000000
        )
        
        # Event handlers'ı kaydet
        self._register_handlers()
        
        # Redis subscription thread'ini başlat
        if self.redis_client:
            self._start_redis_subscriber()
    
    def _get_cors_origins(self, app):
        """CORS origins'i environment'a göre ayarlar"""
        if app.config.get('FLASK_ENV') == 'production':
            return [
                app.config.get('FRONTEND_URL', 'https://orcaquant.com'),
                'https://api.orcaquant.com'
            ]
        return "*"
    
    def _register_handlers(self):
        """WebSocket event handlers'ları kaydet"""
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Client bağlantısı kurulduğunda"""
            client_id = request.sid
            client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
            user_agent = request.headers.get('User-Agent', 'unknown')
            
            # Rate limiting kontrolü
            if not self._check_rate_limit(client_ip):
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return False
            
            # Connection metadata'sını kaydet
            self.connection_metadata[client_id] = {
                'connected_at': datetime.utcnow(),
                'ip_address': client_ip,
                'user_agent': user_agent,
                'subscriptions': set(),
                'last_activity': datetime.utcnow()
            }
            
            logger.info(f"Client connected: {client_id} from {client_ip}")
            emit('connection_established', {'status': 'connected', 'id': client_id})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Client bağlantısı kesildiğinde"""
            client_id = request.sid
            self._cleanup_client(client_id)
            logger.info(f"Client disconnected: {client_id}")
        
        @self.socketio.on('subscribe_price')
        def handle_price_subscription(data):
            """Fiyat güncellemelerine abone ol"""
            client_id = request.sid
            symbols = data.get('symbols', [])
            
            if not self._validate_symbols(symbols):
                emit('error', {'message': 'Invalid symbols provided'})
                return
            
            for symbol in symbols:
                room_name = f"price_{symbol}"
                join_room(room_name)
                
                # Client'ın subscription listesini güncelle
                if client_id in self.connection_metadata:
                    self.connection_metadata[client_id]['subscriptions'].add(symbol)
            
            emit('subscription_confirmed', {'symbols': symbols})
            logger.info(f"Client {client_id} subscribed to: {symbols}")
        
        @self.socketio.on('unsubscribe_price')
        def handle_price_unsubscription(data):
            """Fiyat güncellemelerinden aboneliği iptal et"""
            client_id = request.sid
            symbols = data.get('symbols', [])
            
            for symbol in symbols:
                room_name = f"price_{symbol}"
                leave_room(room_name)
                
                # Client'ın subscription listesinden çıkar
                if client_id in self.connection_metadata:
                    self.connection_metadata[client_id]['subscriptions'].discard(symbol)
            
            emit('unsubscription_confirmed', {'symbols': symbols})
            logger.info(f"Client {client_id} unsubscribed from: {symbols}")
        
        @self.socketio.on('ping')
        def handle_ping():
            """Ping-pong için"""
            emit('pong', {'timestamp': time.time()})
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Rate limiting kontrolü yapar"""
        now = datetime.utcnow()
        limit_window = timedelta(minutes=1)
        max_connections = 10
        
        with self._lock:
            if client_ip not in self.rate_limits:
                self.rate_limits[client_ip] = {
                    'connections': [],
                    'last_reset': now
                }
            
            client_limits = self.rate_limits[client_ip]
            
            # Eski kayıtları temizle
            client_limits['connections'] = [
                conn_time for conn_time in client_limits['connections']
                if now - conn_time < limit_window
            ]
            
            # Limit kontrolü
            if len(client_limits['connections']) >= max_connections:
                return False
            
            client_limits['connections'].append(now)
            return True
    
    def _validate_symbols(self, symbols: list) -> bool:
        """Cryptocurrency sembollerini doğrular"""
        if not symbols or len(symbols) > 50:  # Max 50 symbol
            return False
        
        # Geçerli kripto sembollerinin listesi
        valid_symbols = {
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT',
            'BNBUSDT', 'XRPUSDT', 'LTCUSDT', 'BCHUSDT', 'EOSUSDT',
            'TRXUSDT', 'XLMUSDT', 'ATOMUSDT', 'VETUSDT', 'NEOUSDT'
        }
        return all(symbol in valid_symbols for symbol in symbols)
    
    def _cleanup_client(self, client_id: str):
        """Client bağlantısı kesildiğinde temizlik yapar"""
        with self._lock:
            if client_id in self.connection_metadata:
                del self.connection_metadata[client_id]
            
            # Active connections'dan çıkar
            for symbol, clients in self.active_connections.items():
                clients.discard(client_id)
    
    def broadcast_price_update(self, symbol: str, price_data: dict):
        """Fiyat güncellemesini ilgili room'a gönderir"""
        room_name = f"price_{symbol}"
        
        # Redis'e de kaydet
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"price:{symbol}",
                    300,  # 5 dakika cache
                    json.dumps(price_data)
                )
            except Exception as e:
                logger.error(f"Redis price cache error: {e}")
        
        if self.socketio:
            self.socketio.emit(
                'price_update',
                {
                    'symbol': symbol,
                    'data': price_data,
                    'timestamp': datetime.utcnow().isoformat()
                },
                room=room_name
            )
    
    def _start_redis_subscriber(self):
        """Redis pub/sub için thread başlatır"""
        if not self.redis_client:
            return
        
        def redis_subscriber():
            try:
                pubsub = self.redis_client.pubsub()
                pubsub.subscribe('price_updates')
                
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            symbol = data.get('symbol')
                            price_data = data.get('data')
                            
                            if symbol and price_data:
                                self.broadcast_price_update(symbol, price_data)
                        except json.JSONDecodeError:
                            logger.error("Invalid JSON received from Redis")
                        except Exception as e:
                            logger.error(f"Redis subscriber error: {e}")
            except Exception as e:
                logger.error(f"Redis subscriber thread error: {e}")
        
        thread = threading.Thread(target=redis_subscriber, daemon=True)
        thread.start()
        logger.info("Redis subscriber thread started")
    
    def get_connection_stats(self) -> dict:
        """Bağlantı istatistiklerini döndürür"""
        total_connections = len(self.connection_metadata)
        active_subscriptions = sum(
            len(metadata['subscriptions'])
            for metadata in self.connection_metadata.values()
        )
        
        return {
            'total_connections': total_connections,
            'active_subscriptions': active_subscriptions,
            'uptime': datetime.utcnow().isoformat()
        }

# Global instance
websocket_manager = WebSocketManager()
