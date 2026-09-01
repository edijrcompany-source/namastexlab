#!/usr/bin/env bash
# PÓS-REBOOT — sobe os CONTAINERS de verdade (objetivo literal do projeto).
# Pré-requisito: WSL instalado (feito) + Windows reiniciado.
# Uso:  bash scripts/pos-reboot.sh
set -euo pipefail
DOCKER="/c/Program Files/Docker/Docker/resources/bin/docker.exe"
[ -x "$DOCKER" ] || DOCKER="docker"

echo "▶ 1/4 — iniciando Docker Desktop (aguarde 'Engine running')..."
( cmd //c start "" "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe" ) 2>/dev/null || true
for i in $(seq 1 36); do
  if "$DOCKER" info > /dev/null 2>&1; then echo "   engine OK (${i}0s aprox)"; break; fi
  sleep 10
done
"$DOCKER" info > /dev/null 2>&1 || { echo "❌ engine não subiu — abra o Docker Desktop manualmente e rode de novo"; exit 1; }

echo "▶ 2/4 — docker compose up --build (agent-api + quote-api + postgres)..."
"$DOCKER" compose up --build -d

echo "▶ 3/4 — aguardando health do agent-api..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8001/health > /dev/null 2>&1; then break; fi
  sleep 4
done
curl -sf http://localhost:8001/health && echo && echo "▶ 4/4 — containers no ar:" && "$DOCKER" compose ps

echo ""
echo "✅ CONTAINERS SUBINDOS — teste: curl -X POST http://localhost:8001/conversations"
echo "   (front opcional: cd apps/web && pnpm dev → :3000)"
