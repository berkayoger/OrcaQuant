# Certbot Hızlı Kurulum

Sunucuda:
```bash
sudo apt-get update && sudo apt-get install -y snapd
sudo snap install core && sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
sudo certbot renew --dry-run
```
Yenileme Cron’u otomatik gelir; `systemctl list-timers` ile doğrulayın.

