# Fase 4 — Operação e Loop (Etapas 18-21)

> 🟡 Etapa 18 concluída (aguardando validação) · Etapas 19-21 não iniciadas.
> O sistema vivo: observar, avaliar a IA, governar o uso e realimentar o loop.

| Etapa | Documento | Status |
|---|---|---|
| 18 | [`etapa-18-observabilidade.md`](./etapa-18-observabilidade.md) + `observability/alerts.yml` — OTel SDK único, correlation ID ponta a ponta, 4 SLOs com error budget, 7 alertas↔runbooks, ensaio de incidente | ✅ validada |
| 19 | [`etapa-19-evals.md`](./etapa-19-evals.md) + `evals/golden/` (20 ataques jsonl, seeds extração/handoff) — 5 evals + TRA, prompt-é-código (job bloqueante), FinOps de token com 2 alertas | ✅ validada |
| 20 | [`etapa-20-governanca-ia.md`](./etapa-20-governanca-ia.md) + `prompts/system_v1.md`+CHANGELOG + PR template + job SBOM — trilha auditável, dupla barreira ai-logs, licenças allowlist | ✅ validada |
| 21 | [`etapa-21-retro.md`](./etapa-21-retro.md) + [`postmortems/TEMPLATE.md`](../postmortems/TEMPLATE.md) + `RETRO.md` (raiz) — blameless 48h, DORA por release, loops L1-L3 | 🟡 feita — fecha o processo |

Input obrigatório: produto rodando ponta a ponta (Fases 0-3).
