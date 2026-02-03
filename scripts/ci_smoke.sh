#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m pip install --upgrade pip

if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

if [ -f backend/requirements.txt ]; then
  pip install -r backend/requirements.txt
fi

if [ -f requirements-dev.txt ]; then
  pip install -r requirements-dev.txt
fi

pip install pytest

python -m pytest -q
