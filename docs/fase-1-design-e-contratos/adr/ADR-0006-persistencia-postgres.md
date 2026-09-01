# ADR-0006 — Persistência Postgres gerenciado

**Status:** aceito (01/09/2026)

## Contexto
Persistir: eventos de conversa (append-only, jsonb), estado das conversas,
fila de handoffs. NFR-07: RPO ≤ 24h · NFR-08: 10 conversas simultâneas ·
NFR-12/LGPD: `DELETE /conversations/{id}` com cascata. Deploy: Railway
(multi-container) — ver ADR-0008.

## Decisão
**PostgreSQL 16 gerenciado do Railway** (mesmo projeto dos demais serviços,
rede interna). Eventos em tabela `events` (jsonb), consultas por
`conversation_id` + `seq`. Migrações versionadas (Alembic) rodando como job
efêmero no deploy.

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **SQLite (+volume)** | Zero operação, 1 dependência a menos | Backup/RPO manual; concorrência de escrita limitada (NFR-08); Railway já inclui Postgres — economizar aqui não poupa dinheiro | Descartado |
| **Sem banco (arquivos/logs)** | Simplicidade máxima | Sem consulta de timeline, sem fila de handoff, sem DELETE LGPD confiável | Descartado |
| **Postgres gerenciado** ✅ | RPO 24h grátis (backup diário), JSONB p/ eventos, DELETE cascata, rede interna com agent-api | Um serviço a mais no projeto | **Aceita** |
| **DynamoDB/Mongo (managed)** | Schema-flexível | JSONB do Postgres cobre a flexibilidade; sair do combo Railway aumenta custo/setup | Descartado |

## Consequências
**Positivas:** rastreabilidade (critério de avaliação do desafio) vira query
simples; fila de handoff = tabela com índice, sem broker (ADR da Etapa 7).
**Negativas:** SQLAlchemy+Alembic no stack de dev (custo de aprendizado zero
para o time Python). **Nota:** sem cache de cotação — preço pode mudar e a
verdade é sempre a API (regra da spec, não otimização prematura).
