#!/usr/bin/env bash
set -euo pipefail
TARGET_DIR="${1:-./backups}"
DB_PATH="${2:-./data/ytd_crypto.db}"
mkdir -p "$TARGET_DIR"
ts=$(date +"%Y%m%d_%H%M%S")
cp "$DB_PATH" "${TARGET_DIR}/ytd_crypto_${ts}.db"
echo "Backup: ${TARGET_DIR}/ytd_crypto_${ts}.db"
