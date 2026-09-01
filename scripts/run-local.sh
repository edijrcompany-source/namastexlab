#!/usr/bin/env bash
# Sobe o sistema SEM Docker: quote-api (legado) + agent-api (nosso Agente).
# Uso: bash scripts/run-local.sh   (Ctrl+C encerra os dois)
set -euo pipefail
CHALLENGE="${NAMASTEX_CHALLENGE_DIR:-../namastex-fde-challenge}"
API_PORT="${AGENT_API_PORT:-8010}"

cleanup() { kill %1 %2 2>/dev/null || true; }
trap cleanup EXIT

echo "▶ quote-api (legado instável) em :8000"
( cd "$CHALLENGE/quote-service" && uv run uvicorn app.main:app --port 8000 ) &
echo "▶ agent-api (Agente + FakeLLM offline) em :$API_PORT"
( cd services/agent-api && QUOTE_API_URL=http://localhost:8000   uv run uvicorn app.main:app --port "$API_PORT" ) &

echo ""
echo "✅ pronto:  health  → http://localhost:$API_PORT/health"
echo "            conversa→ curl -X POST http://localhost:$API_PORT/conversations"
wait
