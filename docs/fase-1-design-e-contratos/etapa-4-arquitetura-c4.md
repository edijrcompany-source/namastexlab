# Etapa 4 — Arquitetura (Modelo C4)

> Fase 1 · Arquitetura descrita nos 3 níveis do C4. As decisões por trás de
> cada caixa estão nos [ADRs](./adr/README.md). Regra do guia aplicada:
> **monolito modular primeiro** — extração de serviço só com dor medida.

---

## Nível 1 — Contexto do sistema

```
                    ┌────────────────────┐
                    │       LEAD         │
                    │ (pessoa buscando   │
                    │  seguro auto)      │
                    └─────────┬──────────┘
                              │ conversa (web chat)
                              ▼
┌──────────────────┐   ┌─────────────────────────────┐   ┌──────────────────┐
│    VENDEDOR      │   │                             │   │   LLM PROVIDER   │
│ (humano que      │◀──┤  AUTOSEGURO SALES AGENT     ├──▶│  (API externa,   │
│  atende handoffs)│   │  [nosso sistema]            │   │   key em secret) │
└──────────────────┘   │                             │   └──────────────────┘
                       │  qualifica, cota, decide    │
                       │  handoff                    │
                       └──────────┬──────────────────┘
                                  │ POST /quote (HTTP)
                                  ▼
                       ┌─────────────────────────────┐
                       │  SISTEMA LEGADO DE COTAÇÃO  │
                       │  (quote-api — do desafio,   │
                       │   NÃO alteramos; falha 20%, │
                       │   lento 10%)                │
                       └─────────────────────────────┘

[AVALIADOR Namastex] — usa o mesmo web chat e lê o repo/entrega (não é ator técnico)
```

**Atores/sistemas externos:** Lead · Vendedor · LLM provider · quote-api (legado).

## Nível 2 — Containers

```
   VERCEL (região gru1)                RAILWAY (região São Paulo)
┌────────────────────────┐   ┌──────────────────────────────────────────┐
│  apps/web [Next.js]    │   │  projeto namastex-fde                    │
│  ──────────────────    │   │                                          │
│  • Chat de demo        │   │  ┌──────────────────────────────────┐    │
│  • Fila de handoffs    │   │  │ agent-api [Python 3.12/FastAPI]  │    │
│  • Timeline + export   │   │  │ monolito MODULAR (ver nível 3)   │    │
│                        │   │  └───┬──────────────┬────────────────┘    │
│  Estado: só conv-id    │   │      │              │                     │
│  em localStorage       │   │  TCP/5432       HTTP:8000 (rede interna) │
└───────────┬────────────┘   │      ▼              ▼                     │
            │ HTTPS :443    │ ┌──────────────┐ ┌───────────────────┐     │
            │ (CORS)        │ │ [Postgres 16]│ │ quote-api [FastAPI│     │
            └───────────────┼─▶│ eventos,     │ │ — do desafio,     │     │
                            │ │ conversas,   │ │ mock instável]    │     │
                            │ │ handoffs     │ └───────────────────┘     │
                            │ └──────────────┘                           │
                            │ + migrations (job efêmero no deploy)       │
                            └────────────────────────────────────────────┘
                                     │
                                     ▼ HTTPS (única saída externa do agent-api)
                             [LLM provider — ADR-0005]

DEV LOCAL: docker compose sobe agent-api(8001) + quote-api(8000) + postgres(5432)
           + jaeger (perfil observability). Next roda via `npm run dev`.
```

| Container | Tecnologia | Responsabilidade | ADR |
|---|---|---|---|
| `apps/web` | Next.js (Vercel) | UI do chat, fila, timeline, export | 0001 |
| `agent-api` | Python/FastAPI (Railway) | Monolito modular: conversa, LLM, ACL de cotação, handoff, masking | 0002, 0003 |
| `agent-postgres` | Postgres 16 (Railway) | Event store + conversas + fila de handoff | 0006 |
| `quote-api` | FastAPI (do desafio, Railway) | Cotação instável (insumo imutável) | — |
| LLM provider | API externa | 1 call/turno (intent+extração+resposta) | 0005 |

**Comunicações:** web→agent-api HTTPS+CORS (turno síncrono — ADR-0007) ·
agent-api→quote-api HTTP interno com timeout 3s/retry/breaker (spec §2) ·
agent-api→Postgres TCP (pool) · agent-api→LLM HTTPS (chave em secret).

## Nível 3 — Componentes (dentro do agent-api)

```
                         ┌─────────────────────────────────────────────┐
   HTTP                  │                  agent-api                  │
 ┌──────────┐            │  ┌────────────┐                             │
 │ apps/web ├───────────▶│  │  api/      │ routers, schemas,          │
 └──────────┘  HTTPS     │  │  (borda)   │ problem+json, ULID         │
                          │  └─────┬──────┘                            │
                          │        │                                   │
                          │        ▼                                   │
                          │  ┌──────────────────────────────────────┐  │
                          │  │ conversation/  [NÚCLEO]              │  │
                          │  │ • state_machine (pura, spec §1)      │  │
                          │  │ • turn_orchestrator (1 turno = 1 LLM │  │
                          │  │   call + transições + eventos)       │  │
                          │  └──┬───────────┬───────────┬───────────┘  │
                          │     │ portas (interfaces) │               │
                          │     ▼           ▼          ▼               │
                          │ ┌─────────┐ ┌─────────┐ ┌──────────┐       │
                          │ │ llm/    │ │ quoting/│ │ handoff/ │       │
                          │ │ client  │ │ ACL:    │ │ registro │       │
                          │ │ +prompt │ │ retry,  │ │ + fila   │       │
                          │ │ +price- │ │ breaker │ │ (tabela) │       │
                          │ │ guard   │ │ +client │ │          │       │
                          │ └────┬────┘ └────┬────┘ └────┬─────┘       │
                          │      │           │           │             │
                          │  ┌───▼───────────▼───────────▼──────────┐  │
                          │  │ events/  (event store → Postgres)    │  │
                          │  └──────────────────────────────────────┘  │
                          │                                            │
                          │  privacy/masking (puro — usado por TODOS)  │
                          │  domain/ (enums, tipos — shared kernel)    │
                          └─────────────────────────────────────────────┘
```

### Regras de dependência (enforcement em CI)

1. `conversation/` **não importa** `api/`, `llm/`, `quoting/` diretamente —
   usa portas (Protocol/ABC) injetadas; bordas implementam.
2. `conversation/`, `privacy/`, `domain/` são **puros** (sem I/O, sem
   framework) → alvo do gate de cobertura ≥ 90% (NFR-16).
3. `price-guard` fica em `llm/` (borda), mas sua lógica de detecção de `R$`
   é função pura reutilizada pelos testes do NFR-09.
4. Dependência proibida: qualquer módulo → `api/` (borda é folha).
5. Cross-cutting: `privacy/` não depende de ninguém além de stdlib.

### Fluxo de um turno (sequência)

```
POST /messages
 → api/ (valida, ULID)
 → privacy/masking (mascara PII da msg)
 → conversation/turn_orchestrator:
     1. state_machine: evento da msg
     2. llm/ (se precisa resposta): JSON {intent, dados, resposta}
     3. validação de campos (§4.4) + price-guard (§4.3)
     4. quoting/ACL (se CONFIRMA): 3 tentativas · breaker
     5. handoff/ (se critério): registra motivo
     6. events/: persiste eventos do turno
 ← resposta síncrona {reply, estado, eventos}
```

### Extrações futuras (preventivas, não antecipadas)

| Módulo | Gatilho de extração (dor medida) | Viraria |
|---|---|---|
| `quoting/` | p95 do legado degradando NFR-01 em produção | Serviço de cotação independente (já tem porta limpa) |
| `handoff/` | > 1.000 handoffs/dia ou needing workers | Fila própria (Etapa 7 define o ADR de broker) |
| `llm/` | multi-provider ativo com roteamento por custo | Gateway de LLM |

---

## Rastreabilidade C4 ↔ ADRs

| Elemento do diagrama | Decisão estrutural | ADR |
|---|---|---|
| Um único `agent-api` | Monolito modular vs microserviços | [ADR-0002](./adr/ADR-0002-monolito-modular.md) |
| Runtime do agent-api | Python/FastAPI vs Node/Go | [ADR-0003](./adr/ADR-0003-runtime-python-fastapi.md) |
| `apps/web` na Vercel | Next.js vs Vite/Remix | [ADR-0001](./adr/ADR-0001-front-nextjs-vercel.md) |
| `llm/` caseiro | Sem framework de agente | [ADR-0004](./adr/ADR-0004-framework-agente-caseiro.md) |
| LLM provider | OpenAI gpt-4o-mini default + abstração | [ADR-0005](./adr/ADR-0005-llm-provider.md) |
| Postgres | vs SQLite | [ADR-0006](./adr/ADR-0006-persistencia-postgres.md) |
| Setas síncronas | Turno HTTP vs WebSocket | [ADR-0007](./adr/ADR-0007-turno-sincrono-http.md) |
| Vercel+Railway | vs Fly/Render/CloudRun/VPS | [ADR-0008](./adr/ADR-0008-hospedagem-vercel-railway.md) |

## ✅ Portão de validação da Etapa 4

| Critério | Status |
|---|---|
| Toda decisão estrutural tem ADR com alternativas consideradas | ✅ 8 ADRs |
| Diagrama de containers atualizado | ✅ nível 2 acima (espelha a spec §5.4/§9) |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 5 liberada)*
