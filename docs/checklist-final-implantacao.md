# Checklist Final — Antes de Implantar (os 22 portões)

> Revisão final do processo (01/09/2026). **Legenda:**
> 🟢 **pronto** — portão atendido com evidência existente hoje.
> 🟜 **design fechado, evidência na implementação** — mecanismo completo e
> materializado; a última evidência exige código/infra rodando (task T-XX
> responsável). Conforme o guia: *"linha pendente é risco aceito
> conscientemente"* — cada 🟜 declara o risco e a task que o resolve.
>
> **Mapeamento:** itens 1-10 e 12-22 = Etapas 1-21 · item 11 (spec de
> desenvolvimento) = tasks da Etapa 3 (`etapa-3-tasks.md`).

| N | Portão | Status | Evidência | Risco aceito / task que fecha |
|---|---|---|---|---|
| 1 | Modelo de negócio | 🟢 | Frase do portão (para quem/dor/métrica) — etapa-1 §7 | — |
| 2 | Requisitos e NFRs | 🟢 | 18 NFRs com nº+instrumento · 16 US testáveis · matriz rastreabilidade | — |
| 3 | Especificação | 🟢 | Spec §1-12: estados, parâmetros, formatos, 20 ataques, C1-C6 | — |
| 4 | Arquitetura e ADRs | 🟢 | 11 ADRs c/ alternativas · C4 níveis 1-3 · regras de dependência | — |
| 5 | Contratos API | 🟜 | 2 OpenAPI 3.1 + fluxo lint/codegen/drift desenhado | Gates bloqueiam no 1º pipeline — **T-01** |
| 6 | Erros e resiliência | 🟢 | 13 erros catalogados · matriz 4 dependências · correlation ID no contrato | — |
| 7 | Internacionalização | 🟜 | Catálogo 60+ chaves · ADR-0009 · pseudo-locale especificado | jsx-no-literal AST + pseudo-locale rodam sobre código — **T-02/T-11** |
| 8 | Dados e migrações | 🟜 | ERD DBML · EMC · purga LGPD · procedimento restore | up/down em dados reais + restore ensaiado — **T-06/T-15** |
| 9 | Mensageria | 🟜 | ADR-0010 · lease/SKIP LOCKED · DLQ · 2 testes nomeados | `test_worker_kill_and_resume` + `test_poison_message_dlq` verdes — **worker (Épico B)** |
| 10 | Segurança | 🟜 | STRIDE 16 ameaças · política segredos · scans definidos blocker | gitleaks/CodeQL/audit executam no repo real — **T-01** |
| 11 | Spec de desenvolvimento | 🟢 | 17 tasks · grafo sem ciclos (etapa-3) · teste mapeado por item (matriz etapa-2 §5) | — |
| 12 | Repo e contexto | 🟜 | AGENTS.md v2 · quiz 10 perguntas · onboarding ~55min | Quiz verificado com 1º agente de implementação — **T-01+** |
| 13 | Documentação viva | 🟜 | Portal VitePress + 5 runbooks + Mermaid + Redoc (`make docs-*`) | Publicação real (GH Pages) no 1º merge na main — **repo GitHub** |
| 14 | Padronização | 🟜 | ruff/import-linter/eslint/commitlint gitmoji · catraca zero-aviso | Hooks ativam no `git init`; CI valida range do PR — **T-01** |
| 15 | Testes unificados | 🟜 | Matriz 6 camadas · Playwright C1-C6 escrito · mutmut alvo 60% | Números reais (coverage/mutation/e2e pré-release) — **Épico A→E** |
| 16 | Containers | 🟜 | Multi-stage não-root (10001) · imagem única · compose + perfis · trivy/hadolint | Scan limpo + `make dev` completo com app/ — **T-01** |
| 17 | CI/CD | 🟜 | 4 workflows · 10 gates · rollback automático LAST_GOOD_TAG | Ativação (repo+branch protection) + rehearsal de rollback — **T-14/T-15** |
| 18 | Ambientes e IaC | 🟜 | tofu módulo+envs · plan-em-PR · apply c/ approval · drift diário | 1º apply real + 1ª detecção de drift — **T-15** |
| 19 | Observabilidade | 🟜 | 4 SLOs · 9 alertas↔runbook · OTel correlation ID ponta a ponta | 1º trace real + ensaio de incidente (4 simulações) — **T-07/T-15** |
| 20 | Evals de IA | 🟜 | golden/ (20 ataques jsonl + seeds) · job bloqueante · FinOps c/ 2 alertas | Números E1-E4 + custo/conversa medidos — **T-09/T-10** |
| 21 | Governança de IA | 🟜 | Trilha auditável · dupla barreira ai-logs · prompt v1+changelog · SBOM allowlist | ai-logs reais acumulam na implementação · SBOM no 1º release |
| 22 | Retro e postmortems | 🟢 | RETRO.md viva (loops L1-L3 reais) · template blameless 48h · DORA step no CI | postmortem real = pós-incidente (ensaio T-15 gera o 1º exercício) |

## Veredicto da revisão

- **22/22 portões endereçados** — 7 totalmente 🟢, 15 🟜.
- **Nenhum 🟜 é lacuna de design**: todos têm mecanismo materializado no repo e
  uma task T-XX dona da última evidência. O risco aceito conscientemente é
  único e explícito: **os artefatos de execução (gates rodando, números de
  evals, traces, SBOM) só existem com o código implantado** — que é exatamente
  o próximo marco (T-01..T-17).
- **Ordem de fechamento dos 🟜** (por dependência): T-01 (repo+CI ligam os
  gates 5/10/12/13/14/16/17) → Épico B (9/15 parcial) → T-09/T-10 (20) →
  T-15 rehearsal (8/17/18/19/22 exercício) → entrega.

> Este arquivo é reavaliado ao fim de cada épico (regra registrada na RETRO) —
> 🟜 vira 🟢 com a evidência linkada.
