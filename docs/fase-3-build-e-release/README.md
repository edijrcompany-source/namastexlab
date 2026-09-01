# Fase 3 — Build e Release (Etapas 15-17)

> 🟢 Etapas 15-16 validadas · **Etapa 17 concluída** (aguardando validação — fecha a fase).
> **Regra da fase:** PR gerado por IA só entra com gate automático + revisão
> humana — sempre os dois.

| Etapa | Documento | Status |
|---|---|---|
| 15 | [`etapa-15-containers.md`](./etapa-15-containers.md) + `Dockerfile` multi-stage não-root + `docker-compose.yml` (perfis + seed e2e) + hadolint/trivy | ✅ validada |
| 16 | [`etapa-16-cicd.md`](./etapa-16-cicd.md) + `.github/workflows/` (pr/nightly/release/docs) + CODEOWNERS — 10 gates, rollback automático, branch protection | ✅ validada |
| 17 | [`etapa-17-ambientes.md`](./etapa-17-ambientes.md) + `infra/` (módulo railway-stack + envs tofu) + `infra.yml` (plan-em-PR/apply-aprovado/drift) — **staging adotado** | 🟡 feita |

Input obrigatório: fundação da Fase 2 pronta. ✅
