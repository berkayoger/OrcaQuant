# OrcaQuant WebSocket Implementation

## 🎯 Projeye Genel Bakış

OrcaQuant projesi için gerçek zamanlı kripto para fiyat güncellemeleri ve WebSocket entegrasyonu implementasyonu. Bu çözüm scalable, güvenli ve production-ready bir WebSocket altyapısı sağlar.

### ✨ Özellikler

- **Gerçek Zamanlı Fiyat Güncellemeleri**: Binance ve CoinGecko API'leri üzerinden
- **Scalable WebSocket Mimarisi**: Redis pub/sub ile horizontal scaling
- **Gelişmiş Güvenlik**: Rate limiting, IP filtering, ve input validation
- **Comprehensive Monitoring**: Prometheus metrics ve health checks
- **Production Ready**: Docker, load balancing, ve graceful shutdown desteği
- **Fallback Mekanizması**: Birden fazla veri kaynağı ile yüksek availability

## 🏗️ Mimari

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask/SocketIO │    │   Redis         │
│   (WebSocket    │◄──►│   Backend        │◄──►│   (Pub/Sub)     │
│    Client)      │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Price Streamers│
                       │   - Binance WS   │
                       │   - CoinGecko API│
                       └──────────────────┘
```

### 🔧 Bileşenler

1. **WebSocket Manager** (`backend/websocket/socket_manager.py`)
   - Client bağlantı yönetimi
   - Room-based subscriptions
   - Rate limiting ve güvenlik

2. **Redis Manager** (`backend/core/redis_manager.py`)
   - Redis connection pooling
   - Pub/sub messaging
   - Cache management

3. **Price Streamers** (`backend/utils/price_streamer.py`)
   - Binance WebSocket client
   - CoinGecko API fallback
   - Multi-source data aggregation

4. **Monitoring** (`backend/monitoring/prometheus_metrics.py`)
   - Prometheus metrics
   - Performance tracking
   - Health monitoring

## 🚀 Kurulum ve Konfigürasyon

### 1. Bağımlılıkları Yükleyin

```bash
pip install flask-socketio>=5.3.6 eventlet>=0.33.3 redis>=5.0.0 websocket-client>=1.6.0 python-socketio>=5.8.0 prometheus-client>=0.20.0
```

### 2. Environment Variables

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# WebSocket Configuration
WEBSOCKET_MAX_CONNECTIONS_PER_IP=10
WEBSOCKET_PING_TIMEOUT=60
WEBSOCKET_PING_INTERVAL=25

# Security
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Price Streaming
ENABLE_BINANCE_STREAM=true
ENABLE_COINGECKO_FALLBACK=true
```

### 3. Docker ile Başlatma

```bash
# Development
docker-compose up -d

# Production
FLASK_ENV=production docker-compose up -d
```

## 📡 API Endpoints

### WebSocket Events

#### Client → Server

```javascript
// Subscribe to price updates
socket.emit('subscribe_price', {
  symbols: ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
});

// Unsubscribe from price updates
socket.emit('unsubscribe_price', {
  symbols: ['BTCUSDT']
});

// Ping server
socket.emit('ping');
```

#### Server → Client

```javascript
// Price update notification
socket.on('price_update', (data) => {
  console.log('Price update:', data);
  // {
  //   symbol: 'BTCUSDT',
  //   data: {
  //     price: 50000.00,
  //     change: 1250.00,
  //     change_percent: 2.50,
  //     volume: 1000000.00,
  //     high_24h: 51000.00,
  //     low_24h: 49000.00,
  //     timestamp: '2025-01-01T12:00:00.000Z'
  //   },
  //   timestamp: '2025-01-01T12:00:00.000Z'
  // }
});

// Subscription confirmation
socket.on('subscription_confirmed', (data) => {
  console.log('Subscribed to:', data.symbols);
});

// Connection established
socket.on('connection_established', (data) => {
  console.log('Connected:', data);
});

// Pong response
socket.on('pong', (data) => {
  console.log('Pong:', data.timestamp);
});
```

### HTTP Endpoints

```bash
# Health check
GET /health
# Returns: { status, timestamp, components: { websocket, redis, price_streamer, ... } }

# WebSocket statistics
GET /api/websocket/stats
# Returns: { total_connections, active_subscriptions, uptime }

# WebSocket health
GET /api/websocket/health
# Returns: { status, redis_connected, active_connections, socketio_initialized, timestamp }

# Prometheus metrics
GET /metrics
# Returns: Prometheus formatted metrics
```

## 🎨 Frontend Entegrasyonu

### HTML Setup

```html
<!DOCTYPE html>
<html>
<head>
    <title>OrcaQuant Real-time Prices</title>
    <script src="https://cdn.socket.io/4.7.3/socket.io.min.js"></script>
</head>
<body>
    <div id="price-dashboard"></div>
    <script src="/static/js/websocket-client.js"></script>
</body>
</html>
```

### JavaScript Usage

```javascript
// Initialize WebSocket connection
const websocket = new OrcaQuantWebSocket('http://localhost:5000');

// Initialize price dashboard
const dashboard = new PriceDashboard('price-dashboard', websocket);

// Add event listeners
websocket.onConnectionChange = (isConnected) => {
    console.log('Connection status:', isConnected);
};

websocket.onPriceUpdate = (symbol, priceData) => {
    console.log(`${symbol}: $${priceData.price}`);
};

// Subscribe to symbols
websocket.subscribeToPrices(['BTCUSDT', 'ETHUSDT']);
```

### Custom Integration

```javascript
class CustomPriceHandler {
    constructor() {
        this.websocket = new OrcaQuantWebSocket();
        this.setupHandlers();
    }
    
    setupHandlers() {
        this.websocket.addPriceSubscriber('BTCUSDT', (priceData) => {
            this.updatePriceDisplay('BTCUSDT', priceData);
        });
        
        this.websocket.onConnectionChange = (isConnected) => {
            this.handleConnectionChange(isConnected);
        };
    }
    
    updatePriceDisplay(symbol, data) {
        // Custom price display logic
        const element = document.getElementById(`price-${symbol}`);
        if (element) {
            element.textContent = `$${data.price.toLocaleString()}`;
        }
    }
    
    handleConnectionChange(isConnected) {
        // Custom connection status handling
        const statusElement = document.getElementById('connection-status');
        statusElement.className = isConnected ? 'connected' : 'disconnected';
    }
}

// Initialize
const priceHandler = new CustomPriceHandler();
```

## 📊 Monitoring ve Analytics

### Prometheus Metrics

```bash
# Connection metrics
websocket_connections_total{status="connected"} 150
websocket_active_connections 45

# Message metrics
websocket_messages_total{direction="inbound",message_type="subscribe"} 200
websocket_message_processing_seconds_bucket{message_type="price_update",le="0.001"} 1500

# Error metrics
websocket_errors_total{error_type="rate_limit"} 5

# Price streaming metrics
price_updates_total{symbol="BTCUSDT",source="binance"} 5000
price_update_latency_seconds{symbol="BTCUSDT"} 0.05
```

### Health Monitoring

```bash
# Real-time monitoring
python scripts/websocket/monitor_websockets.py --interval 30

# One-time check
python scripts/websocket/monitor_websockets.py --once

# Custom API URL
python scripts/websocket/monitor_websockets.py --api-url http://your-server:5000
```

### Log Analysis

```bash
# WebSocket bağlantı logları
tail -f /var/log/orcaquant/websocket.log

# Price stream logları
tail -f /var/log/orcaquant/price_stream.log

# Error logları
tail -f /var/log/orcaquant/error.log | grep "WebSocket"
```

## 🧪 Testing

### Unit Tests

```bash
# Tüm WebSocket testleri
python -m pytest tests/test_websocket.py -v

# Belirli test grubu
python -m pytest tests/test_websocket.py::TestWebSocketManager -v

# Coverage ile
python -m pytest tests/test_websocket.py --cov=backend.websocket --cov-report=html
```

### Load Testing

```bash
# Basic load test (50 clients, 30 seconds)
python tests/load_test_websocket.py

# Custom load test
python tests/load_test_websocket.py --clients 100 --duration 60 --symbols BTCUSDT ETHUSDT ADAUSDT

# Save results
python tests/load_test_websocket.py --clients 200 --duration 120 --save --output load_test_results.json

# Test different server
python tests/load_test_websocket.py --url http://production-server:5000 --clients 50
```

### Manual Testing

```bash
# WebSocket demo sayfası
http://localhost:5000/websocket-demo

# Health check
curl http://localhost:5000/health | jq

# WebSocket stats
curl http://localhost:5000/api/websocket/stats | jq

# Prometheus metrics
curl http://localhost:5000/metrics
```

## 🔧 Production Deployment

### Docker Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - WEBSOCKET_MAX_CONNECTIONS=1000
    depends_on:
      - redis
    command: ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "wsgi:app"]
    
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
```

### Nginx Configuration

```nginx
upstream orcaquant_websocket {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name api.orcaquant.com;
    
    # WebSocket proxy
    location /socket.io/ {
        proxy_pass http://orcaquant_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket specific timeouts
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=websocket:10m rate=5r/s;
    limit_req zone=websocket burst=10 nodelay;
}
```

### Environment Variables (Production)

```bash
# Security
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key
REDIS_PASSWORD=your-redis-password

# Performance
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_RATE_LIMIT_PER_MINUTE=30
REDIS_MAX_MEMORY=2gb

# Monitoring
ENABLE_PROMETHEUS_METRICS=true
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn
```

## ⚡ Performance Tuning

### Redis Optimization

```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60

# Connection pooling
maxclients 10000
save 900 1
save 300 10
save 60 10000
```

### WebSocket Optimization

```python
# Gunicorn configuration
workers = 1  # EventLet ile tek worker kullan
worker_class = "eventlet"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
preload_app = True
```

### System Limits

```bash
# /etc/security/limits.conf
www-data soft nofile 65536
www-data hard nofile 65536

# /etc/sysctl.conf
net.core.somaxconn = 65536
net.ipv4.tcp_max_syn_backlog = 65536
```

## 🚨 Troubleshooting

### Common Issues

#### WebSocket Bağlantı Sorunları

```bash
# Service status check
systemctl status orcaquant-websocket

# Connection test
wscat -c ws://localhost:5000/socket.io/

# Port check
netstat -tlnp | grep :5000

# Log check
tail -f /var/log/orcaquant/websocket.log
```

#### Redis Bağlantı Sorunları

```bash
# Redis connectivity
redis-cli ping

# Memory usage
redis-cli info memory

# Active connections
redis-cli info clients

# Clear cache if needed
redis-cli flushdb
```

#### Performance Issues

```bash
# System resources
htop
free -h
df -h

# WebSocket connections
curl http://localhost:5000/api/websocket/stats

# Redis performance
redis-cli --latency-history -i 1

# Application logs
tail -f /var/log/orcaquant/application.log | grep "WebSocket\|Price"
```

### Debugging Tools

```python
# Debug mode için environment
FLASK_ENV=development
WEBSOCKET_DEBUG=true
LOG_LEVEL=DEBUG

# Test script
python -c "
from backend.websocket.socket_manager import websocket_manager
from backend.core.redis_manager import redis_manager
print('Redis:', redis_manager.client.ping())
print('WebSocket:', websocket_manager.socketio is not None)
"
```

### Monitoring Commands

```bash
# Real-time monitoring
python scripts/websocket/monitor_websockets.py --interval 10

# Health check loop
while true; do curl -s http://localhost:5000/health | jq '.status'; sleep 5; done

# Connection count
watch -n 1 'curl -s http://localhost:5000/api/websocket/stats | jq ".total_connections"'
```

## 📈 Performance Benchmarks

### Expected Performance Metrics

```yaml
Production Targets:
  max_concurrent_connections: 10,000
  connection_establishment_time: <100ms
  message_latency: <50ms
  throughput: 100,000 messages/second
  uptime: 99.9%
  
  redis:
    max_memory_usage: 2GB
    operation_latency: <1ms
    cache_hit_ratio: >95%
    
  system:
    cpu_usage: <70% average
    memory_usage: <80% average
    error_rate: <0.1%
```

### Load Test Results

```bash
# Example load test results
WebSocket Load Test Results
================================================================================
📊 Test Summary:
   Total Clients: 500
   Successful Connections: 498
   Failed Connections: 2
   Success Rate: 99.6%
   Test Duration: 60.00s

🔌 Connection Performance:
   Average Connection Time: 0.085s
   Min Connection Time: 0.045s
   Max Connection Time: 0.150s

📨 Message Performance:
   Total Messages Received: 150,000
   Messages per Second: 2,500.00
   Average Messages per Client: 301.2

🎯 Performance Assessment:
   ✅ Connection Success Rate: Excellent (99.6%)
   ✅ Connection Time: Excellent (0.085s)
   ✅ Message Throughput: Excellent (2500.00/s)
   ✅ Error Rate: Excellent (0.004)
```

## 🔐 Security Best Practices

### Production Security Checklist

- [ ] HTTPS/WSS certificates configured
- [ ] Rate limiting enabled per IP and per user
- [ ] Connection limits enforced
- [ ] Input validation for all WebSocket messages
- [ ] Redis authentication enabled
- [ ] Firewall rules configured
- [ ] DDoS protection enabled
- [ ] Regular security audits
- [ ] Error messages don't expose sensitive info
- [ ] Logging configured for security events

### Security Configuration

```python
# Rate limiting
WEBSOCKET_MAX_CONNECTIONS_PER_IP = 5
API_RATE_LIMIT_PER_MINUTE = 60
PRICE_SUBSCRIPTION_LIMIT = 50

# Connection security
WEBSOCKET_PING_TIMEOUT = 60
WEBSOCKET_MAX_MESSAGE_SIZE = 10000
ENABLE_IP_BLOCKING = True

# Redis security
REDIS_PASSWORD = "strong-password"
REDIS_REQUIRE_AUTH = True
REDIS_DISABLE_DANGEROUS_COMMANDS = True
```

## 📝 API Documentation

Tam API dokümantasyonu için:
- Swagger UI: `http://localhost:5000/swagger`
- OpenAPI JSON: `http://localhost:5000/openapi.json`
- WebSocket Demo: `http://localhost:5000/websocket-demo`

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/websocket-enhancement`
3. Run tests: `python -m pytest tests/test_websocket.py`
4. Commit changes: `git commit -am 'Add WebSocket enhancement'`
5. Push to branch: `git push origin feature/websocket-enhancement`
6. Create Pull Request

## 📄 License

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakınız.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: Bu README ve kod içi dokümantasyon
- **Monitoring**: `python scripts/websocket/monitor_websockets.py --help`

---

**Not**: Bu implementasyon production-ready olup, yüksek trafikli ortamlarda test edilmiştir. Herhangi bir sorun durumunda monitoring script'lerini kullanarak sistem durumunu kontrol edebilirsiniz.