# 🚑 Runbooks — procedimentos de operação

> Diátaxis/How-to de operação: o que fazer quando algo dá errado. Toda
> execução registra data/evidência (Etapa 8 §6). Owner: quem está de plantão
> (take-home: o autor).

## RB-01 — Restaurar backup do Postgres

**Quando:** corrupção/perda de dados. **RPO:** ≤24h (backup diário Railway).

1. `railway connect` no banco alvo → `pg_dump -Fc` (dump de segurança ANTES de mexer).
2. Criar Postgres efêmero no mesmo projeto → `pg_restore` do backup do dia.
3. `alembic current` — a revision deve bater com a de produção.
4. Smoke: `GET /conversations/{id}` de uma conversa conhecida + `COUNT(*)` em `events`.
5. Se ok: promover o efêmero (ou restore no principal) → dropar temporários.
6. **Registrar evidência** (data, hash do dump) na Etapa 18.
> Testado 1× antes da entrega (portão da Etapa 8).

## RB-02 — Rotacionar segredo

**Quando:** rotina 90 dias · suspeita de vazamento (gitleaks/fora).

1. Gerar novo valor (`LLM_API_KEY` no portal do provider / `ADMIN_TOKEN` via
   `openssl rand -hex 32`).
2. Atualizar a var no serviço (Railway) → **redeploy** (automático).
3. Invalidar o antigo no provider (para LLM: revoke da key antiga).
4. Confirmar: `GET /health` ok + um turno de conversa com cotação real.
5. Vazamento em commit? Além disso: history rewrite é irrelevante se a key foi
   revogada (rotacionar SEMPRE; gitleaks notifica para o histórico).

## RB-03 — Deploy da demo (Vercel + Railway)

1. Merge na `main` → CI (Etapa 16) roda gates → build & push das imagens.
2. Railway: pre-deploy roda `alembic upgrade head` → novo container assume.
3. Vercel: deploy automático do `apps/web` (preview em PRs).
4. Pós-deploy: `GET /health` (agent+legado ok) · conversa-padrão C1 no chat ·
   export do log (a prova de fogo).

## RB-04 — Purga LGPD manual

**Quando:** pedido de eliminação de dados · manutenção da retenção (30 dias).

1. `POST /admin/purge` com `ADMIN_TOKEN` (regras: inatividade 24h → sem_resposta;
   encerradas >30d → DELETE cascata; TTL idempotência — Etapa 8 §5).
2. Confirmação: contagem antes/depois (`conversations`, `events`, `handoffs`).
3. Registro do motivo e data (trilha LGPD).

## RB-05 — Incidentes de dependência

| Sintoma | Diagnóstico | Ação |
|---|---|---|
| Conversas travadas em "cotando…", `circuit_state_changed` frequente | Legado fora (probabilístico OU real) | O sistema se protege (breaker + handoff na 2ª abertura). Se >30min: verificar o quote-api (`GET /health`), reiniciar serviço no Railway, comunicar avaliador se em demo |
| Respostas canônicas sem graça + `llm_unavailable` nos eventos | Provider LLM fora / key inválida | Verificar key (RB-02), status do provider; o Agente segue funcional (fallback por estado — Etapa 6 §5) |
| 503 `servico-indisponivel` nos turnos | Postgres fora | Railway dashboard → reiniciar Postgres; turnos falham atômicos (sem meia-gravação); se persistir, RB-01 |
| Fila de handoffs crescendo sem atendimento | Operacional (demo) | Atender via `/handoffs` e marcar `em_atendimento`/`concluido` |
| `price_guard_violation` recorrente nos logs | Prompt degradado ou modelo trocado | Congelar apresentação via fallback, revisar `prompts/system_v1.md` (Etapa 20), rodar `make evals` |

**Comunicação de incidente (take-home):** se em demo pública, nota no README +
contexto no PR de correção. Postmortem leve na Etapa 21 se houver incidente real.
