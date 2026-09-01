# Plano de Implementação — Escopo Imutável (T-01 → T-17)

> **Baseline congelada em 01/09/2026.** Este documento é o contrato de
> execução: o escopo do desafio é **imutável** — fontes: README do desafio
> (`namastex-fde-challenge/`), PRD (`fase-0/etapa-3-prd.md`), spec
> (`fase-0/etapa-3-spec.md`) e checklist final (22 portões). Qualquer mudança
> de escopo exige decisão explícita do dono do projeto e vira ADR/nota de
> revisão — **zero scope creep silencioso**.
>
> **Gate de cobertura atualizado por decisão do dono (01/09/2026): **100% na
> lógica determinística** (90→99→100 — NFR-16 revisado; ver §1.3).

---

## 1. Revisão da documentação (pré-implementação) — resultado

| Verificação | Resultado |
|---|---|
| Checklist 21 etapas × artefatos no repo | ✅ 21/21 com portão registrado |
| 22 portões do guia × nossas etapas | ✅ mapeados (item 11 = tasks da Etapa 3) |
| Links pós-migração (openapi/, messages/ na raiz) | ✅ corrigidos nas Etapas 11-12 |
| Consistência de números entre docs (breaker 5/30s/2, timeout 3s, retry 3, rate 10/min, LLM 15s/1x) | ✅ única fonte: spec §2 + etapa-6 §4.1; demais citam |
| **Gate de cobertura** | 🔧 **divergência corrigida nesta revisão**: 90→**99%** (aplicado em NFR-16, `pyproject.toml`, `pr.yml`, etapa-14 e AGENTS.md) |
| Workflows CI | ✅ triggers automáticos desativados até bootstrap (T-01) — comentário de reativação em cada arquivo |
| Escopo | ✅ congelado abaixo (§2) — imutável |

## 2. Escopo imutável do desafio (baseline)

### ENTREGA OBRIGATÓRIA (do README do desafio — intocável)
1. **Agente** que atende ponta a ponta: conversa → qualifica → cota via `/quote` → decide (resolve ou **handoff com critério explícito**).
2. **Repo público** com o código (✅ publicado).
3. **README** de como rodar + decisões (✅ skeleton; finaliza na entrega).
4. **Log de uma execução completa** (C1 exportável — T-13).
5. **`ai-logs/`** com as conversas com IAs, sanitizado (contínuo; fecha T-17).

### REGRAS DO DESAFIO (ambiente dado, não mudam)
- `/quote` falha 20% · lenta 10% (8s) · `QUOTE_SEED` determina — **tratar como parte do produto**.
- `plans.json` é a única fonte de planos/preços-regras.
- Dataset sintético = PII tratada como real (masking Silver).
- `quote-service/` e o dataset original: **somente leitura**.

### FORA DO ESCOPO (decisões já registradas — não implementar)
Emissão de apólice/boleto · WhatsApp real · multi-idioma · auth de usuário final ·
mudança no broker (Postgres é o transporte) · framework de agente externo.

## 3. Fluxo TDD operacional (o contrato humano↔IA em prática)

```
1. VERMELHO: teste que codifica a spec (casos nomeados, dados do golden/spec §)
   → commit ✅ test(scope): specify <comportamento> (spec §X)
2. VERDE: implementação mínima → refatora → cobertura ≥99% do módulo
   → commit ✨ feat(scope): implement <comportamento> (spec §X)
3. GATES locais: ruff · import-linter · pytest --cov-fail-under=99
4. Push direto na main é aceito APENAS enquanto solo/pre-bootstrap
   (branch protection ativa com os primeiros PRs reais — T-14)
```

## 4. Marcos e tasks (ordem sem ciclos — grafo da etapa-3)

| Marco | Tasks | Porta que fecha | Gates de aceitação |
|---|---|---|---|
| **M1 Fundações** | T-01 scaffold · T-02 masking · T-03 ACL(resiliência) | 5·10·12·13·14·16·17 (gates ligam) | health 200 no compose · masking 100% idempotente · simulação 1000 cotações ≥97% (NFR-04) · breaker 5/30s/2 com relógio fake |
| **M2 Motor** | T-04 state machine · T-05 LLM+price-guard · T-06 persistência · T-07 API HTTP | 9 (kill/DLQ) | 4 invariantes da spec §1.3 · price-guard regenera→fallback · C1 integração verde |
| **M3 Dados/IA** | T-08 silver · T-09 evals E1/E2 · T-10 adversarial | 20 | masking 100% no scan · E1 ≥90% · E2 ≥95% · E3 0/20 |
| **M4 Front** | T-11 chat+storybook · T-12 fila · T-13 export | 7(exec) 13(storybook) | Lighthouse ≥90 · mobile 360px · export C1 |
| **M5 Release** | T-14 CI completo · T-15 deploy+rehearsal · T-16 bateria TRA+log · T-17 ai-logs+RETRO | 8·15(exec)·17·18·21·22 | rollback ensaiado · TRA ≥70% · restore testado · ensaio de incidente |

**Definição global de pronto**: todos os gates verdes + cobertura **≥99%**
(lógica determinística) + doc viva atualizada + linha no checklist-final.

## 5. Regras de execução

1. Spec ambígua durante a implementação → **para e corrige a spec primeiro** (AGENTS.md).
2. Task só abre pelo template (contexto, DoD, spec §, primeiro teste nomeado).
3. Commits gitmoji+inglês (commitlint) — micro-commits atômicos.
4. Checkpoint: ao fim de cada marco, reavaliar `checklist-final-implantacao.md`
   (🟜→🟢 com evidência linkada) e atualizar RETRO/DORA.
5. `ai-logs/`: export das sessões de implementação commitado ao fim de M1/M3/M5 (sanitizado).

---

*Início imediato: **T-01 (scaffold) + T-02 (masking, primeiro ciclo TDD completo)**.*
