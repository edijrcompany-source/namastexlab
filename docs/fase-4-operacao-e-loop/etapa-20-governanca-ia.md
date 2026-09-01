# Etapa 20 — Governança da IA no Processo

> Fase 4 · **O processo é auditável: quem pediu o quê, o que a IA gerou e quem
> aprovou.** Export sem segredo, PR sem revisão — **nada passa.**
> Consolida: regra da Fase 3 (Etapa 16) · gitleaks nos ai-logs (Etapa 10) ·
> prompt-é-código (Etapa 19) · e adiciona SBOM de licenças.

---

## 1. A trilha de auditoria (fim a fim, tudo registrado no GitHub)

```
TICKET (template Etapa 3: contexto+DoD)          ← QUEM PEDIU O QUÊ (e a spec §)
   └─ PR (autor: humano OU agente de IA)
        ├─ gates automáticos (pr.yml: lint/contracts/security/test/evals/build)
        ├─ REVISÃO HUMANA registrada (CODEOWNERS + 1 approval — obrigatória)
        └─ merge (IA NUNCA faz merge sozinha — auto-merge DESLIGADO)
             └─ release.yml: imagem sha + SBOM + deploy + smoke
AI-LOGS/ (export higienizado da sessão que gerou o código)  ← O QUE A IA GEROU
```

**Política de revisão (formal, enforçada):**
- Humano aprova **100% dos PRs** (branch protection: 1 approval + CODEOWNERS + required checks — Etapa 16).
- **Auto-merge permanentemente desligado** nos settings do repo.
- Merge de humano é o único caminho para `main`. Auditoria: aba de reviews +
  audit log do GitHub = "quem aprovou o quê, quando".

## 2. `ai-logs/` — exports higienizados (a transparência é ENTREGÁVEL do desafio)

Estrutura: `ai-logs/<ferramenta>/<data>-<topico>.{jsonl,md}` (ex.:
`ai-logs/claude-code/2026-09-01-etapa8-mensageria.md`).

**Checklist de higienização ANTES de commit (barreira 1 — manual):**
- [ ] Nenhuma API key/token (nem em screenshots/paths de terminal)
- [ ] Dados pessoais seus (e-mails, nomes de terceiros) removidos/mascarados
- [ ] URLs internas/privadas removidas
- [ ] Export completo é permitido — feio e cru serve (o desafio pede o processo real)

**Barreira 2 — gitleaks roda SOBRE os ai-logs**: pre-commit + `pr.yml` (security
job varre repo inteiro **incluindo** `ai-logs/` e o histórico). Token escapado =
PR vermelho, token revogado (RB-02), export re-editado.

## 3. Governança de prompts (a promessa da Etapa 19, formalizada)

- Prompts vivem em `prompts/` com **semver próprio** independente do código:
  - `system_v1.md` (materializado nesta etapa — deriva da spec §4.1/§4.2)
  - `CHANGELOG.md` registra: versão · motivo · resultado da suíte (E1/E2/E3)
- **Regra de mudança** (3 barreiras):
  1. PR em `prompts/**` → job `evals-prompts` com LLM REAL (Etapa 19 — bloqueante);
  2. changelog obrigatório no mesmo PR (motivo + números da suíte);
  3. revisão humana (como qualquer código).
- **Rastreabilidade em produção**: cada chamada loga `prompt_version`
  (Etapa 19 §4) — incidente de comportamento correlaciona com a versão exata.
- O prompt é o **contrato do LLM**: regras invioláveis lá = as mesmas da spec
  (nunca uma lista paralela divergente — divergência = bug de doc).

## 4. SBOM — inventário de componentes e licenças (syft)

| Item | Decisão |
|---|---|
| Geração | **syft** no `release.yml`: SBOM (SPDX JSON) da imagem `agent-api` + do `apps/web` — artefato publicado junto ao release |
| CVE | já coberto pelo Trivy (Etapa 15) — syft soma o inventário de licenças |
| Política de licenças | **Allowlist**: MIT · Apache-2.0 · BSD-2/3 · ISC · Python-2.0 · PSF · MPL-2.0 (caso a caso). **Copyleft (GPL/AGPL) em dependência de RUNTIME = conflito = blocker** |
| Verificação | job `sbom` checa licenças contra a allowlist; novidade fora da lista → PR vermelho |
| Licença do repo | **MIT** (entrega pública do take-home) |
| Makefile | `make sbom` (local: syft dir: services/agent-api + apps/web) |

## 5. ✅ Portão de validação da Etapa 20

| Critério | Status |
|---|---|
| Exports sem segredos | ✅ dupla barreira (checklist manual + gitleaks em ai-logs/ e histórico) |
| 100% dos PRs com revisão humana registrada | ✅ branch protection + CODEOWNERS + auto-merge desligado (política §1) |
| Inventário de licenças sem conflito | 🟡 job sbom + allowlist no release; primeira execução com o primeiro lockfile real (T-01) |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 21 liberada)*
