# OrcaQuant Production Playbook

Bu doküman, OrcaQuant uygulamasını üretim ortamında (prod-grade) devreye alırken izlenmesi gereken adımları açıklar. Aşamalar güvenlik → performans → kullanıcı deneyimi → sürdürülebilirlik öncelik sırasına göre düzenlenmiştir. Tüm komutlar Ubuntu 20.04+ (veya uyumlu) üzerinde, Nginx + Gunicorn + systemd + Celery + Redis + PostgreSQL bileşenleri için hazırlanmıştır.

> **Not:** Aksi belirtilmedikçe komutlar kök dizin `/opt/orcaquant` altında çalıştırılmalıdır ve `deployer` adlı sudo yetkili, şifre ile girişe kapatılmış bir kullanıcı varsayılmıştır.

## 1. Altyapı ve Sunucu Hazırlıkları

### 1.1 Sunucu konfigürasyonu (OS + paketler)
```bash
# root olmayan sudo kullanıcı
adduser deployer && usermod -aG sudo deployer

# SSH anahtarı
rsync -avz ~/.ssh/authorized_keys deployer@SERVER:/home/deployer/.ssh/

# Şifreli girişi kapat (sshd_config)
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Temel paketler
sudo apt update
sudo apt install -y build-essential curl git ufw fail2ban nginx python3-pip python3-venv \
                    postgresql postgresql-contrib redis-server

# Docker Engine + Compose plugin
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker deployer

# Certbot (Let’s Encrypt, snap yöntemi)
sudo apt-get install -y snapd
sudo snap install core && sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot
```

### 1.2 Güvenlik (UFW + Fail2ban)
```bash
# UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow http
sudo ufw allow https
sudo ufw enable

# Fail2ban temel SSH jail
sudo tee /etc/fail2ban/jail.d/sshd.local >/dev/null <<'JAIL'
[sshd]
enabled = true
backend = systemd
maxretry = 5
findtime = 10m
bantime = 1h
JAIL
sudo systemctl restart fail2ban
```

## 2. Depo & Ortam Değişkenleri
```bash
# Projeyi yerleştir
sudo mkdir -p /opt/orcaquant && sudo chown -R deployer: /opt/orcaquant
cd /opt/orcaquant
git clone https://github.com/berkayoger/OrcaQuant.git .
git checkout production || true

# .env
cp .env.example .env

# Güçlü anahtarlar (örnek)
python3 - <<'PY'
import secrets; print("SECRET_KEY="+secrets.token_urlsafe(64))
print("JWT_SECRET_KEY="+secrets.token_urlsafe(64))
PY
# Çıktıları .env dosyasına ekleyin
```

**Zorunlu anahtarlar / değişkenler:**
- `SECRET_KEY`, `JWT_SECRET_KEY`: güçlü ve rastgele değerler.
- `DATABASE_URL` (ör. `postgresql://orcaquant:PASS@localhost:5432/orcaquant_prod`).
- `REDIS_URL` (ör. `redis://:PASSWORD@localhost:6379/0`).
- Opsiyonel uyarı kanalları: SMTP/Slack/Telegram webhook’ları.
- `CORS_ORIGINS`, `ALLOWED_ORIGINS`, `APP_ENV=production`, `SERVER_NAME`, `PREFERRED_URL_SCHEME=https`.
- `SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": true, "pool_recycle": 1800}`.

Varsa aşağıdaki betiği çalıştırın:
```bash
python3 scripts/ensure_env_keys.py --apply || true
```

## 3. Veritabanı ve Migrasyonlar

### 3.1 PostgreSQL
```bash
sudo -u postgres psql -c "CREATE USER orcaquant WITH PASSWORD 'STRONG_PASS';"
sudo -u postgres psql -c "CREATE DATABASE orcaquant_prod OWNER orcaquant;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE orcaquant_prod TO orcaquant;"
```

### 3.2 Flask-Migrate
```bash
export FLASK_APP=backend/wsgi.py
flask db init   || true
flask db migrate -m "initial production" || true
flask db upgrade
```

## 4. Redis Konfigürasyonu

`/etc/redis/redis.conf` içerisine önerilen ayarlar:
```
requirepass YOUR_REDIS_PASSWORD
maxmemory 1gb
maxmemory-policy allkeys-lru
appendonly yes
```

Ardından:
```bash
sudo systemctl restart redis-server
```

## 5. Uygulama Servis Yönetimi (systemd)

### 5.1 Gunicorn ayarları
`/opt/orcaquant/gunicorn.conf.py`:
```python
import multiprocessing, os
bind = "127.0.0.1:5000"
workers = int(os.getenv("GUNICORN_WORKERS", (multiprocessing.cpu_count() * 2) + 1))
threads = int(os.getenv("GUNICORN_THREADS", 2))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")  # Socket.IO tam WS için gevent* seçilebilir
timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
```

`backend/wsgi.py` içinde uygulama yaratıldıktan hemen sonra:
```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
```

### 5.2 systemd unit dosyaları

`/etc/systemd/system/orcaquant.service`
```
[Unit]
Description=OrcaQuant Gunicorn App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/orcaquant
EnvironmentFile=/opt/orcaquant/.env
ExecStart=/usr/bin/env bash -lc 'exec gunicorn -c /opt/orcaquant/gunicorn.conf.py "backend:create_app()"'
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/orcaquant-celery.service`
```
[Unit]
Description=OrcaQuant Celery Worker
After=network.target redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/orcaquant
EnvironmentFile=/opt/orcaquant/.env
ExecStart=/usr/bin/env bash -lc 'exec celery -A backend.tasks.celery_tasks worker \
  --loglevel=INFO --concurrency=4 \
  --max-tasks-per-child=200 --max-memory-per-child=300000 --prefetch-multiplier=1'
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/orcaquant-beat.service`
```
[Unit]
Description=OrcaQuant Celery Beat
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/orcaquant
EnvironmentFile=/opt/orcaquant/.env
ExecStart=/usr/bin/env bash -lc 'exec celery -A backend.tasks.celery_tasks beat --loglevel=INFO'
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Servisleri etkinleştirin:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now orcaquant orcaquant-celery orcaquant-beat
sudo systemctl status orcaquant --no-pager
```

## 6. Nginx Reverse Proxy ve SSL

### 6.1 Rate limit bölgesi (global)
`/etc/nginx/conf.d/ratelimit.conf`
```
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

### 6.2 Gzip ve proxy snippet’leri
`/etc/nginx/snippets/gzip.conf`
```
gzip on;
gzip_types text/plain text/css application/json application/javascript application/xml application/rss+xml image/svg+xml;
gzip_min_length 1024;
```

`/etc/nginx/snippets/proxy-params.conf`
```
proxy_set_header Host               $host;
proxy_set_header X-Real-IP          $remote_addr;
proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto  $scheme;
proxy_read_timeout 75s;
proxy_send_timeout 75s;
```

### 6.3 Site konfigürasyonu
`/etc/nginx/sites-available/orcaquant`
```
map $http_upgrade $connection_upgrade {
  default upgrade;
  ''      close;
}

server {
  listen 80;
  server_name your-domain.com www.your-domain.com;
  location /.well-known/acme-challenge/ { root /var/www/html; }
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name your-domain.com www.your-domain.com;

  ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;

  # Güvenlik başlıkları
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
  add_header X-Content-Type-Options nosniff always;
  add_header X-Frame-Options DENY always;
  add_header Referrer-Policy no-referrer-when-downgrade always;
  add_header X-XSS-Protection "1; mode=block" always;
  # CSP'yi önce Report-Only deneyip nonce/sha’ya geçin
  add_header Content-Security-Policy-Report-Only "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' https:; upgrade-insecure-requests" always;

  # API
  location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://127.0.0.1:5000;
    include /etc/nginx/snippets/proxy-params.conf;
  }

  # WebSocket / Socket.IO
  location /socket.io/ {
    proxy_pass http://127.0.0.1:5000/socket.io/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }

  # Genel uygulama (SPA değilse standart proxy)
  location / {
    proxy_pass http://127.0.0.1:5000;
    include /etc/nginx/snippets/proxy-params.conf;
  }

  # Statikler
  location /static/ {
    alias /opt/orcaquant/frontend/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
  }

  client_max_body_size 10M;
  include /etc/nginx/snippets/gzip.conf;
  access_log /var/log/nginx/orcaquant.access.log;
  error_log  /var/log/nginx/orcaquant.error.log;
}
```

Sanal hostu etkinleştirin ve SSL sertifikasını alın:
```bash
sudo ln -s /etc/nginx/sites-available/orcaquant /etc/nginx/sites-enabled/orcaquant
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
sudo certbot renew --dry-run
```

## 7. İzleme ve Loglama

### 7.1 Healthcheck
Uygulama içinde `/healthz` (veya `/api/health`) uç noktası sağlayın ve:
```bash
curl -f http://localhost/healthz
```

### 7.2 Log rotasyonu
`/etc/logrotate.d/orcaquant`
```
/var/log/orcaquant/*.log {
  daily
  rotate 52
  missingok
  compress
  delaycompress
  notifempty
  create 0644 www-data www-data
  postrotate
    systemctl restart orcaquant.service >/dev/null 2>&1 || true
    systemctl restart orcaquant-celery.service >/dev/null 2>&1 || true
    systemctl restart orcaquant-beat.service  >/dev/null 2>&1 || true
  endscript
}
```

> İleri seviye: Prometheus node_exporter, uygulama metrikleri (`/metrics`) ve Alertmanager entegrasyonunu değerlendirin.

## 8. Yedekleme ve Felaket Kurtarma (DR)

`/opt/orcaquant/backup.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/orcaquant"
DB_NAME="orcaquant_prod"
mkdir -p "$BACKUP_DIR"
pg_dump -Fc "$DB_NAME" > "$BACKUP_DIR/db_${DATE}.dump"
redis-cli --rdb "$BACKUP_DIR/redis_${DATE}.rdb"
find "$BACKUP_DIR" -type f -name "*.dump" -mtime +30 -delete
find "$BACKUP_DIR" -type f -name "*.rdb"  -mtime +30 -delete
```

Kurulum ve zamanlama:
```bash
sudo install -m 0755 -D /opt/orcaquant/backup.sh /opt/orcaquant/backup.sh
( crontab -l 2>/dev/null; echo "0 2 * * * /opt/orcaquant/backup.sh" ) | crontab -
```

**DR kontrol listesi:**
- Parola/anahtar kasası (KMS veya secrets manager).
- Geri yükleme adımlarını belgeleyin (`pg_restore`, Redis RDB yükleme).
- Düzenli geri yükleme testleri (en az aylık).

## 9. Performans Optimizasyonu
- Redis cache: sıcak veri için TTL ayarlayın, `allkeys-lru` ve kritik hesaplamalar için cache katmanı ekleyin.
- Veritabanı: indeksleri gözden geçirin (`EXPLAIN ANALYZE`), N+1 sorguları ortadan kaldırın, `pool_pre_ping=True`.
- Statik içerik: uzun süreli immutable cache ve içerik hash’leri uygulayın.
- Gunicorn: `(2 * CPU) + 1` worker, `threads=2` — gerçek trafik verilerine göre ayarlayın.

## 10. Deployment & CI/CD

### 10.1 Docker Compose (opsiyonel)
```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose ps
```

### 10.2 GitHub Actions iskeleti
```yaml
name: Deploy to Production
on:
  push:
    branches: [main, production]

jobs:
  build_and_push_image:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - run: docker buildx create --use
      - run: docker buildx build -t ghcr.io/${{ github.repository }}:${{ github.sha }} -f backend/Dockerfile --push .

  deploy_prod:
    runs-on: ubuntu-latest
    needs: [build_and_push_image]
    steps:
      - name: SSH deploy
        run: |
          ssh -o StrictHostKeyChecking=no ${{ secrets.PROD_SSH }} '
            set -euo pipefail
            cd /opt/orcaquant
            git fetch --all
            git reset --hard origin/production
            pip3 install -r backend/requirements.txt --upgrade
            flask db upgrade
            sudo systemctl restart orcaquant orcaquant-celery orcaquant-beat
            curl -f http://localhost/healthz
          '
```

> Sağlık ucu `/api/health` ise ilgili adresi kullanın. Docker kullanıyorsanız CI adımlarını Compose’a uyarlayın.

## 11. Dış Servis Entegrasyonları
- **CoinGecko:** API anahtarı ve kota yönetimini takip edin; hata durumunda cache/son başarılı değeri fallback olarak kullanın.
- **E-posta:** SMTP App-Password (TLS 587) ile hata/uptime bildirimleri gönderin.
- **Webhook:** Slack/Telegram kanalları ile deploy, hata ve oran limit uyarılarını otomatikleştirin.

## 12. Test & QA
```bash
# Unit & coverage
pytest --cov=backend --cov=frontend tests/

# Integration
pytest tests/integration/

# Smoke
curl -f http://localhost/healthz

# Yük testi (basit)
wrk -t4 -c100 -d30s http://your-domain.com/
```

## 13. API Dokümantasyonu
- OpenAPI/Swagger: `/api/docs` (mevcutsa) üzerinden yayınlayın.
- Versiyonlama: kırıcı değişikliklerde `/api/v1/*` → `/api/v2/*` yaklaşımını izleyin.
- İstemci SDK: temel Python/JS istemci örnekleri sağlayın.

## 14. Legal & Compliance
- KVKK/GDPR: açık rıza, aydınlatma metni, veri saklama süreleri.
- Gizlilik Politikası ve Kullanım Şartları: UI içinde görünür bağlantılar.
- Risk Uyarısı: "Finansal tavsiye değildir" ibaresini görünür bir konuma yerleştirin.

