# AGENTS.md — AutoSeguro Sales Agent

> Contexto versionado para humanos E agentes de IA. **Leia este arquivo antes
> de qualquer contribuição.** Ele é a bússola; a spec é o mapa; o Makefile é o
> idioma comum. Versão 2 (Etapa 11).

## O que é este projeto

Agente de vendas de seguro auto (desafio take-home FDE/AI Engineer da Namastex):
conversa com leads por chat, qualifica (veículo+ano, idade, CEP), cota via API
legado **instável** (20% falha, 10% lenta) e decide quando passar para humano.
Entrega: este repo público + demo viva + `ai-logs/`.

## Estrutura do repo

```
openapi/          contratos API-first (FONTE ÚNICA — inbound + as-consumed)
messages/         catálogo pt-BR compartilhado API↔front (zero string crua)
schemas/eventos/  6 JSON Schemas públicos v1
apps/web/         Next.js → Vercel
services/agent-api/  Python/FastAPI → Railway (monolito modular)
quote-service/    cópia do desafio — SOMENTE LEITURA
prompts/          prompts versionados (system_v1.md)
scripts/          fetch_bronze, build_silver, pseudo_locale
evals/            suite de avaliação da IA
dataset/          Bronze/Silver (gitignored — gerar com make bronze/silver)
ai-logs/          conversas com IAs — ENTREGÁVEL (sanitizar antes de commit)
docs/             docs-as-code: 4 fases / 21 etapas, spec, ADRs
```

## Fontes de verdade (nesta ordem)

1. **Spec:** `docs/fase-0-negocio-e-requisitos/etapa-3-spec.md` — estados,
   parâmetros de resiliência, formatos, mensagens, ataques, casos C1-C6.
2. **Glossário:** `docs/fase-0-negocio-e-requisitos/etapa-1-linguagem-ubiqua.md`
   — vocabulário obrigatório; sinônimos banidos (tabela no fim do arquivo).
3. **Contratos:** `openapi/*.yaml` · **Catálogo:** `messages/pt-BR.json` ·
   **NFRs:** etapa-2 · **ADRs:** `docs/fase-1-design-e-contratos/adr/`.
4. **Status do processo:** `docs/README.md` (checklist 21 etapas).

## Regras invioláveis (violar = rejeitar PR)

1. **Nenhum valor monetário fora de resposta da API `/quote`.** O price-guard
   pós-LLM (spec §4.3) nunca é removido/burlado.
2. **PII nunca aparece crua** em log, timeline, export, eval ou prompt — usar
   o masking (spec §3). `MASKING_STRICT=true` não se desliga. CEP íntegro só
   no request ao legado; no resto, `01***-***`.
3. **`quote-service/` é somente leitura.** Bronze de `dataset/` também
   (regenerável por script, nunca commitado).
4. Toda lógica determinística nasce de **teste primeiro** (TDD — red→green).
5. Vocabulário do glossário. Recusa 422 ≠ falha transiente 5xx: retry **só**
   na transiente.
6. **Commits: `<gitmoji> <type>(escopo)?: intenção em inglês, imperativo, ≤72
   chars** — ex.: `✨ feat(quoting): add circuit breaker with lease`. Tipos:
   feat/fix/test/docs/refactor/perf/security/chore/ci. **Micro-commits
   atômicos** (1 commit = 1 intenção; commitlint rejeita fora do padrão —
   Etapa 13). PR pequeno, citando a seção da spec (ex.: "spec §2").

## Comandos (humano, agente e CI usam os mesmos alvos)

```bash
make contracts-lint   # spectral nos contratos (blocker)
make codegen check    # types TS do contrato — falha se alguém editou à mão
make mock             # Prism mock do agent-api em :4010 (front anda sem back)
make dev              # compose: agent-api(8001) + quote-api(8000) + postgres
make bronze           # regenera dataset Bronze (seed 42, do repo do desafio)
make silver           # Bronze → Silver (masking + normalização)
make test             # pytest + coverage gate ≥99% (lógica determinística)
make evals            # extração/handoff/adversarial (20 ataques, 0/20)
make fmt && make lint # ruff + eslint/prettier + import-linter
```

Alvos não implementados falham com a task responsável no erro — nunca
silenciosamente.

## Convenções

- Python ≥3.12 · ruff · type hints obrigatórios em `core/` · uv
- Módulos de domínio (`masking`, state machine, breaker) são **puros**: sem
  I/O, sem framework. I/O vive nas bordas. Regras de dependência: C4 nível 3.
- Front: TypeScript strict · componentes funcionais · **zero string de tela
  fora de `messages/pt-BR.json`** (eslint jsx-no-literals)
- Erro de protocolo = RFC 7807 com código estável; desfecho de negócio =
   resposta 200 + eventos (etapa-6 §1)
- Eventos novos/endpoint novo: **PR na spec/contrato primeiro**, depois código
- Migration: 1 PR = 1 revision, `down()` obrigatório (etapa-8 §4)

## Armadilhas conhecidas (leia duas vezes)

1. **Timestamps do dataset NÃO são monotônicos** — ordenar por `message_index`.
2. **Preços citados pelos vendedores no dataset NÃO batem com a API** — o
   Agente cota pela API, nunca imita o dataset.
3. Veículo do dataset pode ser impossível ("Fiat Pulse 2008") — texto livre
   não é confiável; validar `veiculo_ano` (1950..ano+1).
4. Em 2026, carro ≤2005 = recusado (>20 anos). Idade 76+ = recusado. ~30% do
   dataset é inelegível — esperado, é o negócio.
5. Resposta lenta de 8s do legado **é** a falha transiente — timeout 3s nosso.
6. O desafio manda **mascarar PII na camada Silver** — nunca logar Bronze cru.

## Para agentes de IA

- Implemente citando a seção da spec no PR/ticket ("spec §2", "C3").
- Spec ambígua ou conflitante: **pare e proponha correção da spec** — não
  improvise silenciosamente.
- Nunca invente preço, dados de plano ou comportamento não especificado;
  `plans.json` do legado é a única fonte de planos (`GET /planos`).
- Tipos de `apps/web/src/types/` são GERADOS (`make codegen`) — nunca edite.
- Quiz de onboarding: `docs/fase-2-fundacao-de-engenharia/etapa-11-estrutura-repo.md` §6 —
  se alguma resposta não estiver neste arquivo ou nos links dele, o contexto
  está incompleto: corrija o contexto.
- Suas conversas com IA vão para `ai-logs/` — **sanitize segredos antes**.
- **PR gerado por IA entra só com gate automático verde + revisão humana —
  sempre os dois** (regra da Fase 3 do processo; branch protection na Etapa 16).
