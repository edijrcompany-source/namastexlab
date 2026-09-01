# Como produzir o `ai-logs/` (guia completo)

> **O que é:** pasta exigida pelo desafio com os **exports das conversas que
> você teve com IAs** durante o projeto. Não é anexo opcional — o README do
> desafio diz literalmente: *"as conversas que você teve com as IAs fazem
> parte da entrega"* e os `ai-logs/` **entram na avaliação junto com o código**.
> A Namastex avalia o *processo* (como você orquestrou IA), não só o resultado.

## O que registrar

1. O **pedido** (prompt) — em versão refinada (gramática + precisão técnica);
2. **Quando** (timestamp — o histórico git do registro incremental comprova);
3. O **resultado/decisão** que o prompt gerou (1 linha com link/commit).

## Como exportar por ferramenta

| Ferramenta | Como exportar | Onde colocar |
|---|---|---|
| **ZCode / Claude Code (CLI)** | As sessões ficam em `~/.claude/projects/<slug>/*.jsonl` (ou histórico do CLI). Alternativa prática (usada aqui): registrar cada prompt no formato abaixo com commit incremental — o git é o timestamp auditável | `ai-logs/prompts/pNN-*.md` |
| **Claude.ai (web)** | Menu da conversa → *Share* (link público) ou *Export* (.md/.txt) | `ai-logs/claude-web/…` + link no índice |
| **ChatGPT** | Menu da conversa → *Share* (link) ou *Settings → Export data* | `ai-logs/chatgpt/…` |
| **Codex CLI** | `~/.codex/sessions/` | copiar o `.jsonl` |
| **Cursor / Windsurf** | Painel de chat → exportar/copiar histórico para `.md` | `ai-logs/cursor/…` |
| **Copilot Chat / outros** | Copiar e colar num `.md` — "pode mandar o histórico como ele saiu" (README do desafio) | `ai-logs/outros/…` |

## Regras de higiene (do desafio e do nosso processo)

- 🚫 **Zero segredos**: keys/tokens/dados pessoais SEUS removidos (barreira 1:
  revisão manual; barreira 2: gitleaks no CI varre `ai-logs/` — Etapa 10 T11);
- ✅ Pode ser cru/feio ("não precisa ser bonito") — mas organizado por sessão;
- 🔁 **Registro incremental**: cada prompt novo → novo arquivo + commit — o
  histórico do git comprova o processo em tempo real (é o que este repo faz).

## Formato deste repo

```
ai-logs/
├── 2026-09-01-implementacao-zcode.md   # resumo estruturado da colaboração
├── prompts/
│   ├── README.md                        # índice dos 40 prompts da sessão
│   └── pNN-<slug>.md                    # 1 prompt por arquivo (refinado + timestamp)
└── COMO-PRODUZIR.md                     # este guia
```

Cada `pNN-*.md`:

```markdown
---
n: 12
quando: 2026-09-01 14:32 (commit  abc1234)
categoria: etapa | decisao | bug | goal
---
## Prompt (refinado)

<versão corrigida e tecnicamente precisa do pedido>

## Resultado
<1-3 linhas + commit/ARquivo de referência>
```
