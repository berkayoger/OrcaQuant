from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
import time
import logging

logger = logging.getLogger(__name__)

# Custom registry for WebSocket metrics
websocket_registry = CollectorRegistry()

# Connection metrics
websocket_connections_total = Counter(
    'websocket_connections_total',
    'Total WebSocket connections',
    ['status'],  # connected, disconnected, failed
    registry=websocket_registry
)

websocket_active_connections = Gauge(
    'websocket_active_connections',
    'Currently active WebSocket connections',
    registry=websocket_registry
)

# Message metrics
websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['direction', 'message_type'],  # inbound/outbound, price_update/subscribe etc.
    registry=websocket_registry
)

websocket_message_processing_time = Histogram(
    'websocket_message_processing_seconds',
    'Time spent processing WebSocket messages',
    ['message_type'],
    registry=websocket_registry
)

# Subscription metrics
websocket_subscriptions_total = Counter(
    'websocket_subscriptions_total',
    'Total symbol subscriptions',
    ['symbol', 'action'],  # subscribe/unsubscribe
    registry=websocket_registry
)

websocket_active_subscriptions = Gauge(
    'websocket_active_subscriptions',
    'Currently active symbol subscriptions',
    ['symbol'],
    registry=websocket_registry
)

# Error metrics
websocket_errors_total = Counter(
    'websocket_errors_total',
    'Total WebSocket errors',
    ['error_type'],  # connection_error, message_error, rate_limit etc.
    registry=websocket_registry
)

# Redis metrics
redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status'],  # get/set/publish, success/failure
    registry=websocket_registry
)

# Price streaming metrics
price_updates_total = Counter(
    'price_updates_total',
    'Total price updates received',
    ['symbol', 'source'],  # BTCUSDT, binance/coingecko
    registry=websocket_registry
)

price_update_latency = Histogram(
    'price_update_latency_seconds',
    'Latency between receiving and broadcasting price updates',
    ['symbol'],
    registry=websocket_registry
)

class MetricsCollector:
    """WebSocket metrikleri toplama ve export"""
    
    def __init__(self):
        self.start_time = time.time()
        logger.info("Metrics collector initialized")
    
    def record_connection(self, status):
        """Bağlantı metriğini kaydet"""
        try:
            websocket_connections_total.labels(status=status).inc()
            
            if status == 'connected':
                websocket_active_connections.inc()
            elif status == 'disconnected':
                websocket_active_connections.dec()
                
            logger.debug(f"Connection metric recorded: {status}")
        except Exception as e:
            logger.error(f"Error recording connection metric: {e}")
    
    def record_message(self, direction, message_type, processing_time=None):
        """Mesaj metriğini kaydet"""
        try:
            websocket_messages_total.labels(
                direction=direction, 
                message_type=message_type
            ).inc()
            
            if processing_time:
                websocket_message_processing_time.labels(
                    message_type=message_type
                ).observe(processing_time)
                
            logger.debug(f"Message metric recorded: {direction}/{message_type}")
        except Exception as e:
            logger.error(f"Error recording message metric: {e}")
    
    def record_subscription(self, symbol, action):
        """Subscription metriğini kaydet"""
        try:
            websocket_subscriptions_total.labels(
                symbol=symbol, 
                action=action
            ).inc()
            
            if action == 'subscribe':
                websocket_active_subscriptions.labels(symbol=symbol).inc()
            elif action == 'unsubscribe':
                # Ensure gauge doesn't go negative
                current_value = websocket_active_subscriptions.labels(symbol=symbol)._value._value
                if current_value > 0:
                    websocket_active_subscriptions.labels(symbol=symbol).dec()
                    
            logger.debug(f"Subscription metric recorded: {symbol}/{action}")
        except Exception as e:
            logger.error(f"Error recording subscription metric: {e}")
    
    def record_error(self, error_type):
        """Error metriğini kaydet"""
        try:
            websocket_errors_total.labels(error_type=error_type).inc()
            logger.debug(f"Error metric recorded: {error_type}")
        except Exception as e:
            logger.error(f"Error recording error metric: {e}")
    
    def record_redis_operation(self, operation, status):
        """Redis operasyon metriğini kaydet"""
        try:
            redis_operations_total.labels(
                operation=operation, 
                status=status
            ).inc()
            logger.debug(f"Redis metric recorded: {operation}/{status}")
        except Exception as e:
            logger.error(f"Error recording Redis metric: {e}")
    
    def record_price_update(self, symbol, source, latency=None):
        """Fiyat güncelleme metriğini kaydet"""
        try:
            price_updates_total.labels(
                symbol=symbol,
                source=source
            ).inc()
            
            if latency:
                price_update_latency.labels(symbol=symbol).observe(latency)
                
            logger.debug(f"Price update metric recorded: {symbol}/{source}")
        except Exception as e:
            logger.error(f"Error recording price update metric: {e}")
    
    def get_metrics_text(self):
        """Prometheus formatında metrics döndür"""
        try:
            return generate_latest(websocket_registry)
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return ""
    
    def get_metrics_content_type(self):
        """Metrics content type döndür"""
        return CONTENT_TYPE_LATEST
    
    def get_connection_count(self):
        """Aktif bağlantı sayısını döndür"""
        try:
            return int(websocket_active_connections._value._value)
        except:
            return 0
    
    def get_total_messages(self):
        """Toplam mesaj sayısını döndür"""
        try:
            total = 0
            for sample in websocket_messages_total.collect():
                for s in sample.samples:
                    total += s.value
            return int(total)
        except:
            return 0
    
    def get_error_count(self):
        """Toplam hata sayısını döndür"""
        try:
            total = 0
            for sample in websocket_errors_total.collect():
                for s in sample.samples:
                    total += s.value
            return int(total)
        except:
            return 0

# Global metrics collector instance
metrics_collector = MetricsCollector()