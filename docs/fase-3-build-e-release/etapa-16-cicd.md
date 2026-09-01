# Etapa 16 — Pipeline CI/CD

> Fase 3 · **Trunk-based com feature flags: merge cedo, libere depois.**
> Cada gate existe para pegar uma **classe de defeito específica** — nenhum
> gate é cerimonial. PR de IA: **gate automático + revisão humana, sempre**.

---

## 1. A ordem dos gates e o que cada um pega

| # | Gate (job) | Workflow | Classe de defeito que pega | Tempo |
|---|---|---|---|---|
| 1 | **lint** | `pr` | estilo/estrutura · **arquitetura violada** (import-linter = C4) · commit fora do gitmoji · Dockerfile inseguro (hadolint) | ~1,5 min |
| 2 | **contracts** | `pr` | contrato quebrado em silêncio (spectral) · types editados à mão (codegen `--check`) | ~40s |
| 3 | **security** + **codeql** | `pr` | segredo vazado (gitleaks, varre `ai-logs/`) · CWE (CodeQL) · CVE de dependência (pip/npm audit) | paralelo |
| 4 | **test** | `pr` | regra de negócio errada · integração quebrada (Postgres real) · contrato drift · componente sem papel semântico · coverage <90% | ~2 min |
| 5 | **build-scan** | `pr` | imagem com CVE crítica (Trivy) · build que não reproduz | ~1 min |
| 6 | **e2e** | `nightly` + pré-release | jornada quebrada de ponta a ponta (C1-C6, legado determinístico) · visual regression | ~6 min |
| 7 | **mutation** | `nightly` | testes que não testam (mutmut ≥60% núcleo) | noturno |
| 8 | **evals-real** | `nightly` | IA degradada (extração/handoff/20 ataques com LLM real) | noturno |
| 9 | **deploy + smoke** | `release` | release quebrada NA DEMO — smoke falha → **rollback automático** | ~3 min |
| 10 | **docs** | `docs` | doc desatualizada ("não publicado = não existe") | ~1 min |

**Metas:** PR **<5 min** (NFR-17, jobs paralelos) · noturno **<10 min**
(portão) · release **<8 min**.

## 2. Workflows materializados (`.github/workflows/`)

| Arquivo | Trigger | Conteúdo |
|---|---|---|
| `pr.yml` | pull_request | gates 1-5 (lint+commitlint+hadolint · contracts · security/codeql · test c/ Postgres real · build+trivy) |
| `nightly.yml` | cron 03:00 UTC + manual | e2e C1-C6 (`QUOTE_SEED=42`) + mutmut + evals LLM real + docs-build |
| `release.yml` | push main | fast-track → **GHCR tag sha** → Railway (pre-deploy = migrations) → **smoke na demo** → falha: **rollback automático** (última imagem boa + `vercel rollback`) → sucesso: registra `LAST_GOOD_TAG` |
| `docs.yml` | push main | Redoc + VitePress → **GitHub Pages** a cada merge |

## 3. Decisões registradas nesta etapa

1. **Feature flags sem Unleash/LaunchDarkly** (inline): 1 serviço, ~2 flags —
   flags locais por env com **kill switch** embutido:
   `FEATURE_COMPARE_REBATIDA` (US-09) · `AGENT_KILL_SWITCH` (se on: responde
   só canônico, sem LLM — desligar o Agente sem deploy). Gatilho p/ Unleash:
   multi-ambiente com experimentos A/B reais.
2. **Preview por PR**: front = Vercel automático (default, portão ✓). agent-api
   preview completo ficaria para Railway Environments (custo) — PRs validam via
   testes+mock; registro da decisão.
3. **Rollback em 2 níveis**: imagem (Railway, `LAST_GOOD_TAG` do GHCR) + front
   (`vercel rollback`). O deploy de rollback é o mesmo job que falhou no smoke —
   um só caminho, sem procedimento manual paralelo.
4. **Trunk-based**: branches vivos <2 dias, PR pequenos, feature flag para o
   inacabado — nada de long-lived branches.

## 4. Revisão humana (portão) — branch protection + CODEOWNERS

Recipe exato (comentado no `.github/CODEOWNERS`):
- ✅ Require PR + **1 approval** (dismiss stale approvals)
- ✅ Required checks: `lint, contracts, security, codeql, test, build-scan`
- ✅ Require linear history · sem force-push na main
- CODEOWNERS aponta o reviewer obrigatório de TODA árvore

**Nenhum PR — inclusive gerado por IA — entra sem os dois** (regra Fase 3,
também no `AGENTS.md`).

## 5. ✅ Portão de validação da Etapa 16

| Critério | Status |
|---|---|
| Pipeline verde <10 min | ✅ orçado: PR <5 · noturno <10 · release <8 (medição real a partir do 1º código) |
| Rollback testado ponta a ponta | 🟡 mecanismo automático no `release.yml` + **rehearsal documentado** (deploy proposital quebrado → smoke falha → rollback → demo boa) executar pré-entrega (T-15) |
| Front com preview por PR | ✅ Vercel default (ativa com o repo conectado — Etapa 17) |
| Nenhum PR sem revisão humana | ✅ branch protection + CODEOWNERS materializados (ativar no repo — recipe pronto) |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 17 liberada)*
