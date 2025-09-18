<div align="center">

# OrcaQuant

**AI Destekli Kripto Analiz ve Karar Destek Platformu**  
Güvenlik-sertleştirmesi etkin, Docker/K8s hazır, test ve CI/CD ile üretime uygun monorepo.

_Lisans: MIT • Dizinler: backend · frontend · deploy/k8s · migrations · tests · scripts_

</div>

---

## İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Mimari ve Dizin Yapısı](#mimari-ve-dizin-yapısı)
3. [Önkoşullar](#önkoşullar)
4. [Hızlı Başlangıç](#hızlı-başlangıç)
5. [Ortam Değişkenleri](#ortam-değişkenleri)
6. [Çalıştırma: Geliştirme / Docker / Staging / Production](#çalıştırma-geliştirme--docker--staging--production)
7. [Veritabanı Migrasyonları](#veritabanı-migrasyonları)
8. [Test, Lint ve Pre-commit](#test-lint-ve-pre-commit)
9. [WebSocket / Realtime](#websocket--realtime)
10. [Güvenlik (Özet)](#güvenlik-özet)
11. [Günlükleme, İzleme ve Sorun Giderme](#günlükleme-izleme-ve-sorun-giderme)
12. [Dağıtım (Nginx / K8s)](#dağıtım-nginx--k8s)
13. [Katkı Rehberi](#katkı-rehberi)
14. [Lisans](#lisans)

---

## Genel Bakış

OrcaQuant; Flask tabanlı bir API, yardımcı servisler ve hafif bir frontend katmanıyla kripto piyasalarındaki verileri toplayan, analiz eden ve kullanıcıya anlaşılır biçimde sunan bir platformdur. Depo, hızla yerelde çalıştırılabilecek şekilde tasarlanmış; Docker Compose ve Kubernetes örnekleri, test altyapısı ve güvenlik sertleştirmeleriyle üretim ortamına kadar uzanan uçtan uca bir kurulum sağlar.

> **WSGI giriş noktası (prod/staging):** `app.secure_app:app`  
> Bu sarmalayıcı CORS allowlist, global/login rate limit, HSTS/CSP gibi güvenlik başlıklarını katmanlı şekilde uygular. (Detay: aşağıdaki **Güvenlik (Özet)**)  

---

## Mimari ve Dizin Yapısı

Monorepo sade ve izlenebilir bir yapı izler:

```
.
├─ .github/               # CI/CD ve güvenlik iş akışları
├─ backend/               # Flask API, iş mantığı, servisler
├─ frontend/              # Basit HTML/JS arayüz (MPA)
├─ deploy/
│  └─ k8s/                # Kubernetes örnek manifestleri
├─ migrations/            # Flask-Migrate veritabanı değişiklikleri
├─ tests/                 # Pytest tabanlı testler
├─ scripts/               # Yardımcı scriptler (env, güvenlik, vb.)
├─ docker-compose.yml     # Yerel geliştirme
├─ docker-compose.staging.yml
├─ docker-compose.ci.yml
├─ WEBSOCKET_README.md    # Realtime/WebSocket notları
└─ README.md
```

> Not: Depodaki bazı yardımcı klasörler (örn. `infra/`, `docs/`, `storage/`) operasyonel araçlar ve örnek veriler içerir.

---

## Önkoşullar

- Python 3.10+ (venv önerilir)
- Docker & Docker Compose (isteğe bağlı ama önerilir)
- Redis ve bir SQL veritabanı (PostgreSQL önerilir)
- Node.js (sadece frontend geliştirme/derleme akışları için gerekebilir)

---

## Hızlı Başlangıç

En hızlı yol Docker Compose:

```bash
# 1) Bağımlılıklar ve servisler
cp .env.example .env  # anahtarları doldurun
docker-compose up --build
```

Yerel Python ortamıyla geliştirme:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # anahtarları doldurun

# DB hazırla (ilk kurulum)
flask db upgrade

# Uygulamayı başlat (geliştirme)
python wsgi.py
```

---

## Ortam Değişkenleri

Tüm değişkenler için **`.env.example`** dosyasına bakın. Üretimde sırları `.env` yerine bir gizli yönetim servisiyle sağlayın (örn. AWS Secrets Manager, Azure Key Vault).

Sık kullanılan anahtarlar:

| Değişken                  | Açıklama                                      |
|---------------------------|-----------------------------------------------|
| `FLASK_ENV`               | `development` / `staging` / `production`     |
| `DATABASE_URL`            | SQL bağlantısı (örn. Postgres DSN)            |
| `REDIS_URL`               | Redis bağlantısı                              |
| `SECRET_KEY`              | Flask gizli anahtarı                          |
| `JWT_SECRET_KEY`          | JWT için gizli anahtar                        |
| `CORS_ALLOWLIST`          | Virgülle ayrık origins                        |
| `RATE_LIMIT`              | Varsayılan hız limiti (örn. `200/minute`)     |
| `SECURE_SSL_REDIRECT`     | Prod’da HTTPS zorunluluğu (true/false)       |

> **İpucu:** `scripts/ensure_env_keys.py --apply` ile eksik anahtarları güvenli şekilde ekleyebilirsiniz (idempotent yaklaşım).

---

## Çalıştırma: Geliştirme / Docker / Staging / Production

### Geliştirme (yerel)
```bash
source .venv/bin/activate
export FLASK_ENV=development
python wsgi.py
```

### Docker (yerel)
```bash
docker-compose up --build
```

### Staging
```bash
docker-compose -f docker-compose.staging.yml up -d --build
```

### Production
**WSGI giriş noktası:** `app.secure_app:app`

```bash
# Örnek Gunicorn başlatma
gunicorn -c gunicorn.conf.py app.secure_app:app
```

**Nginx (özet)**
```nginx
server {
  listen 80;
  server_name your.domain;
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
  location /static/ {
    alias /path/to/frontend/;
  }
}
```

TLS için Let's Encrypt (`certbot`) önerilir.

---

## Veritabanı Migrasyonları

Flask-Migrate kullanılır:

```bash
# ilk kurulumdan sonra
flask db upgrade

# şema güncellemesi geliştirme aşamasında
flask db migrate -m "açıklayıcı mesaj"
flask db upgrade
```

> CI/CD’de otomatik `db upgrade` akışını staging/prod dağıtımı sırasında tetikleyebilirsiniz.

---

## Test, Lint ve Pre-commit

### Test
```bash
pytest -q
```

Coverage ayarları için `.coveragerc` mevcuttur. Test izolasyonu için fixture’lar ve dummy veriler `tests/` altındadır.

### Lint & Format
Proje `pre-commit` ile standart hale getirilmiştir:
```bash
pip install pre-commit
pre-commit install
pre-commit run -a
```

> Güvenlik taramaları ve sızmış sır kontrolleri için repo kökünde `gitleaks` yapılandırması mevcuttur.

---

## WebSocket / Realtime

Gerçek zamanlı veri akışı ve Socket/WS kullanım notları için **`WEBSOCKET_README.md`** dosyasına bakın.

---

## Güvenlik (Özet)

**WSGI Sarmalayıcı:** `app.secure_app:app` ile:
- **CORS allowlist** (sıkı origin kontrolü)
- **Rate limit**: global ve oturum açma uç noktaları için ayrı limitler
- **HTTP güvenlik başlıkları**: HSTS, katı CSP, `X-Frame-Options=DENY`, `X-Content-Type-Options=nosniff`

**Kimlik Doğrulama ve Token Yönetimi**
- Kısa ömürlü **access** (örn. 15 dk) ve **refresh** (örn. 30 gün) token
- **Token rotasyonu** ve **JTI revoke** (Redis kullanımı)
- **Argon2id** ile parola karması, pwned-password kontrolü

**Uygulama Güvenliği**
- Giriş denemelerinde kilitleme (brute-force)
- Girdi doğrulama ve XSS korunumu
- CSRF koruması (cookie tabanlı akışlarda HMAC+timestamp yaklaşımı)
- CI’da bağımlılık taraması ve SBOM üretimi

> Üretimde sırları **Secrets Manager/Key Vault** ile yönetin; `.env` yalnızca yerel geliştirme için.

---

## Günlükleme, İzleme ve Sorun Giderme

- **Günlükleme**: Yapılandırılabilir JSON/structured logging önerilir. Konu korelasyonu için `request-id`/`trace-id` ekleyin.
- **İzleme**: Prod ortamında temel sağlık uç noktaları (`/healthz`, `/readiness`) ve metrikler devreye alın.
- **Sorun Giderme**:
  - 4xx artışı → CORS/rate-limit/log girişlerini kontrol edin.
  - 5xx artışı → DB/Redis bağlantısı ve servis bağımlılıklarını doğrulayın.
  - Yük altında yavaş yanıt → DB indeksleri, cache katmanı ve N+1 sorgu kontrolleri.

---

## Dağıtım (Nginx / K8s)

### Nginx
Yukarıdaki üretim kesitini temel alarak TLS ve güvenlik başlıklarını (HSTS/CSP) etkinleştirin. Statik dosyaları `frontend/` üzerinden servis edin.

### Kubernetes (örnek)
`deploy/k8s/` altındaki manifestleri, ortamınıza göre `image`, `envFrom/secretRef` ve `resources` alanlarıyla uyarlayın.  
Health probe’lar için:
```yaml
livenessProbe:
  httpGet: { path: /healthz, port: 8000 }
readinessProbe:
  httpGet: { path: /readiness, port: 8000 }
```

---

## Katkı Rehberi

1. Issue açın veya mevcut bir issue’yu üzerine alın.
2. Feature/fix için bir branch açın.
3. Testleri ve pre-commit kontrollerini çalıştırın.
4. Açıklayıcı bir PR oluşturun (değişiklik kapsamı, test notları, riskler).

Kod standartlarını ve güvenlik kontrollerini korumak için küçük, odaklı PR’lar tercih edilir.

---

## Lisans

MIT — Telif hakkı (c) sahiplerine aittir. Ayrıntı için `LICENSE` dosyasına bakın.

---

### Hızlı Referans

- **Yerel:** `python wsgi.py` veya `docker-compose up --build`
- **WSGI (prod):** `gunicorn -c gunicorn.conf.py app.secure_app:app`
- **DB migrasyon:** `flask db upgrade`
- **Test:** `pytest -q`
- **WS/Realtime:** `WEBSOCKET_README.md`
