# Troubleshooting

## 502 / Bad Gateway
- `systemctl status orcaquant` ve `journalctl -u orcaquant -f` ile servis loglarını inceleyin.
- `nginx -t` komutu ile ters proxy yapılandırmasını doğrulayın.

## WebSocket bağlantısı düşüyor
- Nginx konfigürasyonunda `Upgrade` ve `Connection` başlıklarının ayarlandığından emin olun.
- Yüksek trafik senaryolarında `gunicorn.conf.py` içinde `worker_class` değerini `geventwebsocket.gunicorn.workers.GeventWebSocketWorker` olarak değiştirin.

## Veritabanı "stale connections"
- `.env` içinde `SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": true, "pool_recycle": 1800}` kullanın.

## Redis bellek doluyor
- `redis-cli info memory` ile kullanım durumunu gözlemleyin.
- `maxmemory-policy allkeys-lru` gibi bir policy uygulayın.

## CoinGecko rate limit
- `.env` dosyasında `COINGECKO_RPS` değerini kota limitlerinize göre güncelleyin.
- `COINGECKO_CACHE_TTL` ile yanıtları önbelleğe alın.
