# Deploy da Demo — runbook exato (T-14 + T-15)

> Tudo que depende de CONTAS SUAS. Tempo estimado: ~15 min na primeira vez.
> Os workflows já estão no repo; os triggers automáticos reativam ao final
> (comentários de reativação estão nos próprios arquivos `.github/workflows/`).

## 1. GitHub — CI + proteção (T-14) · ~5 min

1. **Branch protection** (recipe também no `.github/CODEOWNERS`):
   `Settings → Branches → Add branch ruleset → main`
   - ☑ Require a pull request before merging (1 approval, dismiss stale)
   - ☑ Require status checks: `lint`, `contracts`, `security`, `codeql`, `test`, `build-scan`
   - ☑ Require linear history · ☑ Block force pushes
2. **Secrets** (`Settings → Secrets and variables → Actions`):
   - `LLM_API_KEY` (opcional — sem ela a demo roda com FakeLLM offline)
   - Environments `demo` e `infra`: `RAILWAY_TOKEN` / `VERCEL_TOKEN` (passo 3)
   - Variables: `DEMO_AGENT_API_URL`, `DEMO_WEB_URL` (preencher após deploy)
3. **CodeQL**: `Settings → Code security → Code scanning → default setup` (gratis em repo público)

## 2. Vercel (front) · ~3 min

```bash
npm i -g vercel
cd apps/web && vercel link          # importar projeto namastex-fde-web
vercel env add NEXT_PUBLIC_AGENT_API_URL production   # URL do Railway (passo 3)
vercel --prod
```

## 3. Railway (agent-api + quote-api + Postgres) · ~7 min

```bash
npm i -g @railway/cli
railway login
railway init          # projeto namastex-fde (região São Paulo)
# 3 serviços:
railway add --service agent-api    # Dockerfile: services/agent-api (imagem GHCR via release.yml)
railway add --service quote-api    # repo root: quote-service (Dockerfile do desafio)
railway add --database postgres    # gera DATABASE_URL interna
# variáveis do agent-api (Settings → Variables):
#   QUOTE_API_URL=http://quote-api.railway.internal:8000
#   DATABASE_URL=<internal>  MASKING_STRICT=true  ADMIN_TOKEN=<openssl rand -hex 32>
#   LLM_API_KEY=<opcional>  AGENT_CORS_ORIGINS=https://<seu-app>.vercel.app
railway status       # anote a URL pública → coloque no Vercel env + GitHub vars
```

## 4. Reativar os pipelines (comentários nos arquivos)

```bash
# release.yml / docs.yml: restaurar `push: { branches: [main] }`
# nightly.yml: restaurar o cron   |   infra.yml: push+schedule (T-15 tofu)
git commit -am "👷 ci: activate pipelines (bootstrap complete)" && git push
```
O primeiro `release.yml` faz: testes → imagem GHCR → Railway (pre-deploy roda
`alembic upgrade head` quando o Postgres real entrar) → smoke → **rollback
automático** se falhar (`LAST_GOOD_TAG`).

## 5. Rehearsal de rollback + incidente (T-15 — 10 min, uma vez)

1. Simular quebra: PR com `raise` no `/health` → deploy → smoke falha →
   **rollback automático executa** (evidência na run do Actions).
2. Ensaio de incidente (RB-05): parar o quote-api no Railway 15 min →
   verificar resposta honesta sem preço + alerta `LegadoCircuitoAberto`.
3. Registrar evidências em `docs/fase-4-operacao-e-loop/etapa-18-observabilidade.md` §5.

---

## Decisão: Postgres real (T-06b) — **dívida documentada** (não entra na entrega)

**Por quê:** a demo avalia o Agente (conversa, resiliência, decisão) — o
`InMemoryStore` atende 100% dos fluxos local/compose; adiar o Postgres evita
migrações em janela de avaliação. A **porta `Store` está pronta** (import-linter
protege); plugar é criar `PostgresStore` + Alembic 0001 (o ERD inteiro já está
desenhado na etapa-8) — estimativa: 1 sessão.

**Rastro:** `docs/plano-implementacao.md` §marcos · `checklist-final` portão 8.
