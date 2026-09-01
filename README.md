# AutoSeguro Sales Agent — Namastex FDE Challenge

Agente de vendas de seguro de veículo que conversa, qualifica, **cota via API
legado instável** (20% de falha, 10% de lentidão — de propósito) e decide com
critério explícito quando passar para um humano.

> Resposta ao [desafio FDE/AI Engineer da Namastex](https://github.com/namastexlabs/namastex-fde-challenge).
> Uso de IA como parte do processo — ver [`ai-logs/`](./ai-logs/).

## Demo

- 🌐 Front (chat + fila de handoffs): *URL Vercel — preenchida na entrega (Etapa 17)*
- ⚙️ API: *URL Railway — idem*
- 📜 Log de execução completa: botão **Exportar** no chat (C1 da spec)

## Quickstart (dev)

```bash
# requisitos: Docker + make (ou abra no VS Code — devcontainer sobe sozinho)
make dev          # agent-api :8001 · quote-api :8000 · postgres
make mock         # (opcional) mock do contrato em :4010 para o front
make test         # testes + coverage
```

Documentação completa de setup: [`docs/`](./docs/README.md) → processo de 21 etapas.

## Stack

Next.js/Vercel · Python 3.12/FastAPI/Railway · Postgres · 1 LLM call/turno
(gpt-4o-mini, JSON mode) · resiliência: timeout 3s + 3 tentativas + circuit
breaker 5/30s/2 · TDD na lógica determinística · evals com o dataset do desafio.

## Como este repo se organiza

Ver `AGENTS.md` (bússola do projeto) — contratos em `openapi/`, catálogo de
mensagens em `messages/`, documentação viva em `docs/` (4 fases / 21 etapas /
11 ADRs).

## Decisões-chave

| # | Decisão | Onde |
|---|---|---|
| 1 | Monolito modular (agent-api) com domínio puro | [ADR-0002] |
| 2 | Framework de agente caseiro fino (sem LangChain) | [ADR-0004] |
| 3 | Zero preço inventado — guardrail em CÓDIGO | spec §4.3 |
| 4 | PII mascarada antes do LLM e em toda saída | spec §3 · LGPD |
| 5 | Sem broker: Postgres (outbox + DLQ + lease) | [ADR-0010] |
| 6 | PT-BR único com catálogo compartilhado | [ADR-0009] |

[ADR-0002]: ./docs/fase-1-design-e-contratos/adr/ADR-0002-monolito-modular.md
[ADR-0004]: ./docs/fase-1-design-e-contratos/adr/ADR-0004-framework-agente-caseiro.md
[ADR-0009]: ./docs/fase-1-design-e-contratos/adr/ADR-0009-locale-unico-ptbr-catalogo-compartilhado.md
[ADR-0010]: ./docs/fase-1-design-e-contratos/adr/ADR-0010-sem-broker-postgres-como-transporte.md

---
*Status: documentação Fase 0-1 completa; implementação via TDD conforme
`docs/fase-0-negocio-e-requisitos/etapa-3-tasks.md`.*
