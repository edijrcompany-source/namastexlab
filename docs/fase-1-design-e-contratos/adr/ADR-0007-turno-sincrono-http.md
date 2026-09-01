# ADR-0007 — Turno síncrono HTTP (sem WebSocket)

**Status:** aceito (01/09/2026) · **Origem:** spec §5.4

## Contexto
Cada turno: 1 call LLM (2-4s) + eventualmente cotação no legado (3 tentativas
× timeout 3s + backoff ≈ pior caso ~8s). O front precisa mostrar a resposta do
Agente no mesmo gesto do Lead. Volume: 10 conversas simultâneas.

## Decisão
**`POST /conversations/{id}/messages` é síncrono**: responde `{reply, estado,
eventos_do_turno}` quando o turno completa (alvo p95 < 5s; pior caso ~8s com
retry). Estados intermediários ("pensando", "cotando 2/3") são informados
**na resposta** (eventos do turno) e animados pelo front.

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **WebSocket** | Feedback sub-etapa em tempo real | Estado de conexão no serverless front; reconexão; complexidade de teste E2E; ganho irrelevante para turnos de chat (não é streaming token-a-token para o Lead) | Descartado |
| **POST + polling de status** | Request rápido, progresso consultável | 2 endpoints + latência de polling; UX igual com animação local | Descartado |
| **SSE** | Push simples | Mesma complexidade de conexão do WS para ganho marginal | Descartado |
| **Síncrono** ✅ | 1 endpoint · teste de contrato trivial (C1-C6) · client Next simples | Request aberto até ~8s; timeout do client front precisa ser > pior caso (15s) | **Aceita** |

## Consequências
**Positivas:** C1-C6 viram testes httpx diretos; rastreabilidade do turno vem
numa resposta só (timeline consistente).
**Negativas/riscos:** worker do uvicorn ocupado por turno — com 10 VUs
concurrentes e async correto, não é gargalo (NFR-08 valida); front precisa
de timeout generoso + spinner honesto (spec §8 já especifica).
