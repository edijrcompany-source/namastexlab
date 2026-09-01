# Etapa 11 — Estrutura do Repo e Context Engineering

> Fase 2 · [ADR-0011](../fase-1-design-e-contratos/adr/ADR-0011-monorepo-contexto-ia.md):
> monorepo de propósito, Makefile como linguagem comum, contexto de IA como
> artefato de engenharia. **Esta etapa materializou o esqueleto** — sem código
> de aplicação (nasce na Etapa 14 com TDD).

---

## 1. Estrutura final (materializada)

```
namastex-fde/
├── AGENTS.md              ← contexto raiz p/ agentes e humanos (v2, expandido)
├── README.md              ← README da entrega (skeleton — cresce até o envio)
├── Makefile               ← linguagem comum: humano, agente e CI usam os mesmos alvos
├── package.json           ← workspace pnpm + scripts de contrato (lint/codegen/mock)
├── pnpm-workspace.yaml
├── .gitignore
├── .devcontainer/         ← ambiente reproduzível (humano e agente herdam igual)
│
├── openapi/               ← contratos API-first (FONTE ÚNICA — movidos da docs/)
│   ├── agent-api.yaml     ← inbound (nossa API)
│   └── quote-api.yaml     ← outbound (legado as-consumed)
├── messages/pt-BR.json    ← catálogo i18n compartilhado API↔front (movido da docs/)
├── schemas/eventos/       ← 6 JSON Schemas públicos v1 (nascem com a impl.)
│
├── apps/web/              ← Next.js → Vercel (chat + fila de handoffs)
├── services/agent-api/    ← Python/FastAPI → Railway (monolito modular)
├── quote-service/         ← cópia do desafio — SOMENTE LEITURA
│
├── prompts/               ← system_v1.md etc. (governança: Etapa 20)
├── scripts/               ← fetch_bronze, build_silver, pseudo_locale
├── evals/                 ← suite de evals (Etapa 19)
├── dataset/               ← Bronze/Silver — GITIGNORED, gerado por script
├── ai-logs/               ← entregável obrigatório (sanitizado — gitleaks varre)
└── docs/                  ← docs-as-code: fases 0-4, specs, ADRs
```

**Migração executada nesta etapa:** `openapi/` e `messages/` saíram de
`docs/fase-1-design-e-contratos/` e viram arquivos reais na raiz (como
prometido nas Etapas 5/7 — docs/ volta a ser só documentação).

**Decisões de layout:**
- `dataset/` **gitignored**: Bronze é regenerável (`make bronze`, seed 42 do
  gerador do desafio; path do repo-challenge via env `NAMASTEX_CHALLENGE_DIR`).
  Nada de binário commitado.
- `quote-service/` entra como **cópia congelada** do desafio (Railway builda
  dele); a origem da verdade continua o repo do desafio — proibido alterar
  (regra 3 do AGENTS.md).
- Contratos/catálogo na **raiz** (não dentro de services/): são consumidores
  múltiplos (front, back, CI, Prism) — dono neutro.

## 2. Makefile — a linguagem comum

Alvos (humano, agente e CI chamam **os mesmos comandos** — Etapa 16):

| Alvo | O que faz | Status |
|---|---|---|
| `make contracts-lint` | spectral lint `openapi/*.yaml` | ✅ funcional desde já |
| `make codegen` (+`check`) | openapi-typescript → `apps/web/src/types/api.d.ts` (`check` falha se diff) | ✅ codegen; types materializam com o front |
| `make mock` | Prism mock do agent-api (`:4010`) p/ front andar sem back | ✅ |
| `make dev` | compose: agent-api + quote-api + postgres (+jaeger) | 🟡 T-01 |
| `make bronze` / `make silver` | regenera Bronze / Silver | 🟡 T-08 |
| `make test` / `make evals` | pytest c/ coverage gate / suite de evals | 🟡 Etapas 14/19 |
| `make fmt` / `make lint` | ruff + eslint/prettier + import-linter | 🟡 Etapa 13 |
| `make pseudo-locale` | gera + testa pseudo-locale | 🟡 Etapa 7 §6 |

Alvos ainda não implementados **falham com mensagem explícita** apontando a
task responsável — nunca silenciosamente.

## 3. Hierarquia de contexto (como se programa a IA no padrão do projeto)

```
ORDEM DE LEITURA (agente novo):
1. AGENTS.md (raiz)          — bússola: regras invioláveis, estrutura, comandos, armadilhas
2. docs/README.md            — mapa do processo + status das 21 etapas
3. A spec da feature em pauta — docs/fase-0-negocio-e-requisitos/etapa-3-spec.md §
4. README da pasta onde vai tocar (apps/web, services/agent-api, …)
5. ADR se o tema for estrutural — docs/fase-1-design-e-contratos/adr/

REGRAS DE CONTEXTO:
- Específico mora PERTO: convenção de uma pasta vive no README da pasta
- Global mora na RAIZ: regra inviolável, glossário, comandos → AGENTS.md
- Contexto não se repete: link, não cópia (1 fonte por fato)
- Novo evento/endpoint/erro: PR na spec/contrato ANTES do código
```

## 4. Dev Container (`.devcontainer/devcontainer.json`)

Python 3.12 + Node 20 + **Docker-in-Docker** (para o `docker compose` de dev)
+ uv + pnpm no `postCreateCommand`. Humano e agente herdam o MESMO ambiente —
reproduzibilidade é parte do onboarding < 1h.

## 5. Onboarding humano até o 1º PR (< 1h) — caminho documentado

| Passo | Ação | Tempo |
|---|---|---|
| 1 | Clonar + abrir no VS Code (devcontainer sobe sozinho) | 10 min |
| 2 | Ler `AGENTS.md` inteiro + `docs/README.md` (mapa) | 10 min |
| 3 | `make mock` → abrir `apps/web` contra o mock (sentir o produto) | 5 min |
| 4 | `make dev` (compose) → healthcheck verde | 10 min |
| 5 | Pegar ticket do template (`etapa-3-template-ticket.md`) — começar por um `good first issue` (T-02 masking) | 5 min |
| 6 | TDD: teste vermelho → verde → `make lint && make test` → PR citando a seção da spec | 15 min |

## 6. Quiz de onboarding de agentes (o portão, operacionalizado)

Um agente novo (ou dev novo) **deve acertar** sem perguntar a ninguém — cada
resposta mora em exatamente um lugar:

| # | Pergunta | Resposta mora em |
|---|---|---|
| 1 | Posso apresentar um preço que não veio da API? | AGENTS.md regra inviolável 1 + spec §4.3 |
| 2 | A spec está ambígua — improviso? | AGENTS.md "Para agentes de IA" + processo |
| 3 | Como rodo tudo local? | AGENTS.md "Comandos" + Makefile |
| 4 | Onde edito um texto de tela? | `messages/pt-BR.json` (ADR-0009) |
| 5 | Adicionei um campo no endpoint — o que mais? | Etapa 5 §4 (semver) + codegen `check` + spec |
| 6 | Posso alterar o quote-service? | AGENTS.md regra 3 — NUNCA |
| 7 | 422 do legado: tento de novo? | Glossário: recusa de negócio ≠ falha transiente |
| 8 | Onde vejo o status do projeto? | `docs/README.md` checklist 21 etapas |
| 9 | Nova migration: qual processo? | Etapa 8 §4 (1 PR=1 revision, down obrigatório, EMC) |
| 10 | Minha conversa de IA vai pro repo? | `ai-logs/` sanitizado (T-17, gitleaks varre) |

**Como o portão se verifica:** rodar este quiz com um agente novo (sessão
limpa) antes de congelar a Fase 2 — falha = contexto incompleto = corrigir
AGENTS.md, não culpar o agente.

## 7. ✅ Portão de validação da Etapa 11

| Critério | Status |
|---|---|
| Agente novo responde perguntas sobre convenções | 🟡 quiz de 10 perguntas com fonte única cada; verificação executada com o primeiro agente de implementação (Épico A) |
| Onboarding humano < 1h até o 1º PR | ✅ caminho de 6 passos com tempos somando ~55 min (§5) |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 12 liberada)*
