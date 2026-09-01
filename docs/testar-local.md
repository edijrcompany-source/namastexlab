# Rodar e Testar Local (sem Docker)

> 3 processos: legado instável (8000) + Agente (8010) + front (3000).
> Sem chave de LLM: o Agente roda com **FakeLLM offline** (determinístico).
> Com `LLM_API_KEY`: LLM real (gpt-4o-mini) automaticamente.

## Modo 1 — um comando (Git Bash)

```bash
bash scripts/run-local.sh          # sobe legado + agent-api
# em outro terminal:
cd apps/web && pnpm dev            # front em http://localhost:3000
```

## Modo 2 — manual

```bash
# 1. legado (repo do desafio — intocado)
cd namastex-fde-challenge/quote-service && uv run uvicorn app.main:app --port 8000

# 2. Agente
cd namastex-fde/services/agent-api
QUOTE_API_URL=http://localhost:8000 uv run uvicorn app.main:app --port 8010

# 3. front
cd namastex-fde/apps/web
NEXT_PUBLIC_AGENT_API_URL=http://localhost:8010 pnpm dev
```

## Testar (caminho feliz C1)

```bash
# health (agent + legado)
curl localhost:8010/health

# cria conversa
curl -X POST localhost:8010/conversations

# qualifica → confirma → cota → aceita (use o id retornado acima)
curl -X POST localhost:8010/conversations/<ID>/messages -H 'content-type: application/json' \
  -d '{"text":"Onix 2022, tenho 30 anos e o CEP é 01310-100"}'
curl -X POST localhost:8010/conversations/<ID>/messages -H 'content-type: application/json' \
  -d '{"text":"é isso"}'
curl -X POST localhost:8010/conversations/<ID>/messages -H 'content-type: application/json' \
  -d '{"text":"fechado!"}'

# fila de handoffs + export do log (entregável)
curl localhost:8010/handoffs
curl "localhost:8010/conversations/<ID>/export?fmt=md"
```

Ou **abra http://localhost:3000** e converse no chat.

## Cenários de teste rápidos (browser)

| Cenário | O que fazer | Esperado |
|---|---|---|
| C1 feliz | "quero cotar" → dados → "é isso" → "fechado!" | QuoteCard com preço/caráncia → banner handoff |
| C2 objeção | após cotação: "tá caro" → "ainda caro, desconto?" | rebatida comparativa → handoff objecao_preco |
| C3 recusa | "Gol 1998, 79 anos, CEP 01310-100" → confirmar | recusa clara SEM cotação (pré-check) |
| C5 instabilidade | o legado falha 20% das vezes — repita cotações | mensagem honesta SEM preço; retentativa |
| C6 humano | "quero falar com uma pessoa" | handoff imediato; chat bloqueia |

## Testes automatizados

```bash
cd services/agent-api && uv run pytest --cov=app --cov-fail-under=100
# 151 testes · cobertura 100% (gate)
```

## Docker (quando disponível)

`make dev` (compose completo com Postgres + perfis migrate/observability).
