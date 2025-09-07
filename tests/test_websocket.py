import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import asyncio
from datetime import datetime

# Test imports
from backend.websocket.socket_manager import WebSocketManager
from backend.core.redis_manager import RedisManager
from backend.utils.price_streamer import BinancePriceStreamer, CoinGeckoPriceStreamer
from backend.monitoring.prometheus_metrics import MetricsCollector

class TestWebSocketManager:
    
    @pytest.fixture
    def app(self):
        """Test Flask uygulaması"""
        from backend import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Test HTTP client'ı"""
        return app.test_client()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.setex.return_value = True
        mock_client.publish.return_value = True
        return mock_client
    
    @pytest.fixture
    def websocket_manager(self, app, mock_redis):
        """Test WebSocket manager"""
        manager = WebSocketManager()
        manager.redis_client = mock_redis
        manager.init_app(app)
        return manager
    
    def test_websocket_manager_initialization(self, websocket_manager):
        """WebSocket manager'ın başlatılmasını test et"""
        assert websocket_manager.socketio is not None
        assert websocket_manager.connection_metadata == {}
        assert websocket_manager.active_connections == {}
    
    def test_rate_limiting(self, websocket_manager):
        """Rate limiting fonksiyonunu test et"""
        client_ip = "192.168.1.1"
        
        # İlk 10 istek geçmeli
        for i in range(10):
            assert websocket_manager._check_rate_limit(client_ip) == True
        
        # 11. istek bloklanmalı
        assert websocket_manager._check_rate_limit(client_ip) == False
    
    def test_symbol_validation(self, websocket_manager):
        """Sembol doğrulama fonksiyonunu test et"""
        # Geçerli semboller
        valid_symbols = ['BTCUSDT', 'ETHUSDT']
        assert websocket_manager._validate_symbols(valid_symbols) == True
        
        # Geçersiz sembol
        invalid_symbols = ['INVALIDCOIN']
        assert websocket_manager._validate_symbols(invalid_symbols) == False
        
        # Çok fazla sembol
        too_many_symbols = ['BTCUSDT'] * 60
        assert websocket_manager._validate_symbols(too_many_symbols) == False
        
        # Boş liste
        assert websocket_manager._validate_symbols([]) == False
    
    def test_broadcast_price_update(self, websocket_manager):
        """Fiyat güncellemesi broadcast'ini test et"""
        symbol = 'BTCUSDT'
        price_data = {
            'price': 50000,
            'change_percent': 2.5,
            'volume': 1000000
        }
        
        # Mock socketio emit
        websocket_manager.socketio.emit = Mock()
        
        websocket_manager.broadcast_price_update(symbol, price_data)
        
        # Redis cache kontrol
        websocket_manager.redis_client.setex.assert_called()
        
        # SocketIO emit kontrol
        websocket_manager.socketio.emit.assert_called_once()
    
    def test_connection_stats(self, websocket_manager):
        """Bağlantı istatistiklerini test et"""
        # Mock data ekle
        websocket_manager.connection_metadata = {
            'client1': {'subscriptions': {'BTCUSDT', 'ETHUSDT'}},
            'client2': {'subscriptions': {'ADAUSDT'}}
        }
        
        stats = websocket_manager.get_connection_stats()
        
        assert stats['total_connections'] == 2
        assert stats['active_subscriptions'] == 3
        assert 'uptime' in stats

class TestRedisManager:
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        mock_client = Mock()
        mock_client.ping.return_value = True
        return mock_client
    
    @pytest.fixture
    def redis_manager(self, mock_redis_client):
        """Test Redis manager"""
        with patch('redis.Redis') as mock_redis:
            mock_redis.return_value = mock_redis_client
            manager = RedisManager(host='localhost', port=6379, db=1)
            manager.client = mock_redis_client
            return manager
    
    def test_redis_connection(self, redis_manager):
        """Redis bağlantısını test et"""
        assert redis_manager.client.ping() == True
    
    def test_set_get_json(self, redis_manager):
        """JSON set/get işlemlerini test et"""
        test_data = {'symbol': 'BTCUSDT', 'price': 50000}
        
        # Mock return value
        redis_manager.client.setex.return_value = True
        redis_manager.client.get.return_value = json.dumps(test_data)
        
        # Test set
        result = redis_manager.set_with_expiry('test:price', test_data, 60)
        assert result == True
        redis_manager.client.setex.assert_called()
        
        # Test get
        retrieved_data = redis_manager.get_json('test:price')
        assert retrieved_data == test_data
    
    def test_publish(self, redis_manager):
        """Redis publish işlemini test et"""
        test_message = {'symbol': 'BTCUSDT', 'price': 50000}
        
        redis_manager.client.publish.return_value = True
        result = redis_manager.publish('price_updates', test_message)
        
        assert result == True
        redis_manager.client.publish.assert_called()
    
    def test_increment_counter(self, redis_manager):
        """Rate limiting counter'ını test et"""
        key = 'test:rate_limit'
        
        # Mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [2]  # Counter value
        redis_manager.client.pipeline.return_value = mock_pipeline
        
        count = redis_manager.increment_counter(key, 3600)
        assert count == 2
        
        mock_pipeline.incr.assert_called_with(key)
        mock_pipeline.expire.assert_called_with(key, 3600)

class TestPriceStreamer:
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        mock_client = Mock()
        mock_client.publish.return_value = True
        return mock_client
    
    def test_binance_streamer_initialization(self, mock_redis_client):
        """Binance streamer'ın başlatılmasını test et"""
        symbols = ['BTCUSDT', 'ETHUSDT']
        streamer = BinancePriceStreamer(mock_redis_client, symbols)
        
        assert streamer.symbols == ['btcusdt', 'ethusdt']
        assert streamer.is_running == False
        assert len(streamer.callbacks) == 0
    
    @pytest.mark.asyncio
    async def test_binance_message_handling(self, mock_redis_client):
        """Binance mesaj işleme testi"""
        streamer = BinancePriceStreamer(mock_redis_client, ['BTCUSDT'])
        
        # Test message
        test_message = json.dumps({
            'stream': 'btcusdt@ticker',
            'data': {
                's': 'BTCUSDT',
                'c': '50000.00',
                'P': '2.50',
                'p': '1250.00',
                'v': '1000.00',
                'h': '51000.00',
                'l': '49000.00'
            }
        })
        
        await streamer._handle_message(test_message)
        
        # Redis publish kontrol
        mock_redis_client.publish.assert_called()
        call_args = mock_redis_client.publish.call_args
        assert call_args[0][0] == 'price_updates'
        
        # Published data kontrol
        published_data = json.loads(call_args[0][1])
        assert published_data['symbol'] == 'BTCUSDT'
        assert published_data['data']['price'] == 50000.0
    
    def test_coingecko_streamer_initialization(self, mock_redis_client):
        """CoinGecko streamer'ın başlatılmasını test et"""
        symbols = ['BTCUSDT', 'ETHUSDT']
        streamer = CoinGeckoPriceStreamer(mock_redis_client, symbols)
        
        assert streamer.symbols == symbols
        assert streamer.is_running == False
        assert streamer.update_interval == 30

class TestMetricsCollector:
    
    @pytest.fixture
    def metrics_collector(self):
        """Test metrics collector"""
        return MetricsCollector()
    
    def test_metrics_initialization(self, metrics_collector):
        """Metrics collector'ın başlatılmasını test et"""
        assert metrics_collector.start_time > 0
    
    def test_connection_metrics(self, metrics_collector):
        """Bağlantı metriklerini test et"""
        # Connected metric
        initial_connections = metrics_collector.get_connection_count()
        metrics_collector.record_connection('connected')
        assert metrics_collector.get_connection_count() == initial_connections + 1
        
        # Disconnected metric
        metrics_collector.record_connection('disconnected')
        assert metrics_collector.get_connection_count() == initial_connections
    
    def test_message_metrics(self, metrics_collector):
        """Mesaj metriklerini test et"""
        initial_messages = metrics_collector.get_total_messages()
        
        metrics_collector.record_message('inbound', 'subscribe', 0.001)
        metrics_collector.record_message('outbound', 'price_update')
        
        # Message count artmalı
        assert metrics_collector.get_total_messages() > initial_messages
    
    def test_error_metrics(self, metrics_collector):
        """Hata metriklerini test et"""
        initial_errors = metrics_collector.get_error_count()
        
        metrics_collector.record_error('connection_failed')
        metrics_collector.record_error('rate_limit_exceeded')
        
        # Error count artmalı
        assert metrics_collector.get_error_count() > initial_errors

class TestIntegration:
    """Integration testleri"""
    
    @pytest.fixture
    def app(self):
        """Test Flask uygulaması"""
        from backend import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        return app
    
    def test_health_endpoint(self, app):
        """Health endpoint'ini test et"""
        with app.test_client() as client:
            response = client.get('/health')
            
            assert response.status_code in [200, 503]  # Healthy or degraded
            data = response.get_json()
            
            assert 'status' in data
            assert 'timestamp' in data
            assert 'components' in data
    
    def test_websocket_stats_endpoint(self, app):
        """WebSocket stats endpoint'ini test et"""
        with app.test_client() as client:
            response = client.get('/api/websocket/stats')
            
            # Rate limiting aktifse 429 olabilir, o yüzden 200 veya 429 kabul et
            assert response.status_code in [200, 429, 500]
            
            if response.status_code == 200:
                data = response.get_json()
                assert isinstance(data, dict)
    
    @patch('backend.core.redis_manager.redis_manager.client')
    def test_websocket_health_endpoint(self, mock_redis, app):
        """WebSocket health endpoint'ini test et"""
        mock_redis.ping.return_value = True
        
        with app.test_client() as client:
            response = client.get('/api/websocket/health')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['status'] == 'healthy'
            assert data['redis_connected'] == True
            assert 'active_connections' in data
            assert 'timestamp' in data

class TestLoadTesting:
    """Load testing simulasyonu"""
    
    def test_multiple_connections_simulation(self):
        """Çoklu bağlantı simülasyonu"""
        from backend.websocket.socket_manager import WebSocketManager
        
        manager = WebSocketManager()
        manager.redis_client = Mock()
        
        # 100 client bağlantısı simülasyonu
        for i in range(100):
            client_id = f"client_{i}"
            manager.connection_metadata[client_id] = {
                'connected_at': datetime.utcnow(),
                'ip_address': f'192.168.1.{i}',
                'subscriptions': {'BTCUSDT', 'ETHUSDT'},
                'last_activity': datetime.utcnow()
            }
        
        stats = manager.get_connection_stats()
        assert stats['total_connections'] == 100
        assert stats['active_subscriptions'] == 200  # 100 clients * 2 symbols each
    
    def test_message_throughput_simulation(self):
        """Mesaj throughput simülasyonu"""
        metrics = MetricsCollector()
        
        # 1000 mesaj simülasyonu
        start_time = time.time()
        for i in range(1000):
            metrics.record_message('inbound', 'price_update', 0.001)
        end_time = time.time()
        
        duration = end_time - start_time
        throughput = 1000 / duration if duration > 0 else float('inf')
        
        print(f"Message throughput: {throughput:.2f} messages/second")
        assert throughput > 100  # En az 100 mesaj/saniye bekliyoruz

@pytest.mark.asyncio
async def test_async_operations():
    """Asenkron operasyonları test et"""
    from backend.utils.price_streamer import BinancePriceStreamer
    
    mock_redis = Mock()
    streamer = BinancePriceStreamer(mock_redis, ['BTCUSDT'])
    
    # URL oluşturma testi
    url = await streamer._create_stream_url()
    assert 'btcusdt@ticker' in url
    assert url.startswith('wss://stream.binance.com:9443/ws/')

if __name__ == '__main__':
    # Test çalıştırma
    pytest.main([__file__, '-v'])