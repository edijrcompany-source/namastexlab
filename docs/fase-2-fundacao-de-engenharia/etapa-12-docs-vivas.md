# Etapa 12 — Documentação Viva (docs dinâmicas)

> Fase 2 · Regra de ouro: **se pode ser gerado, é proibido escrever à mão;
> se não está publicado, não existe.** O fluxo invertido — as fontes da
> verdade (contrato, componentes, infra) GERAM a documentação — e a prosa
> (tutoriais, how-tos, ADRs, runbooks) segue **Diátaxis**, versionada no repo.

---

## 1. O que é gerado vs. o que é escrito (mapa de geração)

| Documentação | Fonte da verdade | Gerador | Público |
|---|---|---|---|
| **Referência da API** (agent-api) | `openapi/agent-api.yaml` (Etapa 5) | **Redoc** (`redoc-cli bundle` no build do portal) — NUNCA escrita à mão | Avaliador/dev |
| **Referência da API** (consumo do legado) | `openapi/quote-api.yaml` | idem | Engenharia |
| **Swagger interativa** | FastAPI `/openapi.json` (drift-testado vs YAML — Etapa 5) | FastAPI nativo (`/docs`) | Dev local |
| **Catálogo de componentes** | `apps/web/src/components/*` | **Storybook 8** (1 página por componente: ChatWindow, MessageBubble, QuoteCard, HandoffBanner, TimelineSidebar, ErrorBanner — com estados: idle/pensando/cotando/handoff/erro) | Front |
| **Eventos públicos** | `schemas/eventos/*.v1.json` | renderização dos JSON Schemas no portal | Integração |
| **Catálogo de mensagens** | `messages/pt-BR.json` | tabela renderizada do JSON (script `scripts/render_catalog.py`) | Negócio/i18n |
| **Comandos** | `Makefile` | `make help` (fonte ÚNICA — alvo listado = alvo documentado) | Todos |
| **Infra** | sem Terraform (ADR-0008: Railway/Vercel config-by-platform) | **N/A justificado** — infra docs = `docker-compose.yml` + tabela de envs (spec §9), referenciadas no portal | Ops |
| **Diagramas** | Mermaid as-code (`docs/diagramas-as-code.md`) | Mermaid (renderiza no GitHub + portal) | Todos |

**Anti-padrão banido:** página de API escrita à mão descrevendo endpoints que o
YAML já descreve. O drift test (Etapa 5) protege o contrato; o portal renderiza
o contrato — nunca há segunda cópia.

## 2. Portal — VitePress + GitHub Pages (publicado a cada merge)

- **Ferramenta:** VitePress (ecossistema node/pnpm, Markdown-first, Mermaid)
  rodando sobre `docs/` — o repo inteiro já é docs-as-code; o portal só adiciona
  navegação e render.
- **Publicação:** GitHub Actions → **GitHub Pages** a cada merge na `main`
  (job `docs` na Etapa 16): `pnpm dlx vitepress build docs` + `redoc-cli bundle`
  → deploy. URL pública: `https://<org>.github.io/namastex-fde/` —
  *o avaliador navega a documentação inteira sem clonar nada.*
- **"Se não está publicado, não existe":** PR que altera comportamento sem
  atualizar a doc correspondente é incompleto (checklist do template de ticket).

## 3. Estrutura Diátaxis da prosa (versionada no repo, navegável no portal)

| Quadrante | Conteúdo | Onde |
|---|---|---|
| 📚 **Tutorial** (aprender) | Primeiros passos: devcontainer → make dev → mock → 1º PR | `docs/tutorial.md` |
| 🔧 **How-to** (resolver tarefa) | Adicionar endpoint/evento/erro/string/migration · rodar evals | `docs/how-to.md` |
| 📖 **Referência** (consultar) | API (Redoc) · eventos · catálogo · glossário · comandos · envs | `docs/referencia.md` + geradas |
| 💡 **Explicação** (entender) | Processo 21 etapas · ADRs · spec · threat model · event storming | `docs/fase-*/` (já existentes — o portal navega) |
| 🚑 **Runbooks** | Restore, rotação de segredo, deploy, purga LGPD, incidentes | `docs/runbooks.md` |

Materializado nesta etapa: `docs/.vitepress/config.ts` (nav/sidebar Diátaxis),
`tutorial.md`, `how-to.md`, `referencia.md`, `runbooks.md` (5 runbooks),
`diagramas-as-code.md` (Mermaid: máquina de estados + containers).

## 4. Diagramas as-code (Mermaid — renderiza no GitHub e no portal)

Criados nesta etapa (`docs/diagramas-as-code.md`):
1. **Máquina de estados da conversa** (`stateDiagram-v2`) — vista da spec §1.3
   (a TABELA da spec continua sendo a fonte executável dos testes; o diagrama
   é a vista humana — divergência entre eles é bug de doc, apontado no review).
2. **Containers** (flowchart com subgraphs Vercel/Railway) — vista do C4 nível 2.

Evolução registrada (não antecipada): gerar o stateDiagram A PARTIR da tabela
da spec por script, eliminando a dupla manutenção.

## 5. Storybook (nasce com o front — T-11)

Configuração especificada: Storybook 8 + Vite, stories co-localizadas
(`Component.stories.tsx`), páginas para os 6 componentes com estados reais do
chat (incluindo pseudo-locale da Etapa 7 como story de teste de layout).
Publicação: Chromatic **não** (custo) — build estático no portal
(`/storybook/`) pelo mesmo job de docs. Alvo no Makefile: `make storybook`.

## 6. ✅ Portão de validação da Etapa 12

| Critério | Como | Status |
|---|---|---|
| Portal publica automaticamente a cada merge | Job `docs` (Etapa 16): vitepress build + redoc → GH Pages | 🟡 config materializada; job no pipeline (Etapa 16) |
| Referência de API renderizada do contrato | Redoc do `openapi/*.yaml`; Swagger via FastAPI drift-testado — nunca à mão | 🟡 comando `make docs-api`; entra no build do portal |
| Componentes com página no Storybook | 6 componentes × estados especificados | 🟡 nasce com T-11 (front) |
| ADRs e runbooks navegáveis no portal | sidebar "Explicação" (ADRs) + `docs/runbooks.md` | ✅ materializado nesta etapa |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 13 liberada)*
