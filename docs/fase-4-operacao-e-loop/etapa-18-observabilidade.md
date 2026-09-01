# Etapa 18 — Observabilidade

> Fase 4 · O sistema vivo: **sem isso, todas as fases anteriores são cegas em
> produção.** Um único SDK (OpenTelemetry) para traces, métricas e logs;
> **SLOs com error budget** orientam prioridade; o correlation ID da Etapa 6
> costura o trace do front ao banco.
>
> *"Alerta que acorda sem importância destrói a confiança no sistema de
> alertas"* — portanto: **poucos alertas, todos acionáveis, cada um com runbook.**

---

## 1. Os 3 pilares sob um SDK (OpenTelemetry)

| Pilar | Como | Detalhe |
|---|---|---|
| **Traces** | OTel SDK (autoinstrumentação FastAPI/SQLAlchemy/httpx) | Span tree de um turno: `web.fetch` → `api.turno` → `privacy.masking` · `llm.completion` · `quote.attempt[n]` (3 máx) · `db.transacao` |
| **Métricas** | OTel metrics → backend (Grafana Cloud free / Prometheus compat) | turno duração, tentativas de cotação, estado do circuito, TRA diária, tokens LLM |
| **Logs** | JSON estruturado (`structlog`) com `correlation_id`, `conversation_id`, `quote_id`, estado | PII **mascarada por construction** (Etapa 6 — o masking roda ANTES do log) |

### O correlation ID costura tudo (da Etapa 6 ao Sentry)

```
front gera X-Correlation-Id (crypto.randomUUID)
  → header do POST /messages
    → trace_id/baggage OTel do turno (e spans filhos)
      → TODOS os eventos persistidos (events.correlation_id — Etapa 8)
      → TODOS os logs do turno
      → problem+json em erro (correlation_id)
      → Sentry: tag correlation_id + release(sha) + env
```

O avaliador vê o correlation ID no rodapé do chat (Etapa 6 §6); a engenharia
busca o MESMO id no trace, nos logs e no evento — **uma requisição, um fio**.

### Limite honesto do tracing
O quote-api é do desafio (**não instrumentamos o legado** — regra 3): o trace
nossa parte vai do front até o **client span** da chamada ao legado (com
tentativas/backoff visíveis). Dentro dele é caixa-preta — por design.

## 2. Backends por ambiente (decisão)

| Ambiente | Traces | Métricas/Alertas | Logs | Erros |
|---|---|---|---|---|
| dev | **Jaeger** (compose perfil `observability` — Etapa 15) | — | stdout JSON | — |
| staging/prod | OTLP → **Grafana Cloud free** (traces+metrics) | regras versionadas `observability/alerts.yml` | JSON (Railway) + Loki se ativo | **Sentry** (DSN por env, tags: correlation_id/conversation_id/release) |
| uptime | — | **Better Stack free**: ping `/health` a cada 5 min (NFR-06) | — | — |

*Datadog/Loki/Tempo self-host: N/A justificado (custo/operação para 1 dev) —
Grafana Cloud free cobre o porte; gatilho de migração: volume além do free.*

## 3. SLOs e error budget (prioridade orientada por dados)

| # | SLI | SLO | Error budget (30d) | Se queimar 100% |
|---|---|---|---|---|
| SLO-1 | Turnos com resposta 2xx + `/health` ok | **99%** | ~7,2 h/mês | semana vira só-confiabilidade |
| SLO-2 | Turno p95 < 5s (NFR-01) | 95% das semanas | 5% | investigar gargalo (trace mostra: LLM vs legado vs DB) |
| SLO-3 | **TRA ≥ 70%** (métrica norte) | mensal | 30% | evals (Etapa 19) apontam onde a autonomia cai |
| SLO-4 | Preço sem origem (`price_guard_violation`) | **0** (zero-tolerance — NFR-09) | **sem budget**: 1 ocorrência = incidente | RB-05 + revisão de prompt (Etapa 20) |

**Política de error budget** (adaptada a 1 dev): budget queimado → a próxima
semana prioriza confiabilidade, não features. Registrada no RETRO (Etapa 21)
quando acionada.

## 4. Alertas — poucos, acionáveis, TODOS com runbook

Regras versionadas em [`observability/alerts.yml`](../../observability/alerts.yml)
(formato PrometheusRule — compatível com Grafana Cloud):

| Alerta | Condição | Severidade | Runbook |
|---|---|---|---|
| `DemoDown` | ping `/health` falha 3× (5 min) | 🔴 critical | RB-03/RB-05 |
| `PrecoSemOrigem` | `price_guard_violation` ≥ 1 | 🔴 **critical (SLO-4)** | RB-05 + Etapa 20 |
| `DBIndisponivel` | 503 `servico-indisponivel` > 5 em 5 min | 🔴 critical | RB-01/RB-05 |
| `LegadoCircuitoAberto` | circuito aberto > 2× em 15 min | 🟡 warning | RB-05 |
| `TurnoLento` | p95 turno > 8s por 10 min | 🟡 warning | RB-05 (trace aponta o span) |
| `LLMIndisponivel` | `llm_unavailable` > 10% turnos/30 min | 🟡 warning | RB-02/RB-05 |
| `TRAReprovada` | TRA diária < 70% | 🟡 warning | Etapa 19 (evals) |

**Anti-"alarm fatigue":** nenhum alerta informativo; warning = mesmo dia;
critical = ação imediata. Alerta sem runbook é bug da observabilidade.

## 5. Incidente simulado (portão) — o ensaio

| Simulação (em staging) | Como | Alerta esperado |
|---|---|---|
| Legado fora | parar o serviço quote-api 15 min | `LegadoCircuitoAberto` → depois `DemoDown`? não: agente degrada gracefully (RB-05) — o alerta certo é o circuito |
| DB fora | parar Postgres 5 min | `DBIndisponivel` + turnos atômicos falham |
| LLM fora | key inválida 30 min | `LLMIndisponivel` + fallback canônico ativo |
| Preço inventado | injetar mock de LLM que alucina valor | `PrecoSemOrigem` (o guardrail pega) |

O ensaio é executado em staging (Etapa 17) e **registrado aqui**:
`[ ] ensaio executado em ____/____ (T-15) — evidências anexadas ao release`

## 6. ✅ Portão de validação da Etapa 18

| Critério | Status |
|---|---|
| Trace ponta a ponta de uma requisição | 🟡 instrumentação especificada (SDK único, spans definidos); primeiro trace real no T-07 (healthcheck + 1 turno) — verificável em `make observability` (Jaeger dev) |
| Incidente simulado dispara o alerta correto | 🟳 ensaio mapeado (§5), executa no T-15 pré-entrega (staging) |
| Cada alerta tem runbook | ✅ 7 alertas ↔ RBs existentes (`docs/runbooks.md`) — regras versionadas no repo |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 19 liberada)*
