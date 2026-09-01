# ADR-0011 — Monorepo (sem Nx/Turborepo), contexto de IA como artefato

**Status:** aceito (01/09/2026)

## Contexto
Entrega = 1 repo público (exigência do desafio) contendo front (Next/Vercel),
back (agent-api/Railway), legado (quote-service), contratos, dataset-pipeline,
evals, docs e `ai-logs/`. Time de 1. Mudanças frequentes cross-stack
(contrato → types do front + client do back no mesmo PR).

## Decisão
1. **Monorepo único** (o repo de entrega) — propósito: PRs atômicos
   cross-stack, contexto único para agentes de IA (1 `AGENTS.md`), CI único,
   1 URL para o avaliador.
2. **Sem Nx/Turborepo**: orquestração via **Makefile** + **pnpm workspace**
   (só `apps/web` hoje; hook pronto para `packages/` futuros, ex.: types
   gerados como pacote). 2 apps + 1 serviço Python não justificam cache remoto.
3. **Contexto de IA é artefato de engenharia**: `AGENTS.md` (raiz) +
   READMEs por pasta + `docs/` versionada + quiz de onboarding (Etapa 11 §6) +
   **Dev Container** (humano e agente herdam o mesmo ambiente).

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Polyrepo** (front/back/dataset separados) | Isolamento | Exigiria multi-repo público p/ entrega; PRs cross-stack partidos; contexto de IA duplicado; versionamento de contrato coordenado à mão | Descartado |
| **Monorepo + Nx/Turborepo** | Cache remoto, grafo de tarefas | 3 pacotes, build total < 3 min — complexidade sem retorno; mais config p/ agente entender | Reserva (gatilho: >5 apps ou CI > 10 min) |
| **Monorepo + Makefile/pnpm** ✅ | Simples, universal (agente/humano/CI usam os mesmos alvos), zero lock-in de task runner | Sem cache de build | **Aceita** |
| **Bun/npm workspace** | — | pnpm: workspaces + velocidade + uso corrente | Descartado |

## Consequências
**Positivas:** `make X` é a linguagem comum de humano, agente e CI (Etapa 16
chama os mesmos alvos); onboarding = abrir devcontainer + ler AGENTS.md;
contrato/catálogo/eventos na raiz com dono claro.
**Negativas:** repo maior (mitigado: dataset gerado por script, `.gitignore`);
CI roda tudo a cada push até surgir path-filtering (Etapa 16).
