from functools import wraps
from flask import request, jsonify, g
import time
import hashlib
from typing import Dict, Optional
import logging
from .redis_manager import redis_manager

logger = logging.getLogger(__name__)

class RateLimiter:
    """WebSocket bağlantıları için gelişmiş rate limiter"""
    
    def __init__(self):
        self.redis = redis_manager.client
        self.default_limits = {
            'websocket_connections': {'count': 5, 'window': 60},  # 5 bağlantı/dakika
            'price_subscriptions': {'count': 50, 'window': 60},   # 50 subscription/dakika
            'api_calls': {'count': 100, 'window': 60}             # 100 API call/dakika
        }
    
    def _get_client_key(self, identifier: str, limit_type: str) -> str:
        """Client için unique key oluşturur"""
        hash_input = f"{identifier}:{limit_type}".encode()
        hash_key = hashlib.md5(hash_input).hexdigest()
        return f"rate_limit:{limit_type}:{hash_key}"
    
    def check_limit(self, identifier: str, limit_type: str, 
                   custom_limit: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Rate limit kontrolü yapar"""
        
        limit_config = custom_limit or self.default_limits.get(limit_type)
        if not limit_config:
            return True, {}
        
        key = self._get_client_key(identifier, limit_type)
        current_time = int(time.time())
        window_start = current_time - limit_config['window']
        
        try:
            # Current window'daki istekleri al
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)  # Eski kayıtları sil
            pipe.zcard(key)  # Mevcut istek sayısı
            pipe.expire(key, limit_config['window'])
            results = pipe.execute()
            
            current_count = results[1]
            
            if current_count >= limit_config['count']:
                # Limit aşıldı
                return False, {
                    'limit_exceeded': True,
                    'current_count': current_count,
                    'limit': limit_config['count'],
                    'reset_time': window_start + limit_config['window']
                }
            
            # Yeni isteği kaydet
            self.redis.zadd(key, {current_time: current_time})
            
            return True, {
                'limit_exceeded': False,
                'current_count': current_count + 1,
                'limit': limit_config['count'],
                'remaining': limit_config['count'] - current_count - 1
            }
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Redis hatası durumunda işleme devam et
            return True, {}
    
    def websocket_limit(self, custom_limit: Optional[Dict] = None):
        """WebSocket bağlantıları için rate limit decorator"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
                
                allowed, info = self.check_limit(
                    client_ip, 
                    'websocket_connections', 
                    custom_limit
                )
                
                if not allowed:
                    logger.warning(f"WebSocket rate limit exceeded for {client_ip}")
                    return False  # WebSocket bağlantısını reddet
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def api_limit(self, custom_limit: Optional[Dict] = None):
        """API endpointleri için rate limit decorator"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
                
                allowed, info = self.check_limit(
                    client_ip, 
                    'api_calls', 
                    custom_limit
                )
                
                if not allowed:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'details': info
                    }), 429
                
                g.rate_limit_info = info
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# Global instance
rate_limiter = RateLimiter()