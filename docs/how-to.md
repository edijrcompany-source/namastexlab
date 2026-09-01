# 🔧 How-to — Tarefas do dia a dia

> Diátaxis/How-to: receitas para tarefas concretas. Todas partem de regras
> já decididas (ADRs/spec) — aqui é o "como", não o "porquê".

## HT-01 — Adicionar/modificar endpoint ou campo de API

1. **Spec/contrato primeiro**: edite `openapi/agent-api.yaml` (regras semver:
   aditivo = minor; remover/estreitar = major — Etapa 5 §4).
2. `make contracts-lint && make codegen` → types do front regenerados
   (**nunca** editar `apps/web/src/types/api.d.ts` à mão).
3. Implemente no `services/agent-api` (TDD) — o drift test falha se o
   `openapi.json` da app divergir do YAML.
4. Se breaking: novo ADR + nota no PR.

## HT-02 — Adicionar evento (interno ou público)

1. Evento interno (rastreabilidade): adicione ao enum da spec §5.2 **e** ao
   `TipoEvento` do contrato — PR na spec primeiro (AGENTS.md regra "novo
   evento: PR na spec antes do código").
2. Evento público (integração): crie `schemas/eventos/<nome>.v1.json`
   (envelope Etapa 9 §3 — `event_version`, PII-safe: só `cep_prefixo`).
3. Teste: fixture do evento validada contra o schema no CI.

## HT-03 — Adicionar mensagem de erro ao catálogo

1. Crie a chave em `messages/pt-BR.json` → `api.erro.<slug>` (`title` + `detail`).
2. O slug vira o `type` do problem+json (código estável — Etapa 6 §2).
3. Adicione o caso no teste do catálogo (completude AST — Etapa 7 §5).

## HT-04 — Adicionar string de tela (front)

1. **Só** em `messages/pt-BR.json` → `ui.*` (eslint jsx-no-literals bloqueia
   string crua — Etapa 7 §5).
2. Interpole com `{placeholder}` — concatenação é proibida (ADR-0009).
3. `make pseudo-locale` para validar comprimento/placeholders.

## HT-05 — Criar uma migration

1. `alembic revision` — 1 PR = 1 revision; **`down()` obrigatório** (Etapa 8 §4).
2. Mudança quebrante? Siga expand-migrate-contract em 3 deploys.
3. CI roda `upgrade head → downgrade base → upgrade head` com seed Silver.

## HT-06 — Rodar evals localmente

```bash
make bronze && make silver   # dataset (seed 42) mascarado
make evals                   # extração ≥90% · handoff ≥95% · 20 ataques (0/20)
```

## HT-07 — Atualizar a documentação

- **Gerada** (API/eventos/catálogo/comandos): não se escreve — regenera no
  build do portal (Etapa 12 §1).
- **Prosa** (how-to/runbook/ADR): edite aqui — o portal publica no próximo
  merge. PR que muda comportamento sem doc = incompleto.
