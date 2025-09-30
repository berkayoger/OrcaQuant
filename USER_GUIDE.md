# OrcaQuant Kullanıcı Rehberi

## API Uç Noktaları
- `/api/market/price`: Basit fiyat sorgusu (`symbol=bitcoin&vs=usd`). CoinGecko'dan veri çeker, sonuçlar Redis ile cache'lenir.
- `/api/docs`: ReDoc arayüzü üzerinden OpenAPI dokümantasyonu.
- `/healthz` ve `/api/health`: Servis durum kontrolü.

## Şifre Sıfırlama
Uygulamanızda e-posta gönderimi gerekiyorsa `.env` içindeki SMTP alanlarını doldurun. `backend/services/emailer.py` modülü TLS destekli basit SMTP gönderimi yapar.

## Bildirimler
Slack veya Telegram bildirimleri için `.env` dosyasındaki `SLACK_WEBHOOK_URL`, `TELEGRAM_BOT_TOKEN` ve `TELEGRAM_CHAT_ID` alanlarını doldurun. `backend/services/notifier.py` bu entegrasyonları kullanır.
