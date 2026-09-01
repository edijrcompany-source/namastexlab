# Documentação — AutoSeguro Sales Agent (Namastex FDE Challenge)

> ✅ **PROCESSO DE 21 ETAPAS CONCLUÍDO E VALIDADO (01/09/2026).**
> Revisão final dos 22 portões: [`checklist-final-implantacao.md`](./checklist-final-implantacao.md)
> (7 🟢 prontos · 15 🟜 design-fechado com task dona da evidência — nenhum risco esquecido).
> Próximo marco: implementação T-01..T-17 (TDD — [`fase-0-negocio-e-requisitos/etapa-3-tasks.md`](./fase-0-negocio-e-requisitos/etapa-3-tasks.md)).

Este diretório contém a documentação viva do projeto, organizada pelas fases do
guia de processo adotado (4 fases, 18 etapas). Nada é escrito aqui por acaso:
cada documento responde a uma etapa e passa por um **portão de validação**
antes de liberar a próxima.

> 📌 **Manutenção:** este README é atualizado ao final de TODA etapa
> (status do checklist, linha de validação e índice de artefatos).

## Mapa das fases e status

| Fase | Diretório | Cobertura | Status |
|---|---|---|---|
| 0 — Negócio e Requisitos | [`fase-0-negocio-e-requisitos/`](./fase-0-negocio-e-requisitos/) | Etapas 1-3 | ✅ Concluída 01/09/2026 |
| 1 — Design e Contratos | [`fase-1-design-e-contratos/`](./fase-1-design-e-contratos/) | Etapas 4-10 | ✅ Concluída 01/09/2026 (4-10 validadas) |
| 2 — Fundação de Engenharia | [`fase-2-fundacao-de-engenharia/`](./fase-2-fundacao-de-engenharia/) | Etapas 11-14 | ✅ Concluída 01/09/2026 (11-14 validadas) |
| 3 — Build e Release | [`fase-3-build-e-release/`](./fase-3-build-e-release/) | Etapas 15-17 | 🟡 Etapas 15-16 ✅ · Etapa 17 feita (fecha a fase) |
| 4 — Operação e Loop | [`fase-4-operacao-e-loop/`](./fase-4-operacao-e-loop/) | Etapas 18-21 | ✅ Concluída 01/09/2026 (18-21 validadas) |

## Índice de artefatos — Fase 0

| Etapa | Artefato | Conteúdo |
|---|---|---|
| 1 | [`etapa-1-modelo-de-negocio.md`](./fase-0-negocio-e-requisitos/etapa-1-modelo-de-negocio.md) | Problema, dores com evidências, personas, canvas, métrica norte (TRA), bounded contexts, portão |
| 1 | [`etapa-1-linguagem-ubiqua.md`](./fase-0-negocio-e-requisitos/etapa-1-linguagem-ubiqua.md) | Glossário DDD (~35 termos) + sinônimos banidos |
| 1 | [`etapa-1-event-storming.md`](./fase-0-negocio-e-requisitos/etapa-1-event-storming.md) | Fluxo feliz + 3 alternativos, políticas, hotspots H1-H8 |
| 2 | [`etapa-2-requisitos-e-nfrs.md`](./fase-0-negocio-e-requisitos/etapa-2-requisitos-e-nfrs.md) | 16 user stories (Given/When/Then) · 18 NFRs numerados · checklist LGPD · DoR · matriz de rastreabilidade |
| 3 | [`etapa-3-prd.md`](./fase-0-negocio-e-requisitos/etapa-3-prd.md) | PRD enxuto (1 página) |
| 3 | [`etapa-3-spec.md`](./fase-0-negocio-e-requisitos/etapa-3-spec.md) | ⭐ Spec técnica: máquina de estados, resiliência finita, masking exato, contrato LLM, endpoints, 20 ataques, casos C1-C6 |
| 3 | [`etapa-3-tasks.md`](./fase-0-negocio-e-requisitos/etapa-3-tasks.md) | 17 tasks em 5 épicos + grafo de dependências |
| 3 | [`etapa-3-template-ticket.md`](./fase-0-negocio-e-requisitos/etapa-3-template-ticket.md) | Template de ticket autocontido + checklist de pronto |

Contexto versionado do repo: [`../AGENTS.md`](../AGENTS.md) — fontes de verdade,
regras invioláveis e protocolo para agentes de IA.

## Apêndices e certificação

| Doc | Conteúdo |
|---|---|
| [`apendice-a-entrega-modular-scrum.md`](./apendice-a-entrega-modular-scrum.md) | Sprints 1-2 sem · fatias verticais banco→API→front · preview Vercel · evidência visual · aceite humano por feature |
| [`apendice-b-normas-seguranca.md`](./apendice-b-normas-seguranca.md) | OAuth 2.1+OIDC/PKCE · RBAC servidor · RLS por tenant · rate-limit/WAF · DTO como fronteira · OWASP Top 10 por release |
| [`auditoria-final.md`](./auditoria-final.md) | Certificação item a item vs desafio + 22 portões (evidências executadas) |

## Índice de artefatos — Fase 1

| Etapa | Artefato | Conteúdo |
|---|---|---|
| 4 | [`etapa-4-arquitetura-c4.md`](./fase-1-design-e-contratos/etapa-4-arquitetura-c4.md) | C4 níveis 1-3 · monolito modular · regras de dependência · gatilhos de extração |
| 4 | [`adr/README.md`](./fase-1-design-e-contratos/adr/README.md) | Índice dos 8 ADRs (contexto, decisão, alternativas, consequências) |
| 5 | [`etapa-5-contratos.md`](./fase-1-design-e-contratos/etapa-5-contratos.md) | Fluxo API-first: lint/codegen/mock/drift · semver de contrato · gates |
| 5 | [`../../openapi/agent-api.yaml`](../../openapi/agent-api.yaml) | Contrato inbound (7 endpoints, RFC 7807, ULID, exemplos ricos) — **na raiz do repo** |
| 5 | [`../../openapi/quote-api.yaml`](../../openapi/quote-api.yaml) | Contrato do consumidor (legado as-consumed: 200/400/422/5xx) — **na raiz** |
| 6 | [`etapa-6-erros-resiliencia.md`](./fase-1-design-e-contratos/etapa-6-erros-resiliencia.md) | RFC 7807 + correlation ID · catálogo de erros estáveis · matriz de resiliência por dependência (legado/LLM/DB) · idempotência · front error states |
| 7 | [`etapa-7-i18n.md`](./fase-1-design-e-contratos/etapa-7-i18n.md) | ADR-0009 pt-BR único · catálogo único API↔front · formatos centralizados · lint zero-string · pseudo-locale |
| 7 | [`../../messages/pt-BR.json`](../../messages/pt-BR.json) | Catálogo v1: `agent.*` (24 canônicas) · `api.erro.*` (6) · `ui.*` (~30) — **na raiz do repo** |
| — | [`deploy-demo.md`](./deploy-demo.md) | **Runbook dos seus 15 min**: branch protection, secrets, Railway/Vercel, reativação dos pipelines, rehearsal de rollback + decisão Postgres= dívida |
| — | [`testar-local.md`](./testar-local.md) | Como rodar e testar TUDO local (sem Docker) — C1..C6, testes, evals, TRA |
| 8 | [`etapa-8-modelo-de-dados.md`](./fase-1-design-e-contratos/etapa-8-modelo-de-dados.md) | ERD DBML (4 tabelas + 4 enums) · Alembic + expand-migrate-contract · purga LGPD · restore testado |
| 9 | [`etapa-9-mensageria.md`](./fase-1-design-e-contratos/etapa-9-mensageria.md) | ADR-0010 sem broker · outbox transacional · worker retry_quote (lease/SKIP LOCKED) · DLQ · 6 eventos públicos versionados (PII-safe) |
| 10 | [`etapa-10-threat-model.md`](./fase-1-design-e-contratos/etapa-10-threat-model.md) | STRIDE 16 ameaças · política de segredos + rotação · auth entre serviços · ASVS L1 · scans obrigatórios (gitleaks/CodeQL/semgrep/audit) · OWASP LLM |

## Índice de artefatos — Fase 2

| Etapa | Artefato | Conteúdo |
|---|---|---|
| 11 | [`fase-2.../etapa-11-estrutura-repo.md`](./fase-2-fundacao-de-engenharia/etapa-11-estrutura-repo.md) | Monorepo materializado (ADR-0011) · AGENTS.md v2 · Makefile · devcontainer · quiz de onboarding |
| 12 | [`fase-2.../etapa-12-docs-vivas.md`](./fase-2-fundacao-de-engenharia/etapa-12-docs-vivas.md) | Geração vs. prosa · VitePress+GH Pages · Diátaxis |
| 12 | [`tutorial.md`](./tutorial.md) · [`how-to.md`](./how-to.md) · [`referencia.md`](./referencia.md) · [`runbooks.md`](./runbooks.md) · [`diagramas-as-code.md`](./diagramas-as-code.md) | Portal Diátaxis + Mermaid (estado, containers, turno) |
| 13 | [`fase-2.../etapa-13-padronizacao.md`](./fase-2-fundacao-de-engenharia/etapa-13-padronizacao.md) | ruff+import-linter · ESLint(jsx-no-literals)+Prettier · pre-commit · commitlint gitmoji · catraca zero-aviso |
| 14 | [`fase-2.../etapa-14-testes-unificados.md`](./fase-2-fundacao-de-engenharia/etapa-14-testes-unificados.md) | Matriz de cobertura única · TDD humano↔IA · Playwright C1-C6+smoke+visual · mutmut ≥60% · Pact-like decidido |

## Índice de artefatos — Fase 3

| Etapa | Artefato | Conteúdo |
|---|---|---|
| 15 | [`fase-3.../etapa-15-containers.md`](./fase-3-build-e-release/etapa-15-containers.md) | Multi-stage não-root · imagem única multi-destino · compose com perfis + seed e2e · hadolint/trivy gates |
| 16 | [fase-3.../etapa-16-cicd.md](./fase-3-build-e-release/etapa-16-cicd.md) | 10 gates com classe de defeito | 4 workflows Actions | rollback automatico (LAST_GOOD_TAG) | branch protection + CODEOWNERS |
| 17 | [fase-3.../etapa-17-ambientes.md](./fase-3-build-e-release/etapa-17-ambientes.md) | 3 ambientes par-idade-por-construcao | infra/ tofu (modulo railway-stack + envs) | plan-em-PR + drift diario | staging adotado |
| 18 | [fase-4.../etapa-18-observabilidade.md](./fase-4-operacao-e-loop/etapa-18-observabilidade.md) | OTel SDK unico (correlation ID costura front-banco) | 4 SLOs com error budget | 7 alertas com runbook | ensaio de incidente |
| 19 | [fase-4.../etapa-19-evals.md](./fase-4-operacao-e-loop/etapa-19-evals.md) | 5 evals (E1-E5) + TRA | golden/ versionado (20 ataques em jsonl) | prompt-e-codigo (job bloqueante) | FinOps: 2 alertas de orcamento |
| 20 | [fase-4.../etapa-20-governanca-ia.md](./fase-4-operacao-e-loop/etapa-20-governanca-ia.md) | trilha auditavel ticket-PR-revisao | ai-logs com dupla barreira | prompts/ semver+CHANGELOG (system_v1.md materializado) | SBOM syft+allowlist |
| 21 | [fase-4.../etapa-21-retro.md](./fase-4-operacao-e-loop/etapa-21-retro.md) | postmortem blameless 48h + template | DORA por release (step no CI) | loops reais L1-L3 registrados | RETRO.md na raiz |

## Checklist das etapas (guia atualizado — 21 etapas, 01/09/2026)

| # | Etapa | Portão de validação | Status |
|---|---|---|---|
| 1 | Modelo de negócio e domínio | Responder em 1 frase: para quem, qual dor, como se mede sucesso | ✅ Validada 01/09/2026 |
| 2 | Requisitos funcionais e NFRs | Cada requisito é testável e rastreável | ✅ Validada 01/09/2026 |
| 3 | Especificação (spec-driven) | Spec cobre fluxo feliz + alternativos + handoff | ✅ Validada 01/09/2026 |
| 4 | Arquitetura e ADRs | Toda decisão estrutural com ADR + containers atualizado | ✅ Validada 01/09/2026 |
| 5 | Contratos API-first | Lint passa; codegen sem ajuste manual; contract tests no CI | ✅ Validada 01/09/2026 (gates viram jobs na Etapa 16) |
| 6 | Tratamento de erros e resiliência **(nova)** | Matriz de erros cobre 100% dos fluxos alternativos | ✅ Validada 01/09/2026 |
| 7 | Internacionalização (i18n) **(nova)** | Estratégia definida (escopo PT-BR + centralização) | ✅ Validada 01/09/2026 |
| 8 | Modelo de dados e migrações | Schema versionado | ✅ Validada 01/09/2026 |
| 9 | Mensageria e eventos | ADR: sem broker (outbox/tabela) | ✅ Validada 01/09/2026 |
| 10 | Segurança e threat modeling | STRIDE + prompt injection + PII + segredos | ✅ Validada 01/09/2026 |
| 11 | Estrutura do repo e context engineering | Monorepo + AGENTS.md | ✅ Validada 01/09/2026 |
| 12 | Documentação viva (docs dinâmicas) **(nova)** | Docs geradas/verificadas por pipeline | ✅ Validada 01/09/2026 |
| 13 | Padronização automatizada de código | ruff/eslint/prettier no pre-commit + CI | ✅ Validada 01/09/2026 |
| 14 | Estratégia de testes unificados (TDD + Playwright) | Pirâmide + E2E browser + cobertura | ✅ Validada 01/09/2026 |
| 15 | Containers | Compose de dev completo | ✅ Validada 01/09/2026 |
| 16 | Pipeline CI/CD | Actions verde + gates das Etapas 5/13/14 | ✅ Validada 01/09/2026 |
| 17 | Ambientes e Infrastructure as Code | Plan revisado em PR · staging espelha prod · drift | ✅ Validada 01/09/2026 |
| 18 | Observabilidade | Trace ponta a ponta · alerta dispara · cada alerta com runbook | ✅ Validada 01/09/2026 |
| 19 | Avaliação contínua de IA (evals) | Eval bloqueia no CI · custo/conversa com alerta · prompt passa pela suíte | ✅ Validada 01/09/2026 |
| 20 | Governança da IA no processo | Exports sem segredos · 100% PRs com revisão · SBOM sem conflito | ✅ Validada 01/09/2026 |
| 21 | Retrospectivas e postmortems | Postmortem 48h · action items com dono · DORA por release | ✅ Validada 01/09/2026 — PROCESSO COMPLETO |

> **Mapeamento numeração antiga → nova** (docs escritos antes de 01/09 usam a
> antiga): 6→8 · 7→9 · 8→10 · 9→11 · 10→13 · 11→14 · 12→15 · 13→16 · 14→17 ·
> 15→18 · 16→19 · 17→20 · 18→21. Etapas novas: 6, 7 e 12.

> Legenda: ⚪ não iniciada · 🟡 aguardando validação · ✅ validada · Ⓘ futura

## Decisões já fechadas (pré-ADRs)

| ID | Decisão | Contexto |
|---|---|---|
| D1 | Front Next.js na Vercel | Chat de demo + log de execução vivo |
| D2 | Backend no Railway (agent-api + quote-api + Postgres) | quote-api não é alterado |
| D3 | TDD como metodologia | Lógica determinística primeiro |
| D4 | Dev local via docker compose | Paridade com a régua do desafio |

## Fontes de verdade

- Desafio original (insumos): `../namastex-fde-challenge/` — **somente leitura**
- Regras de negócio brutas: `namastex-fde-challenge/quote-service/data/plans.json`
- Dicionário do dataset: `namastex-fde-challenge/dataset/DICIONARIO.md`
