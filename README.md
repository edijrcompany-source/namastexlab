# AutoSeguro Sales Agent — Namastex FDE Challenge

Agente de vendas de seguro de veículo que conversa, qualifica, **cota via API
legado instável** (20% de falha · 10% de lentidão — de propósito) e decide com
critério explícito quando passar para um humano.

> Resposta ao [desafio FDE/AI Engineer da Namastex](https://github.com/namastexlabs/namastex-fde-challenge).
> Uso de IA como parte do processo — ver [`ai-logs/`](./ai-logs/).

## Como rodar (2 caminhos)

### Com Docker (recomendado — igual ao CI/produção)

```bash
docker compose up --build
# agent-api :8001 · quote-api :8000 · postgres — health em http://localhost:8001/health
cd apps/web && pnpm i && NEXT_PUBLIC_AGENT_API_URL=http://localhost:8001 pnpm dev
# chat em http://localhost:3000 · fila de handoffs em /handoffs
```

### Sem Docker (3 processos)

```bash
bash scripts/run-local.sh                       # legado :8000 + agente :8010
cd apps/web && NEXT_PUBLIC_AGENT_API_URL=http://localhost:8010 pnpm dev
```

Detalhes e os 6 cenários de teste (C1-C6): **[`docs/testar-local.md`](./docs/testar-local.md)**

## Entregáveis do desafio

| Exigência | Onde |
|---|---|
| Agente ponta a ponta (conversa→cota→decisão) | API + chat — cenários C1-C6 da spec, verdes nos containers |
| Repo público com código | este repo (TDD, 27+ commits, gates no CI) |
| README de decisões | este arquivo + [`docs/`](./docs/README.md) (21 etapas, 11 ADRs) |
| **Log de execução completa** | **[`docs/log-execucao-c1.md`](./docs/log-execucao-c1.md)** (gerado nos containers, PII mascarada) |
| Conversas com IAs | [`ai-logs/`](./ai-logs/2026-09-01-implementacao-zcode.md) (sanitizadas, scan 0 segredos) |

## Números da entrega (verificados)

- **Cobertura: 100%** no backend — 157 testes + 11 do pipeline de dados (gate bloqueante)
- **Front: 11 testes** (Vitest + Testing Library) · build verde · Storybook (`pnpm storybook`)
- **Evalss**: extração 100% · decisão de handoff 100% · adversarial 20/20 (0 violações)
- **TRA 96,5%** (200 conversas no pior caso do legado — meta 70%)
- **Silver**: 26.470 mensagens com **PII 100% mascarada** (0 vazamentos)
- Containers **não-root** (uid 10001) · arquitetura enforçada por import-linter

## Stack

Next.js/Vercel* · Python 3.12/FastAPI/Railway* · Postgres · 1 LLM call/turno
(gpt-4o-mini via porta — **sem chave roda com FakeLLM offline**). Resiliência:
timeout 3s · 3 tentativas · circuit breaker 5/30s/2 · **zero preço inventado**
(guardrail em código, spec §4.3) · PII mascarada antes do LLM.

*deploy público: runbook pronto em [`docs/deploy-demo.md`](./docs/deploy-demo.md) (contas do autor).

## Decisões-chave

| # | Decisão | ADR |
|---|---|---|
| 1 | Monolito modular (domínio puro + portas) | [ADR-0002](./docs/fase-1-design-e-contratos/adr/ADR-0002-monolito-modular.md) |
| 2 | Framework de agente caseiro (sem LangChain) | [ADR-0004](./docs/fase-1-design-e-contratos/adr/ADR-0004-framework-agente-caseiro.md) |
| 3 | Zero preço inventado — guard em CÓDIGO | spec §4.3 |
| 4 | Sem broker: Postgres como transporte | [ADR-0010](./docs/fase-1-design-e-contratos/adr/ADR-0010-sem-broker-postgres-como-transporte.md) |
| 5 | PT-BR único, catálogo compartilhado | [ADR-0009](./docs/fase-1-design-e-contratos/adr/ADR-0009-locale-unico-ptbr-catalogo-compartilhado.md) |

Processo completo: 4 fases / 21 etapas com portões — [`docs/README.md`](./docs/README.md) ·
RETRO com aprendizados: [`RETRO.md`](./RETRO.md)
