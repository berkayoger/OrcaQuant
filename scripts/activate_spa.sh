#!/usr/bin/env bash
# OrcaQuant SPA Activation Script
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "🚀 OrcaQuant SPA aktivasyonu başlıyor..."

# Check if frontend-spa exists
if [ ! -d "frontend-spa" ]; then
  echo "❌ frontend-spa dizini bulunamadı!"
  echo "Önce patch'i çalıştırdığınızdan emin olun."
  exit 1
fi

# Backup existing frontend
if [ -d "frontend" ]; then
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  echo "📦 Mevcut frontend yedekleniyor: frontend-legacy-$TIMESTAMP"
  mv frontend "frontend-legacy-$TIMESTAMP"
fi

# Activate SPA
echo "🔄 SPA aktivasyonu..."
mv frontend-spa frontend

echo "📦 Dependencies kuruluyor..."
cd frontend
npm install

echo "🔧 Environment dosyası hazırlanıyor..."
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "✏️  .env dosyasını ihtiyacınıza göre düzenleyin"
fi

echo ""
echo "✅ OrcaQuant SPA başarıyla aktif edildi!"
echo ""
echo "📋 Sonraki adımlar:"
echo "   1. Backend dependencies: pip install -r backend/requirements.txt"
echo "   2. Backend'i çalıştır: python run_with_socketio.py"
echo "   3. Frontend'i çalıştır: cd frontend && npm run dev"
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "🔌 Backend: http://localhost:5000"
echo ""
