# OrcaQuant Production Playbook (Nginx + Gunicorn + systemd)

Güvenlik → Performans → UX → Sürdürülebilirlik sırasıyla üretim ortamı için özet rehber. Örnekler Ubuntu 20.04+ içindir.

## 1. Altyapı ve Güvenlik
```bash
# Yetkili kullanıcı
adduser deployer && usermod -aG sudo deployer
# SSH anahtarları, PasswordAuthentication no
systemctl restart ssh

apt update
apt install -y build-essential curl git ufw fail2ban nginx python3-pip python3-venv \
  postgresql postgresql-contrib redis-server docker.io docker-compose-plugin

# Docker kullanıcı ekleme
usermod -aG docker deployer

# Certbot
snap install core && snap refresh core
snap install --classic certbot
ln -sf /snap/bin/certbot /usr/bin/certbot

# UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow http
ufw allow https
ufw enable

# Fail2ban (SSH)
tee /etc/fail2ban/jail.d/sshd.local >/dev/null <<'JAIL'
[sshd]
enabled = true
backend = systemd
maxretry = 5
findtime = 10m
bantime  = 1h
JAIL
systemctl restart fail2ban
```

## 2. Repo ve .env
```bash
sudo mkdir -p /opt/orcaquant && sudo chown -R $USER: /opt/orcaquant
cd /opt/orcaquant
git clone https://github.com/berkayoger/OrcaQuant.git .
cp .env.example .env
python3 - <<'PY'
import secrets
print("SECRET_KEY=" + secrets.token_urlsafe(64))
print("JWT_SECRET_KEY=" + secrets.token_urlsafe(64))
PY
```
`.env` içinde `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, `SQLALCHEMY_ENGINE_OPTIONS` gibi değerleri güncelleyin.

## 3. PostgreSQL ve Migrasyonlar
```bash
sudo -u postgres psql -c "CREATE USER orcaquant WITH PASSWORD 'STRONG_PASS';"
sudo -u postgres psql -c "CREATE DATABASE orcaquant_prod OWNER orcaquant;"
export FLASK_APP=backend/wsgi.py
flask db upgrade
```

## 4. Redis
`/etc/redis/redis.conf` önerileri:
```
requirepass YOUR_REDIS_PASSWORD
maxmemory 1gb
maxmemory-policy allkeys-lru
appendonly yes
```
Restart: `systemctl restart redis-server`

## 5. Gunicorn & systemd
`gunicorn.conf.py` prod ayarlarını içerir (localhost:5000, (2*CPU)+1 workers, gthread). Hizmetler:
```bash
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now orcaquant.service orcaquant-celery.service orcaquant-beat.service
sudo systemctl status orcaquant.service --no-pager
```

## 6. Nginx + SSL
- Rate limit: `deploy/nginx/conf.d/ratelimit.conf`
- Snippets: `deploy/nginx/snippets/*`
- Site config: `deploy/nginx/orcaquant.conf`
```bash
sudo cp deploy/nginx/conf.d/ratelimit.conf /etc/nginx/conf.d/
sudo cp deploy/nginx/snippets/*.conf /etc/nginx/snippets/
sudo cp deploy/nginx/orcaquant.conf /etc/nginx/sites-available/orcaquant.conf
sudo ln -s /etc/nginx/sites-available/orcaquant.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d orcaquant.example.com -d www.orcaquant.example.com
sudo certbot renew --dry-run
```

## 7. Healthcheck, Log Rotate, Backup
```bash
curl -f http://localhost/healthz
curl -f http://localhost/api/health
sudo cp deploy/logrotate/orcaquant /etc/logrotate.d/orcaquant
sudo install -m 0755 deploy/scripts/backup.sh /opt/orcaquant/backup.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/orcaquant/backup.sh") | crontab -
```

## 8. CI/CD Özeti
- Docker image'ı build & push (`.github/workflows/deploy.yml`).
- Sunucuda image pull + `docker compose up -d` + `flask db upgrade` + `/healthz` + `/api/health` kontrolleri.
- Güvenlik taramaları: CodeQL, pip-audit, Trivy.

## 9. Performans & Güvenlik İpuçları
- Redis cache katmanı; TTL tanımlayın.
- SQL index kontrolleri, `EXPLAIN ANALYZE`, N+1 temizlikleri.
- CSP'yi `Report-Only` → nonce/sha256 ile sıkılaştırma.
- JWT erişim 15 dk / refresh 7 gün; döngüsel secret yenileme (`scripts/rotate_jwt_secret.py`).

## 10. Sorun Giderme
- 502/Bad Gateway → `journalctl -u orcaquant -f`, `nginx -t`.
- WebSocket kopmaları → Nginx `Upgrade/Connection` başlıklarını ve `worker_class` ayarını kontrol edin.
- DB stale connections → `pool_pre_ping=True`, `pool_recycle=1800`.
- Redis bellek → `redis-cli INFO memory`, `maxmemory-policy allkeys-lru`.

## 11. Monitoring Stack (Opsiyonel)
```bash
cd deploy/monitoring
docker compose -f docker-compose.monitoring.yml up -d
# Prometheus http://SERVER:9090, Grafana http://SERVER:3000 (admin/admin)
```
