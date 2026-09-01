# Etapa 15 — Containers

> Fase 3 · **Empacotar e entregar com segurança.** Regra da fase (do guia):
> **PR gerado por IA só entra com gate automático E revisão humana — sempre
> os dois, sem exceção** (implementado na Etapa 16: branch protection).
> Reprodutibilidade é o que permite delegar execução a agentes com confiança.

---

## 1. Artefatos materializados nesta etapa

| Artefato | Conteúdo |
|---|---|
| `services/agent-api/Dockerfile` | **multi-stage** (builder uv → runtime slim) · **não-root** (`app:10001`) · healthcheck sem curl (httpx) · imagem **única multi-destino** (dev compose = Railway = VPS — mesma imagem, config por env) |
| `services/agent-api/.dockerignore` | contexto mínimo (cache + reprodutibilidade) |
| `docker-compose.yml` | **um comando sobe tudo** · perfis: default (dev) · `observability` (+jaeger OTLP) · `migrate` (job efêmero alembic) · `QUOTE_SEED=42` via env = legado determinístico p/ e2e |
| `.hadolint.yaml` | lint do Dockerfile, tudo erro (catraca), 2 ignores justificados |
| Makefile | `dev` · `dev-deps` · `dev-e2e` · `migrate` · `lint-docker` · `scan` |

## 2. Decisões de container

1. **Imagem única, multi-destino** — nenhum `Dockerfile.prod` separado: dev,
   CI e Railway usam A MESMA imagem (portão do guia: "um artefato, N destinos").
   O que muda entre ambientes: **env vars** (spec §9) — nunca o build.
2. **Não-root por construção** — uid/gid dedicados `10001`, `USER app:app`
   antes do `EXPOSE`; shell `nologin`. Verificável: `docker run … id -u` → `10001`.
3. **Artifacts de design entram na imagem**: `messages/` (catálogo ADR-0009) e
   `prompts/` são **lidos em runtime** — o container é autocontido.
4. **quote-api intocado** — compose builda do Dockerfile do desafio (regra 3);
   ajustes de instabilidade só via env (`QUOTE_FAILURE_RATE` etc.).
5. **Migrations como job efêmero** da mesma imagem (compose `migrate` /
   Railway pre-deploy — etapa-8 §4).
6. **E2E determinístico** (`make dev-e2e`): `QUOTE_SEED=42` congela a sequência
   de falhas do legado — C4/C5 viram testes estáveis (etapa-14 §4).

## 3. Gates de imagem (porta do CI — job na Etapa 16)

| Gate | Ferramenta | Critério |
|---|---|---|
| Boas práticas do Dockerfile | **hadolint** | zero erro (`make lint-docker`) |
| CVE da imagem | **Trivy** | **`--severity CRITICAL,HIGH --exit-code 1`** — CVE crítica quebra o build (portão) |
| Reprodutibilidade | compose + lockfiles (uv.lock/pnpm-lock) | `docker compose up` em máquina limpa |
| Não-root | healthcheck + `id -u` no smoke do container | 10001 |

## 4. Sequenciamento honesto (chicken-and-egg com T-01)

- `make dev-deps` **funciona hoje**: postgres + quote-api sobem (dependências
  não dependem do nosso código).
- `make dev` precisa do `app/` (scaffold T-01) — o Dockerfile falha com erro
  claro apontando a task até lá. A **definição** do container está completa e
  verificável nesta etapa; a **execução** completa ativa no T-01.

## 5. ✅ Portão de validação da Etapa 15

| Critério | Status |
|---|---|
| Imagem sem CVE crítica | 🟡 Trivy gate definido (`make scan`, blocker no CI); roda a partir da primeira imagem (T-01) |
| Sobe em máquina limpa com um comando | 🟡 compose completo + lockfiles; `dev-deps` já funcional; completo no T-01 |
| Roda como não-root | ✅ `USER app:10001` no Dockerfile (verificável por `id -u`) |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 16 liberada)*

> ✍️ **Nota da Etapa 17:** este portão (deploy sem downtime em staging) ficou
> MAIS forte — staging real adotado na Etapa 17 (Railway env + Vercel alias),
> substituindo o "ensaio em cópia do banco" originalmente proposto aqui.
