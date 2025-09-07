import os
import redis
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis bağlantı ve işlemlerini yönetir"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None, 
                 max_connections=100, socket_timeout=30):
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        self.client = redis.Redis(connection_pool=self.pool)
        self._lock = threading.Lock()
        
        # Connection health check (do not fail hard in test/sandbox)
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Redis bağlantısını test eder. Test/CI ortamında hata fırlatmaz."""
        # Skip strict failures during tests or when explicitly disabled
        skip_strict = bool(
            os.getenv("PYTEST_CURRENT_TEST") or
            os.getenv("DISABLE_REDIS") or
            os.getenv("SKIP_REDIS_PING")
        )
        try:
            self.client.ping()
            logger.info("Redis connection established successfully")
            return True
        except redis.ConnectionError as e:
            # In restricted sandboxes, socket ops may be blocked. Don't raise.
            level = logging.WARNING if skip_strict else logging.ERROR
            logger.log(level, f"Redis connection failed: {e}. Running in degraded mode.")
            return False
    
    def set_with_expiry(self, key: str, value: Any, expiry_seconds: int = 300) -> bool:
        """Expiry ile key-value set eder"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            return self.client.setex(key, expiry_seconds, value)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[Dict]:
        """JSON formatında value döndürür"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    def publish(self, channel: str, message: Any) -> bool:
        """Redis pub/sub'a mesaj publish eder"""
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            
            self.client.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"Redis publish error for channel {channel}: {e}")
            return False
    
    def increment_counter(self, key: str, expiry_seconds: int = 3600) -> int:
        """Rate limiting için counter artırır"""
        try:
            with self._lock:
                pipe = self.client.pipeline()
                pipe.incr(key)
                pipe.expire(key, expiry_seconds)
                result = pipe.execute()
                return result[0]
        except Exception as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return 0
    
    def get_connection_stats(self) -> Dict:
        """Redis bağlantı istatistiklerini döndürür"""
        try:
            info = self.client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {}
    
    def cleanup_expired_keys(self, pattern: str = "temp:*"):
        """Geçici anahtarları temizler"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"Cleaned up {len(keys)} expired keys")
        except Exception as e:
            logger.error(f"Redis cleanup error: {e}")
    
    def close(self):
        """Redis bağlantısını kapatır"""
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Redis close error: {e}")

# Global instance
redis_manager = RedisManager()
