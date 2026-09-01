# Etapa 8 — Modelo de Dados e Migrações

> Fase 1 · "A decisão mais cara de reverter depois da arquitetura." Stack
> decidida no ADR-0006: **Postgres 16 + Alembic**. Este doc é o schema canônico
> v1 — a migração `0001` nasce daqui, e o ERD é versionável (DBML).

---

## 1. Decisões de modelagem

| Decisão | Justificativa |
|---|---|
| **Event store + snapshot híbrido** | `events` (append-only, spec §5.2) é a verdade histórica; `conversations` guarda o **estado atual** (snapshot) para leitura rápida da máquina de estados e da timeline |
| **Sem tabela `quotes`** | Cotação é imutável e já vive no payload de `quote_succeeded`; a Timeline deriva `cotacoes[]` dos eventos. Sem cache (ADR-0006): a verdade do preço é sempre a API |
| **1 handoff por conversa** (UNIQUE) | Estado `HANDOFF` é absorvente (spec §1.3) — segunda solicitação apenas reafirma |
| **PII em Bronze interna** | `dados_qualificados.cep` e `events.payload` guardam íntegro (acesso restrito); **toda saída** da API mascara (spec §3). DELETE cascata = LGPD |
| **ULID como PK pública** | Ordenável, sem bias de sequência (spec §5.4); `BIGSERIAL` interno só em `events.id` |
| **Enums nativos do Postgres** | `estado_conversa`, `tipo_evento` (18 valores + `llm_unavailable`), `motivo_handoff`, `status_handoff` — quebra de valor inválido no banco, não na aplicação |

## 2. ERD (DBML — cole no [dbdiagram.io](https://dbdiagram.io) para visual)

```dbml
Enum estado_conversa {
  QUALIFICANDO
  CONFIRMANDO
  COTANDO
  COTACAO_APRESENTADA
  OBJECAO
  HANDOFF
  ENCERRADA_GANHO_EM_ANDAMENTO
  ENCERRADA_PERDIDO_INELIGIVEL
  ENCERRADA_PERDIDO
  ENCERRADA_SEM_RESPOSTA
}

Enum tipo_evento {
  conversation_started
  message_in
  message_out
  intent_detected
  lead_qualified
  pre_check_failed
  quote_requested
  quote_attempt_failed
  circuit_state_changed
  quote_succeeded
  quote_presented
  quote_refused
  objection_raised
  handoff_requested
  retry_scheduled
  price_guard_violation
  llm_unavailable
  conversation_ended
}

Enum motivo_handoff {
  aceite_fechamento
  inelegivel_contestado
  objecao_preco
  preferencia_humana
  falha_tecnica
  fora_escopo
}

Enum status_handoff {
  pendente
  em_atendimento
  concluido
}

Table conversations {
  id                   char(26)      [pk, note: 'ULID público']
  estado               estado_conversa
  desfecho             varchar       [null, note: 'desfecho terminal (linguagem ubíqua)']
  dados_qualificados   jsonb         [null, note: 'Bronze interna — CEP íntegro; saída sempre mascarada']
  retry_pending        boolean       [default: false, note: 'flag da retentativa 2min (spec §1.3)']
  circuito_reaberturas integer       [default: 0, note: 'handoff falha_tecnica na 2ª abertura']
  criada_em            timestamptz   [default: `now()`]
  atualizada_em        timestamptz
  encerrada_em         timestamptz   [null]

  indexes {
    estado    [name: 'idx_conversations_estado']
    encerrada_em [name: 'idx_conversations_purga']
  }
}

Table events {
  id              bigserial [pk]
  conversation_id char(26)
  seq             integer   [note: '1..N por conversa']
  type            tipo_evento
  payload         jsonb     [default: `'{}'`, note: 'PII: saída mascarada pela aplicação']
  correlation_id  uuid      [null, note: 'Etapa 6 — rastreio ponta a ponta']
  criado_em       timestamptz [default: `now()`]

  indexes {
    (conversation_id, seq) [unique, name: 'uq_events_conv_seq']
    (type, criado_em)      [name: 'idx_events_type_time']
  }
}

Table handoffs {
  id              char(26) [pk]
  conversation_id char(26) [unique, note: 'absorvente — 1 por conversa']
  motivo          motivo_handoff
  resumo          varchar(500)
  status          status_handoff [default: pendente]
  criado_em       timestamptz [default: `now()`]

  indexes {
    (status, criado_em) [name: 'idx_handoffs_fila']
  }
}

Table idempotency_keys {
  conversation_id char(26) [note: 'PK composta']
  chave           varchar(64)
  turno_resposta  jsonb    [note: 'resposta completa p/ replay (Etapa 6)']
  criado_em       timestamptz [default: `now()`]

  indexes {
    (conversation_id, chave) [pk]
    criado_em                [name: 'idx_idem_ttl']
  }
}

Ref: events.conversation_id > conversations.id        [delete: cascade]
Ref: handoffs.conversation_id > conversations.id      [delete: cascade]
Ref: idempotency_keys.conversation_id > conversations.id [delete: cascade]

// NOTA (Etapa 9 / migração 0002): + tabela dead_letters e colunas
// retry_attempts / retry_lease_expires_at em conversations — ver
// etapa-9-mensageria.md §4.4 (expansão aditiva, padrão EMC).
```

## 3. DDL essencial (v1 — conteúdo da migração `0001`)

Além do ERD acima, a `0001` cria os 4 enums, as 4 tabelas e os índices.
Regras de integridade que o DDL garante (e a aplicação **não** repete):

1. `UNIQUE (conversation_id, seq)` — sem buraco/duplicidade na timeline.
2. `ON DELETE CASCADE` nas 3 FKs — **um DELETE resolve a cascata LGPD** (US-12).
3. Enums nativos — valor inválido nunca entra.

## 4. Estratégia de migração — Alembic + expand-migrate-contract

### Regras do dia 1

| Regra | Detalhe |
|---|---|
| 1 PR = 1 revision | `alembic revision` autogerada + editada; nome descritivo (`0002_add_nps_rating`) |
| `down()` **obrigatório** | revisão sem down = PR rejeitado; forward-only exige ADR |
| Deploy: job pre-rollout | No Railway: **pre-deploy command** `alembic upgrade head` antes do novo container assumir tráfego |
| Teste de revisão no CI | container Postgres efêmero: `upgrade head` → `downgrade base` → `upgrade head` com **seed de dados reais** (§6) |
| Revisão de performance | migration que varre tabela grande exige `USING CONCURRENTLY` / batch — revisar no PR |

### Expand-Migrate-Contract (deploys sem downtime)

Qualquer mudança quebrante segue 3 deploys — código antigo e novo convivem:

```
DEPLOY 1 (EXPAND)    schema aditivo: coluna nova NULLABLE / tabela nova / enum+valor
                     código novo LÊ a novidade e ESCREVE nela (se souber); antigo segue no mesmo schema
DEPLOY 2 (MIGRATE)   backfill em batch (ex.: UPDATE ... WHERE ... LIMIT 10000 em loop)
                     sem lock longo; dados antigos copiados p/ formato novo
DEPLOY 3 (CONTRACT)  código antigo removido; então: NOT NULL / DROP coluna antiga / DROP tabela
```

**Exemplo canônico** (documentado p/ qualquer mudança futura): adicionar
`conversations.nps_rating` → ① coluna `smallint NULL` + código grava quando
houver; ② backfill `0` para históricos elegíveis; ③ constraint
`CHECK (nps_rating BETWEEN 0 AND 10)` + código legado removido.
Enum: **adicionar valor é expand puro** (Postgres aceita); **remover** valor
exige EMC em 3 passos com tabela de reassociação.

### Sem-downtime no nosso caso

Turno é síncrono com retry idempotente no client (Etapa 6 §4.2) → restart do
`agent-api` durante deploy não perde mensagem (replay pela
`Idempotency-Key`). Migrações são aditivas (EMC) → container antigo e novo
convivem nos segundos de rollout.

## 5. Retenção e purga (LGPD — closes US-12/US-16)

| Regra | Implementação |
|---|---|
| Inatividade > 24h → encerra `SEM_RESPOSTA` | `UPDATE conversations SET estado='ENCERRADA_SEM_RESPOSTA', encerrada_em=now() WHERE encerrada_em IS NULL AND atualizada_em < now()-interval '24h'` + evento `conversation_ended` |
| Conversas encerradas > 30 dias → **DELETE cascata** | `DELETE FROM conversations WHERE encerrada_em < now()-interval '30 days'` (cascade varre events/handoffs/idempotency) |
| `idempotency_keys` TTL 2 min | limpeza lazy na leitura + `DELETE ... WHERE criado_em < now()-interval '2 min'` no mesmo job |

Mecanismo: endpoint admin `POST /admin/purge` (`ADMIN_TOKEN`) executando as 3
regras em transação, chamado por **cron diário externo** (Etapa 17) — auditável,
testável (TDD com relógio fake), sem scheduler interno.

## 6. Backup & restore — "backup sem restore testado não é backup"

| Item | Definição |
|---|---|
| Backup | Railway Postgres backup diário automático (RPO ≤ 24h — NFR-07) |
| **Restore testado** | Procedimento abaixo executado **1× antes da entrega** (e a cada troca de schema maior), com evidência (log + timestamp) em `docs/fase-4-operacao-e-loop/etapa-18-observabilidade.md` |
| Procedimento | ① `railway connect` no banco de origem → dump (`pg_dump -Fc`) ② criar Postgres efêmero → restore (`pg_restore`) ③ rodar `alembic current` (deve bater com a revision de prod) ④ smoke: timeline de uma conversa + contagem de eventos ⑤ dropar efêmero |
| Seed p/ testes de migração | Dump anonimizado (PII mascarada — Saída Silver) vira fixture do CI: **up/down/up roda sobre dados reais**, não banco vazio (portão) |

## 7. ✅ Portão de validação da Etapa 8

| Critério | Como se satisfaz | Status |
|---|---|---|
| Migração up e down roda em cópia de dados reais | CI (Etapa 16): Postgres efêmero + seed Silver → `upgrade head` → `downgrade base` → `upgrade head` | 🟡 definido aqui; vira job na Etapa 16 |
| Rollback testado | Mesmo job + `down()` obrigatório por PR + ensaio de restore (§6) | 🟡 idem |
| Deploy sem downtime validado em staging | Não há staging dedicado (custo); o ensaio equivalente = migração aplicada em **cópia do banco real** antes do rollout (§6) + EMC aditivo (§4) + replay idempotente | 🟡 ensaio documentado; executa pré-entrega (T-15) |

> Mesma nota de sequenciamento das Etapas 5/6: os mecanismos estão definidos
> aqui; os **jobs** que os tornam bloqueantes nascem com o pipeline (Etapa 16),
> e o ensaio de restore/migração roda no deploy da demo (T-15/T-16).

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 9 liberada)*
