# Etapa 14 — Estratégia de Testes Unificada (TDD + Playwright)

> Fase 2 (fecha a fase) · **Uma pirâmide para o produto inteiro, não uma por
> camada.** TDD com divisão de papéis: **o teste que codifica a spec é do
> autor; a implementação que o satisfaz é da IA.**

---

## 1. Matriz de cobertura (uma estratégia, duas camadas) — preenchida

| Camada | API (agent-api) | Front (apps/web) | Onde roda | Orçamento |
|---|---|---|---|---|
| **Unitário** | regra pura sem I/O: masking (§3), state machine (invariantes §1.3), breaker/backoff (§2, relógio fake), price-guard (§4.3), validação de campos (§4.4), regras de handoff, `format_brl` — `tests/unit/` (pytest `@unit`) | hooks/utils: `format.ts`, `t()` do catálogo, correlation-id — Vitest `src/**/*.test.ts` | pre-commit (rápidos) + CI **bloqueante** | ~1 min |
| **Integração** | endpoint + **Postgres real** (compose): C1-C6 parciais via `httpx.AsyncClient`, idempotency replay, LGPD delete cascata, worker kill/resume + poison→DLQ (portão Etapa 9) — `tests/integration/` (`@integration`) | cliente tipado contra **Prism mock** do contrato — Vitest | CI **bloqueante** | ~3 min |
| **Contrato** | **provedor**: drift `oasdiff` (openapi.json vs YAML) + fixtures 200/400/422/5xx validadas contra `quote-api.yaml` (consumidor do legado) + eventos vs `schemas/eventos/*.v1.json` — `tests/contract/` (`@contract`) | **consumidor**: types GERADOS (codegen `--check`) + fixtures TS validando exemplos do YAML | CI **bloqueante** | ~1 min |
| **Componente** | — | Testing Library **por papel semântico** (sem testar implementação): QuoteCard exibe prêmio/franquia/carência, HandoffBanner, estados idle→pensando→cotando→erro, error boundary com correlation ID | CI | ~1 min |
| **E2E** | **via UI contra o compose completo** (agent-api+quote-api+Postgres com taxas reais de falha → `QUOTE_SEED=42` p/ determinismo) | idem — `e2e/critical-flows.spec.ts`: **C1-C6** + mobile viewport 360px + visual regression (QuoteCard/chat) | **CI noturno + pré-release** (bloqueia deploy) | ~6 min |
| **Smoke** | `GET /health` (agent+legado) + `POST /conversations` + 1 turno | home carrega + fluxo principal abre | **pipeline pós-deploy** (demo real) | <1 min |
| **Evals** | suite de IA (Etapa 19): extração/handoff/**20 ataques**/zero-preço | — | CI (FakeLLM) + noturno (LLM real) | ~3 min |

**Pact — decisão registrada (inline):** com **1 consumidor** e contrato
centralizado, o efeito Pact ("quebra antes do deploy") já é obtido pelo trio
**drift test + codegen `--check` + fixtures dos dois lados** — adotar
pact-python/pact-js agora adicionaria infra sem ganho. Gatilho de adoção:
surgir 2º consumidor da agent-api (app mobile, outro BFF).

## 2. Estrutura no repo (materializada)

```
services/agent-api/tests/
├── unit/         (regra pura — TDD estrito; coverage gate 99% — NFR-16)
├── integration/  (compose: Postgres real + worker + endpoints)
└── contract/     (drift + fixtures do legado + eventos vs schemas)

apps/web/src/**        (*.test.ts utils · *.test.tsx componentes Testing Library)
e2e/                   (Playwright: playwright.config.ts + critical-flows + smoke)
evals/                 (Etapa 19 — separada por natureza: valida IA, não código)
```

Marcadores pytest já configurados (Etapa 13): `unit | contract | integration | evals`.

## 3. TDD — divisão de papéis (o contrato humano↔IA)

```
1. AUTOR escreve o teste que codifica a spec
   (dado do caso, asserts com as keywords do catálogo, relógio fake onde
    houver tempo) — commit ✅ test(scope): specify <comportamento da spec §X>
2. IA implementa até o verde em passos mínimos (1 ciclo por commit)
3. AUTOR revisa contra a spec (não contra o gosto): o PR cita a seção
4. MUTAÇÃO espreme (§5): mutmut mata os testes fracos → volta pro passo 1
```

O template de ticket (Etapa 3) já exige o nome do primeiro teste na DoD —
esta etapa fecha o ciclo: **spec → teste (humano) → verde (IA) → mutação**.

## 4. Playwright — E2E, smoke e visual regression

- **Config** (`e2e/playwright.config.ts`): baseURL do compose (`:3000` do
  front dev) · projetos: `chromium` desktop + **`mobile-chrome` 360px**
  (NFR-18) · `QUOTE_SEED=42` no compose ⇒ as falhas do legado são
  **determinísticas** no E2E (cenários C5 reproduzíveis) · retry 1×.
- **Fluxos críticos = C1-C6** (spec §11) — 6 specs, a jornada completa.
- **Visual regression**: `toHaveScreenshot` em QuoteCard/HandoffBanner/chat
  (`maxDiffPixels` calibrado — pseudo-locale da Etapa 7 vira um dos cenários).
- **Smoke pós-deploy** (pipeline da demo real): health + home + 1 turno
  completo — falha = rollback automático do deploy (Etapa 16).
- **Quando roda:** noturno + **pré-release sempre** (portão). PR comum fica
  com unit+integration+contract+componente (NFR-17: pipeline < 5 min).

## 5. Mutation testing — "os testes testam?"

| Item | Decisão |
|---|---|
| Ferramenta | **mutmut** (núcleo Python: masking, state machine, breaker, price-guard, handoff) |
| Alvo | **score ≥ 60% no núcleo** (régua do guia;coverage ≥90% continua sendo o gate de PR — mutação mede QUALIDADE dos asserts) |
| Quando roda | **noturno** (é lento; nunca no PR) — score abaixo → issue "teste fraco em <módulo>" → autor escreve o teste que falta (papel humano, §3) |
| Front | Stryker: N/A nesta fase (custo/benefício com ~15 utils) — registrado; adotar se o front crescer |

## 6. Suíte rápida (<10 min — portão; PR <5 min — NFR-17)

| Job | Conteúdo | Meta |
|---|---|---|
| `PR` | unit + integration + contract + componente + lint + codegen-check | **< 5 min** |
| `noturno` | tudo + e2e (C1-C6) + visual + mutation + evals-LLM-real | **< 10 min** |
| `pré-release` | tudo + e2e | < 8 min |
| `pós-deploy` | smoke | < 1 min |

## 7. ✅ Portão de validação da Etapa 14

| Critério | Status |
|---|---|
| Matriz preenchida no repo e executando | 🟡 matriz completa (§1) + estrutura dirs + configs; "executando" com o primeiro código (Épico A) |
| E2E Playwright antes de cada release | 🟡 config + specs C1-C6 materializados (`e2e/`); job pré-release na Etapa 16 |
| Mutation score ≥60% no núcleo | 🟡 mutmut configurado como job noturno; medida a partir do primeiro módulo núcleo |
| Suíte rápida <10 min | ✅ orçamento por job com metas (§6); PR <5min já era NFR-17 |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Fase 2 fechada; Etapa 15 liberada)*
