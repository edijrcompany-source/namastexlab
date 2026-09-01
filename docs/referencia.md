# 📖 Referência

> Diátaxis/Referência: consulta. **Regra da Etapa 12: aqui só entra link —
> conteúdo gerado é embutido pelo build do portal, nunca escrito à mão.**

## API agent-api (Redoc)

Renderizada do `openapi/agent-api.yaml` no build do portal
(`make docs-api` → `redoc-cli bundle`). Local, sempre atual:
**Swagger interativa** em `http://localhost:8001/docs` (FastAPI, drift-testada
contra o YAML pelo CI).

- Contrato inbound: [`/openapi/agent-api.yaml`](https://github.com/) *(link do repo)*
- Contrato do legado (as-consumed): `openapi/quote-api.yaml`

## Eventos públicos

Schemas v1 em `schemas/eventos/*.v1.json` (envelope `event_version`, PII-safe).
Tabela dos 6 eventos: [Etapa 9 §1](./fase-1-design-e-contratos/etapa-9-mensageria.md).

## Catálogo de mensagens

Tabela renderizada de `messages/pt-BR.json` (script `scripts/render_catalog.py`
no build do portal). Fonte: [`messages/pt-BR.json`](../messages/pt-BR.json).

## Glossário (linguagem ubíqua)

→ [etapa-1-linguagem-ubiqua.md](./fase-0-negocio-e-requisitos/etapa-1-linguagem-ubiqua.md)

## Comandos

`make help` é a fonte única (alvo listado = alvo documentado). Snapshot:

| Alvo | Uso |
|---|---|
| `make dev` | compose de dev (agent-api, quote-api, postgres) |
| `make test` / `make evals` | testes + coverage / suite de evals |
| `make contracts-lint` / `make codegen check` / `make mock` | ferramentas de contrato |
| `make bronze` / `make silver` / `make pseudo-locale` | pipeline de dados / i18n |
| `make docs-dev` / `make docs-build` | portal (esta documentação) |
| `make storybook` | catálogo de componentes (com o front) |

## Variáveis de ambiente

Tabela canônica: [spec §9](./fase-0-negocio-e-requisitos/etapa-3-spec.md) +
parâmetros de resiliência [Etapa 6 §4.1](./fase-1-design-e-contratos/etapa-6-erros-resiliencia.md).
Segredos vivem SÓ no Railway (Etapa 10 §3).

## Erros (códigos estáveis)

Catálogo completo: [Etapa 6 §3](./fase-1-design-e-contratos/etapa-6-erros-resiliencia.md)
— chave do catálogo `api.erro.*` = slug do `type` do problem+json.
