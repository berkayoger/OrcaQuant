#!/usr/bin/env bash
set -euo pipefail

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/orcaquant"
DB_NAME="orcaquant_prod"

mkdir -p "$BACKUP_DIR"

# PostgreSQL - sıkıştırılmış özel format (-Fc)
pg_dump -Fc "$DB_NAME" > "$BACKUP_DIR/db_${DATE}.dump"

# Redis snapshot
redis-cli --rdb "$BACKUP_DIR/redis_${DATE}.rdb"

# 30 günden eski dosyaları temizle
find "$BACKUP_DIR" -type f -name "*.dump" -mtime +30 -delete
find "$BACKUP_DIR" -type f -name "*.rdb"  -mtime +30 -delete
