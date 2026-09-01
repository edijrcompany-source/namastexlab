# Etapa 17 — Ambientes e Infrastructure as Code

> Fase 3 (fecha a fase) · **Dev, staging e produção idênticos por construção —
> mesma forma, escalas diferentes.** Nada de "na minha máquina funciona".
>
> ⚠️ **Mudança de decisão:** a Etapa 8 registrava "sem staging dedicado
> (custo)". O guia exige staging espelhando produção → **staging adotado**
> (custo adicional ~US$ 3-5/mês). O portão da Etapa 8 (deploy sem downtime)
> fica MAIS forte: migrações agora ensaiadas em staging de verdade.

---

## 1. Os três ambientes — mesma forma, escalas diferentes

| | dev | staging | produção (demo) |
|---|---|---|---|
| Onde roda | docker compose (máquina/CI) | Railway env `staging` + Vercel alias estável | Railway main + Vercel production |
| Imagem agent-api | **build local do mesmo Dockerfile** | **a mesma** (GHCR tag sha do main) | **a mesma** (GHCR tag sha) |
| quote-api | Dockerfile do desafio (envs de falha default) | idem prod | idem prod |
| Postgres | container compose | Postgres Railway (plan mínimo) | Postgres Railway (backup diário — NFR-07) |
| Dados | seed/empty | **seed sintético (Silver fixture)** | dados de demo (purga 30d — Etapa 8 §5) |
| Variáveis | mesmas chaves (spec §9), defaults | mesmas chaves, valores de staging | mesmas chaves, valores de prod |
| Migrações | `make migrate` | pre-deploy igual | pre-deploy igual |
| Release | — | deploy contínuo do main | **release.yml** (smoke + rollback) |

**Paridade por construção:** 1 Dockerfile · 1 compose · 1 módulo de IaC
parametrizado por ambiente · mesmas env-vars com valores diferentes · mesmos
gates. A única diferença real é **escala e dados**.

## 2. Infra como código — `infra/` (materializado)

```
infra/
├── modules/
│   └── railway-stack/     # módulo versionado: projeto + 3 serviços + vars
├── envs/
│   ├── staging/main.tf    # chama o módulo (escala mínima, seed sintético)
│   └── production/main.tf # chama o módulo (produção)
└── README.md              # fluxo, drift, secrets, adoção
```

- **Terraform/OpenTofu** com providers `vercel/vercel` (oficial) e
  `railwayzx/railway` — provisiona: projetos, serviços (agent-api do GHCR,
  quote-api, Postgres), variáveis **não-secretas** por ambiente, região
  `São Paulo`, domínios Vercel.
- **Módulo versionado**: `infra/modules/railway-stack` com CHANGELOG — reuso
  entre staging/produção (mesma forma, parâmetros diferentes).
- **State**: local commitado (`infra/envs/*/`) — **válido por construção**:
  o state não contém segredo algum (secrets ficam fora, §4). Gatilho para
  HCP Terraform (remote state free) se o time/ambientes crescerem.
- *Nota de adoção honesta:* o `.tf` é a **spec declarativa** — o primeiro
  `terraform init && plan` (com tokens) valida contra a versão vigente dos
  providers; nenhuma infra real foi provisionada ainda (mesmo regime de todas
  as etapas de design).

## 3. Mudança de infra = PR com plan revisado (Atlantis-like, sem Atlantis)

Fluxo no `.github/workflows/infra.yml`:

```
PR tocando infra/**  →  fmt -check · validate · PLAN de cada env
                        (comentado no PR pelo bot — revisável)
merge na main        →  APPLY com GitHub Environment "infra"
                        (APROVAÇÃO HUMANA obrigatória — mesma regra da Fase 3)
```

**Atlantis/env0 N/A justificado:** exigiriam servidor/serviço rodando — o CI
plan-in-PR + apply-com-approval entrega o mesmo controle para 1 projeto.
Gatilho de adoção: múltiplos repositórios de infra.

## 4. Secrets por ambiente (cofre separado, com rotação)

| Ambiente | Cofre | Rotação |
|---|---|---|
| dev | `.env` local (gitignored) | n/a (chaves fake/desativadas) |
| staging | variáveis Railway/Vercel do env staging + **GitHub Environment `staging`** | 90 dias (RB-02) — chaves PRÓPRIAS de staging, isoladas |
| produção | idem em `production` | 90 dias (RB-02) — nunca compartilhadas com staging |
| CI | GitHub Environments separados por env (RAILWAY_TOKEN_STG/PROD…) | junto com cada cofre |

Regra: **TF/state nunca carrega valores secretos** — só declara que existem;
`scripts/sync_secrets.sh` aplica valores a partir do cofre local (1Password/env
do operador) — o valor não passa pelo repo.

## 5. Detecção de drift

- Job agendado (noite, no `infra.yml`): `terraform plan -detailed-exitcode`
  por ambiente — **exit 2 = drift** → abre issue automática
  `[drift] <env>: configuração divergiu do declarado` e notifica.
- Correção obrigatória via PR (reverter a mudança manual OU codificá-la) —
  "consertar no console" sem PR reabre o drift na noite seguinte.

## 6. Custos atualizados (decisão de staging incluída)

Railway produção ~US$5 + Railway staging ~US$3-5 + Vercel Hobby $0 + Pages $0
→ **~US$ 8-10/mês** (dentro do teto NFR/ADR-0008).

## 7. ✅ Portão de validação da Etapa 17

| Critério | Status |
|---|---|
| Todo plan de infra revisado em PR | ✅ workflow plan-in-PR + comentário do bot; apply exige approval humana |
| Staging espelha produção | ✅ mesmo módulo TF, mesma imagem GHCR, mesmas vars/chaves — só escala e dados diferem (adoção material no T-15) |
| Drift detectado e corrigido | 🟡 job noturno + issue automática definidos; primeira detecção real no T-15 (pré-entrega) |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Fase 3 fechada; Etapa 18 liberada)*
