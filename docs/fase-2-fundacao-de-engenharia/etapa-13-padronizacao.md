# Etapa 13 — Padronização Automatizada de Código

> Fase 2 · Com IA gerando volume, linter é **guardrail de arquitetura**, não
> estética. Formatação nunca ocupa revisão humana. Política de **catraca**:
> zero aviso novo tolerado.
>
> ⚠️ **Mudança de convenção:** commits passam de conventional puro para
> **gitmoji + type em inglês + micro-commits atômicos** (padrão do guia) —
> `AGENTS.md` atualizado nesta etapa.

---

## 1. Stack de padronização (configs materializadas nesta etapa)

| Camada | Ferramenta | Config | Guarda o quê |
|---|---|---|---|
| Python lint+format | **ruff** | `services/agent-api/pyproject.toml` [tool.ruff] | estilo + bugs (`B`), imports (`I`), `UP`, `SIM`… tudo como **erro** (catraca) |
| Regras de arquitetura (py) | **import-linter** | mesmo pyproject [tool.importlinter] | **contratos do C4 nível 3** (ADR-0002): domínio puro, bordas não invadidas |
| JS/TS lint | **ESLint** (flat) + **Prettier** | `apps/web/eslint.config.js` + `.prettierrc.json` | inclui **`react/jsx-no-literals`** — guardrail do i18n (ADR-0009) |
| Gate local | **pre-commit** | `.pre-commit-config.yaml` | ruff · eslint/prettier · **gitleaks** · higiene (EOF, whitespace) · **commitlint** (commit-msg) |
| Padrão de commit | **commitlint** (parser gitmoji) | `commitlint.config.js` | formato `<gitmoji> <type>(escopo): intenção em inglês` |
| Editor | `.editorconfig` | raiz | consistência básica multi-editor |

**Por que ESLint+Prettier e não Biome:** a regra `react/jsx-no-literals` é
**guardrail de arquitetura i18n** (Etapa 7 §5) e não existe no Biome —
alternativa registrada; Biome reavaliado se a regra ganhar equivalente.

## 2. Padrão de commit (rejeitado automaticamente se fora)

Formato: **`<gitmoji> <type>(escopo)?: <subject imperativo em inglês>`**

```
✨ feat(quoting): add circuit breaker with lease
🐛 fix(conversation): absorb handoff messages idempotently
✅ test(masking): cover plate regex edge cases
📝 docs(adr): record ADR-0010 no-broker decision
♻️ refactor(events): extract event store repository
```

| Gitmoji→type | | Gitmoji→type |
|---|---|---|
| ✨ feat | 🐛 fix | ✅ test |
| 📝 docs | ♻️ refactor | ⚡️ perf |
| 🔒️ security | 👷 ci/chore | 🔥 chore(discard) |

Regras do commitlint (todas **bloqueantes**): formato acima · subject ≤ 72
chars · imperativo (sem "added/adding") · escopo do conjunto fechado
(agent-api|web|contracts|messages|docs|ci|data…) · sem subject vazio.

**Micro-commit atômico (política, definida precisa):** 1 commit = 1 intenção —
teste+implementação da MESMA mudança vão juntos; refactor nunca misturado com
feature; doc junto da mudança que ela documenta. Atomicidade não é
automatizável — enforce por review com checklist do PR.

**Inglês no subject:** enforce por review (checklist do PR) — idioma não é
validável por regex sem falso-positivo; formato e comprimento são do CI.

## 3. Catraca (zero aviso novo)

- Repo novo ⇒ **sem baseline e sem dívida herdeira**: toda regra nasce como ERRO.
- ESLint: `--max-warnings 0` (qualquer warning = build vermelho).
- Ruff: qualquer violação falha (`ruff check`); format check no CI (`ruff format --check`).
- `pre-commit run --all-files` também roda no CI (Etapa 16) — o gate local e o
  remoto são o mesmo.
- Regra de processo: PR que "desliga regra para passar" precisa de ADR.

## 4. import-linter — os contratos do C4 (ADR-0002) como código

```
1. conversation → ∉ {api, llm, quoting, handoff}   (core não conhece bordas — portas!)
2. privacy → ∉ qualquer módulo além de domain       (puro, sem I/O)
3. layers: api → todos · nenhum → api               (borda é folha)
```

Quebra = CI vermelho — refatorar "por conveniência" importando borda no core
é bloqueado por máquina, não por memória.

## 5. Alvos Makefile (implementados nesta etapa)

```bash
make fmt   # ruff format + ruff --fix + prettier --write
make lint  # ruff check + ruff format --check + eslint --max-warnings 0 + import-linter + pre-commit --all-files
```

*(requer `pnpm install` para as deps JS; no devcontainer já vem pronto)*

## 6. ✅ Portão de validação da Etapa 13

| Critério | Como | Status |
|---|---|---|
| Commit fora do padrão rejeitado automaticamente | commitlint no pre-commit (commit-msg) **e** no CI validando o range do PR (Etapa 16) | 🟡 configs materializadas; hooks ativam no `git init` do repo (T-01); job CI na Etapa 16 |
| Zero aviso novo (catraca) | sem baseline; tudo é erro; `--max-warnings 0`; mesma suíte local e CI | ✅ política + configs prontas (efeivo com o primeiro código) |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 14 liberada)*
