# Fase 1 — Design e Contratos (Etapas 4-10)

> ✅ Concluída 01/09/2026 — Etapas 4-10 validadas. Libera a Fase 2.

| Etapa | Documento | Status |
|---|---|---|
| 4 | [`etapa-4-arquitetura-c4.md`](./etapa-4-arquitetura-c4.md) — C4 níveis 1-3, monolito modular, regras de dependência | ✅ validada |
| 4 | [`adr/`](./adr/README.md) — ADR-0001 a ADR-0011 | ✅ validada |
| 5 | [`etapa-5-contratos.md`](./etapa-5-contratos.md) + [`openapi/` na raiz](../../../openapi/) — agent-api (inbound) + quote-api (consumidor), lint/codegen/mock/drift | ✅ validada (gates → Etapa 16) |
| 6 | [`etapa-6-erros-resiliencia.md`](./etapa-6-erros-resiliencia.md) — RFC 7807 + correlation ID, catálogo de erros, matriz de resiliência, idempotência, front error states | ✅ validada |
| 7 | [`etapa-7-i18n.md`](./etapa-7-i18n.md) + [`messages/pt-BR.json` na raiz](../../../messages/pt-BR.json) — ADR-0009: pt-BR único, catálogo compartilhado, pseudo-locale | ✅ validada |
| 8 | [`etapa-8-modelo-de-dados.md`](./etapa-8-modelo-de-dados.md) — ERD DBML, enums, Alembic + EMC, purga LGPD, restore testado | ✅ validada |
| 9 | [`etapa-9-mensageria.md`](./etapa-9-mensageria.md) — ADR-0010: Postgres como transporte; outbox, worker lease+SKIP LOCKED, DLQ, eventos públicos v1 | ✅ validada |
| 10 | [`etapa-10-threat-model.md`](./etapa-10-threat-model.md) — STRIDE (16 ameaças), segredos+rotação, auth entre serviços, ASVS L1, scans obrigatórios | ✅ validada |

Input: `../fase-0-negocio-e-requisitos/` validado. ✅
Output: libera a Fase 2 (Etapa 11 — Estrutura do repo e context engineering).
