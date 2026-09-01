# infra/ — Infrastructure as Code (Etapa 17)

Dev/staging/produção **idênticos por construção** — mesma forma, escalas
diferentes. Ver `docs/fase-3-build-e-release/etapa-17-ambientes.md`.

```
modules/railway-stack/   módulo versionado (projeto + agent-api + quote-api + postgres)
envs/staging/            espelho de produção: escala mínima + seed sintético
envs/production/         demo pública
```

## Regras

1. **Mudança de infra = PR com plan revisado** (`.github/workflows/infra.yml`
   comenta o plan no PR; apply só com aprovação humana do Environment `infra`).
2. **Segredos nunca passam daqui** — state sem valores sensíveis por
   construção; cofre por ambiente (Railway/Vercel/GitHub Environments),
   rotação 90d (RB-02), aplicação via `scripts/sync_secrets.sh`.
3. **Drift** — job diário `plan -detailed-exitcode`; exit 2 abre issue.
   Correção via PR, nunca "no console".
4. State: local commitado (sem secrets por design); gatilho p/ remote state
   documentado na etapa-17 §2.

## Adoção (T-15)

```bash
cd infra/envs/staging && tofu init && tofu plan    # valida providers/spec
# RAILWAY_TOKEN_* e VERCEL_TOKEN nos GitHub Environments correspondentes
```
