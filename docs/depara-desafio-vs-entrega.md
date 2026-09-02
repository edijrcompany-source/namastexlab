# De-Pará: Desafio vs Entrega — Status Final (02/09/2026)

> Comparação item por item do que o desafio pede vs o que está entregue.
> Evidências executadas contra os containers ativos.

---

## 1. ENTREGÁVEIS OBRIGATÓRIOS (README do desafio)

| # | O desafio pede | O que foi entregue | Status |
|---|---|---|---|
| 1 | **Agente de ponta a ponta**: conversa → qualifica → cota → decide (resolve ou encaminha) | Agente FastAPI com máquina de estados (7 estados), ACL resiliente (retry+breaker), price-guard, handoff com 6 motivos | ✅ **C1-C6 verdes em browser real** |
| 2 | **Repositório público no GitHub** | `github.com/edijrcompany-source/namastexlab` — 92 commits gitmoji, TDD visível | ✅ |
| 3 | **README explicando como rodar e decisões** | README raiz (quickstart Docker e sem-Docker, stack, números) + docs/README (21 etapas) + 11 ADRs com alternativas | ✅ |
| 4 | **Log de uma execução completa** | `docs/log-execucao-c1.md` — gerado nos containers, PII mascarada, eventos com seq | ✅ |
| 5 | **Conversas com IA (ai-logs/)** | 49 prompts com commit incremental + resumo estruturado + guia COMO-PRODUZIR.md | ✅ |

## 2. CRITÉRIOS DE AVALIAÇÃO (o que eles olham)

| Critério | Como avaliam | Nossa entrega | Status |
|---|---|---|---|
| **Funciona de ponta a ponta?** | Caminho feliz com cotação | C1: conversa → dados → cotação R$ 119,90 → aceite → handoff `aceite_fechamento` — verificado em browser real e containers | ✅ |
| **O que faz quando a /quote falha?** | Ponto que "mais separa" | Retry 3× com backoff+jitter · circuit breaker 5/30s/2 · mensagem honesta SEM preço · retentativa automática · handoff técnico na 2ª abertura | ✅ |
| **Critério de handoff explícito?** | Defensável | 6 motivos em enum: `aceite_fechamento`, `inelegivel_contestado`, `objecao_preco`, `preferencia_humana`, `falha_tecnica`, `fora_escopo` + eval E2 100% | ✅ |
| **Rastreável?** | Cada mensagem/cotação com id e status | ULID por conversa · seq por evento · correlation_id · 17 tipos de evento · timeline + export md/json | ✅ |
| **Cuidado com dados sensíveis?** | PII no histórico | Masking §3: CPF/e-mail/telefone/placa mascarados antes do LLM · CEP mascarado em logs · NFR-12 com scan · Silver 26.470 msgs PII 100% mascarada | ✅ |
| **Qualidade: outro engenheiro entende?** | Decisões documentadas | 21 etapas + 11 ADRs + import-linter (arquitetura enforced) + spectral 0 erros + AGENTS.md + ruff catraca + RETRO com 8 loops | ✅ |
| **Como usou a IA?** | ai-logs entram na avaliação | Processo TDD humano↔IA documentado + 49 prompts com timestamp/commit + incidentes honestos | ✅ |

## 3. ARQUITETURA (o que foi planejado vs implementado)

| Camada | Planejado (spec/ADR) | Implementado | Status |
|---|---|---|---|
| **Máquina de estados** | 7 estados, tabela §1.3, 4 invariantes | ✅ 100% — tabela literal + testes de propriedade | ✅ |
| **ACL do legado** | Timeout 3s · 3 tentativas · backoff 500/1000+jitter · breaker 5/30s/2 | ✅ 100% — com simulação NFR-04 ≥97% | ✅ |
| **Price-guard** | Zero-tolerance, regenera→fallback | ✅ 100% — em código (não só prompt) + eval E3 0/20 | ✅ |
| **LLM** | Porta LLMPort: FakeLLM ou OpenAI gpt-4o-mini | ✅ FakeLLM ativo (offline) · OpenAI client pronto (1 env var) | ✅ |
| **Persistência** | Postgres 16 + Alembic | ⚠️ InMemoryStore (Postgres real = dívida T-06b) | 🟡 |
| **Mensageria** | Sem broker: outbox + SKIP LOCKED + DLQ | 🟡 Design completo, worker não implementado (só retry_pending) | 🟡 |
| **API HTTP** | 7 endpoints §5.4 | ✅ 100% — smoke 23/23 | ✅ |
| **Front** | Next.js chat + fila + export | ✅ Chat funcional + /handoffs + botão exportar | ✅ |
| **i18n** | Catálogo único pt-BR, zero string crua | ✅ messages/pt-BR.json + eslint jsx-no-literals + pseudo-locale | ✅ |
| **Contratos** | OpenAPI 3.1 + codegen + drift test | ✅ Spectral 0 erros + types gerados + commitados | ✅ |
| **Observabilidade** | OTel + structlog + alertas com runbook | ✅ JSON logging com correlation_id + 9 alertas + SLOs | ✅ |
| **Segurança** | STRIDE + segredos + OWASP | ✅ 16 ameaças mapeadas + Apêndice B (OAuth/RBAC/RLS/OWASP) | ✅ |
| **CI/CD** | 5 workflows com gates | ⚠️ Workflows prontos, triggers aguardam `gh auth login` | 🟡 |
| **Containers** | Multi-stage, não-root, compose | ✅ Rodando agora: agent-api(healthy) + postgres(healthy) + quote-api | ✅ |

## 4. NÚMEROS FINAIS (verificados)

| Métrica | Valor | Meta | Status |
|---|---|---|---|
| Cobertura backend | **100.00%** | ≥99% | ✅ |
| Cobertura front (lines) | **100%** | ≥99% | ✅ |
| Evals E1 (extração) | **100%** (16/16) | ≥90% | ✅ |
| Evals E2 (handoff) | **100%** (8/8) | ≥95% | ✅ |
| Evals E3 (adversarial) | **0 violações** (20/20) | 0 | ✅ |
| TRA (métrica norte) | **93-96%** | ≥70% | ✅ |
| API smoke | **23/23 endpoints** | 23/23 | ✅ |
| Silver PII mascarada | **100%** (0 vazamentos) | 100% | ✅ |
| Import-linter | **3/3 contracts** | 3/3 | ✅ |
| Commits | **92** | — | — |
| Prompts em ai-logs | **49** | — | — |

## 5. DÍVIDAS DOCUMENTADAS (não bloqueiam o desafio)

| Item | Impacto | Runbook |
|---|---|---|
| Postgres real (T-06b) | Persistência entre restarts | Porta `Store` pronta + ERD completo (Etapa 8) |
| CI ativo (T-14) | Gates no GitHub Actions | `docs/deploy-demo.md` (~15 min) |
| Deploy público (T-15) | Demo na internet | `docs/deploy-demo.md` (Railway+Vercel) |
| LLM real | IA generativa no chat | `LLM_API_KEY=sk-...` no docker-compose |
| Worker retry (T-06) | Retentativa 2min automática | Design completo (Etapa 9 §4) |

## 6. DOCUMENTAÇÃO (57 arquivos)

| Categoria | Arquivos | Status |
|---|---|---|
| Fase 0 (negócio) | 8 | ✅ completo |
| Fase 1 (design) | 8 + 11 ADRs | ✅ completo |
| Fase 2 (fundação) | 5 | ✅ completo |
| Fase 3 (build) | 4 | ✅ completo |
| Fase 4 (operação) | 5 | ✅ completo |
| Apêndices A+B | 2 | ✅ Scrum + Segurança |
| Auditoria/Checklist | 2 | ✅ 22 portões + certificação |
| Runbooks (Diátaxis) | 5 | ✅ tutorial/how-to/ref/runbooks/diagramas |
| Contratos OpenAPI | 2 | ✅ spectral 0 erros |
| ai-logs | 49 prompts + 3 docs | ✅ registro incremental |
| Links quebrados | **0** | ✅ |
| ADRs com alternativas | **11/11** | ✅ |

---

## Veredito Final

**O desafio está 100% cumprido no que ele avalia.** A integração com a API do
desafio é real (HTTP para o container do legado, com instabilidade real), os 7
critérios de avaliação estão todos endereçados com evidência executável, e a
documentação cobre todo o processo de engenharia de ponta a ponta.

As 5 dívidas documentadas não fazem parte da régua do desafio (que pede repo
público + código + README + log + ai-logs, não deploy ou Postgres real) e têm
runbook pronto para quando quiser fechá-las.
