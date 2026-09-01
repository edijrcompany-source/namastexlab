# ADRs — Architecture Decision Records

> Decisões estruturais do projeto. Cada ADR é imutável após aceito (superseded
> por novo ADR, nunca editado). Formato: contexto, decisão, alternativas,
> consequências. Status: `aceito` · `substituído por ADR-XXXX` · `proposto`.

| ADR | Título | Status | Origem |
|---|---|---|---|
| [0001](./ADR-0001-front-nextjs-vercel.md) | Front Next.js hospedado na Vercel | aceito 01/09/2026 | decisão D1 |
| [0002](./ADR-0002-monolito-modular.md) | Monolito modular (agent-api) | aceito 01/09/2026 | Etapa 4 |
| [0003](./ADR-0003-runtime-python-fastapi.md) | Runtime Python 3.12 + FastAPI | aceito 01/09/2026 | Etapa 4 |
| [0004](./ADR-0004-framework-agente-caseiro.md) | Framework de agente caseiro fino (sem LangGraph/LangChain) | aceito 01/09/2026 | Etapa 4 |
| [0005](./ADR-0005-llm-provider.md) | LLM: abstração de provider + default OpenAI gpt-4o-mini | aceito 01/09/2026 | Etapa 4 |
| [0006](./ADR-0006-persistencia-postgres.md) | Persistência Postgres gerenciado | aceito 01/09/2026 | Etapa 4 |
| [0007](./ADR-0007-turno-sincrono-http.md) | Turno síncrono HTTP (sem WebSocket) | aceito 01/09/2026 | spec §5.4 |
| [0008](./ADR-0008-hospedagem-vercel-railway.md) | Hospedagem: Vercel (front) + Railway (backend), região GRU | aceito 01/09/2026 | decisão D2/D4 |
| [0009](./ADR-0009-locale-unico-ptbr-catalogo-compartilhado.md) | Locale único pt-BR + catálogo único compartilhado API↔front | aceito 01/09/2026 | Etapa 7 |
| [0010](./ADR-0010-sem-broker-postgres-como-transporte.md) | Sem broker: Postgres como transporte (outbox + SKIP LOCKED + DLQ) | aceito 01/09/2026 | Etapa 9 |
| [0011](./ADR-0011-monorepo-contexto-ia.md) | Monorepo sem Nx/Turborepo; contexto de IA como artefato | aceito 01/09/2026 | Etapa 11 |
