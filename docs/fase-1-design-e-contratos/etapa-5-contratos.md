# Etapa 5 — Contratos API-first

> Fase 1 · **O contrato existe antes do código.** Os YAMLs em `openapi/` são a
> fonte única da verdade das duas bordas HTTP do agent-api — inbound (nossa
> API) e outbound (legado).

---

## 1. Artefatos

| Arquivo | Papel | Direção |
|---|---|---|
| [`openapi/agent-api.yaml`](../../../openapi/agent-api.yaml) | Nossa API (7 endpoints, schemas, exemplos, RFC 7807) | inbound — nós proveemos |
| [`openapi/quote-api.yaml`](../../../openapi/quote-api.yaml) | Contrato **do consumidor**: o que esperamos do legado do desafio | outbound — nós consumimos |

## 2. O fluxo API-first (o compilador vira guardião)

```
 openapi/agent-api.yaml  (fonte única, versionada no git)
        │
        ├──▶ spectral lint ────────────── quality gate do contrato
        │
        ├──▶ openapi-typescript ─────────▶ apps/web/src/types/api.d.ts
        │     (types do front GERADOS; editar à mão = CI falha)
        │
        ├──▶ @stoplight/prism mock ──────▶ front anda ANTES do back existir
        │     (exemplos ricos já no YAML: cotação, handoff, falha)
        │
        └──▶ drift test (CI) ────────────▶ openapi.json exportado pela app
              FastAPI  vs  YAML canônico (oasdiff --breaking)
              qualquer divergência quebrante = build vermelho

 openapi/quote-api.yaml  (contrato do consumidor)
        │
        └──▶ contract tests: fixtures de 200/400/422/5xx validados contra o
              schema; client `quoting/` tipado por pydantic derivado daqui.
              Roda contra o legado REAL no CI (Efase 3) e contra mocks nos
              testes unitários — quebra de contrato detectada antes do deploy.
```

## 3. Ferramentas e comandos (executáveis desde já; gate no CI na Etapa 16)

| Ferramenta | Uso | Comando |
|---|---|---|
| **Spectral** (`@stoplight/spectral-cli`) | Lint dos contratos + ruleset próprio | `spectral lint openapi/*.yaml` |
| **openapi-typescript** | Codegen TS para o front | `openapi-typescript openapi/agent-api.yaml -o apps/web/src/types/api.d.ts` |
| **Prism** (`@stoplight/prism-cli`) | Mock server do contrato | `prism mock openapi/agent-api.yaml -p 4010` |
| **oasdiff** | Detecção de breaking changes (inbound drift) | `oasdiff breaking openapi/agent-api.yaml <(app export-openapi)` |
| **pytest + pydantic** | Contract tests do consumidor (outbound) | fixtures em `tests/contract/quote_api/` validados contra `quote-api.yaml` |

**Ruleset Spectral custom (mínimo):** toda operação com `operationId`; todo 2xx
com `examples`; todo erro com schema `Problem` (RFC 7807); schemas com
`required` explícito; proibido `additionalProperties: true` fora de
payloads-livre (`payload` de evento).

## 4. Regras de evolução do contrato (semver)

| Mudança | Tipo | Regra |
|---|---|---|
| Novo endpoint/schema/campo opcional/novo valor de enum de entrada | minor (aditiva) | OK sem comunicação |
| Remover campo/endpoint, estreitar tipo, novo `required` | **major (breaking)** | Nova versão de arquivo + seção no ADR + notas no PR |
| Exemplo alterado | patch | OK (mas re-gerar types) |

**Invariante:** `apps/web/src/types/api.d.ts` e os modelos pydantic do
`quoting/` são **sempre gerados/derivados** — nunca editados à mão. O CI
regenera e falha em qualquer diff (`codegen --check`).

## 5. Decisões registradas nesta etapa

1. **`DELETE /conversations/{id}` e `/handoffs` admin** protegidos por
   `adminToken` (bearer) — token simples via env; detalhes e ameaças na
   Etapa 10 (threat model).
2. **`TurnoResponse` carrega `cotacao` e `handoff` inline** — o front desenha
   QuoteCard/HandoffBanner sem segunda chamada (menos round-trips no mobile).
3. **CEP sempre mascarado na saída** (`01***-***`) mesmo em timeline interna —
   o íntegro só existe em Bronze e no request ao legado (LGPD · Etapa 2 §3.2).
4. **quote-api.yaml é do consumidor**: se o desafio alterar o legado, o
   contract test acusa; nós não alteramos o provedor.

## 6. ✅ Portão de validação da Etapa 5

| Critério | Como se satisfaz | Status |
|---|---|---|
| Lint do contrato passa | `spectral lint openapi/*.yaml` limpo (regras §3) | 🟡 comandos definidos; gate entra no CI da Etapa 16 |
| Codegen compila sem ajuste manual | types TS gerados do YAML; `--check` no CI; proibido editar gerados | 🟡 idem |
| Contract tests bloqueiam CI em quebra | drift test (oasdiff) + fixtures do consumidor como jobs **blocking** | 🟡 idem |

> **Nota de sequenciamento honesta:** o pipeline ainda não existe (Épico E /
> Etapa 16 do guia novo). Esta etapa entrega os contratos, o ruleset, os
> comandos e o desenho dos gates — a Etapa 16 os transforma em jobs
> obrigatórios, e só então o portão fecha **de fato**. O checklist master
> reflete isso (Etapa 5 ✅ quando o CI rodar os 3 gates).

---

*Validado em: 01/09/2026 pelo responsável do projeto (contratos aprovados; gates entram como jobs obrigatórios na Etapa 16)*
