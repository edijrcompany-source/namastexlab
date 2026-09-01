# ADR-0010 — Sem broker: Postgres como transporte de eventos e filas

**Status:** aceito (01/09/2026)

## Contexto
O sistema tem: (a) um event store interno (spec §5.2, 18 tipos) para
rastreabilidade — critério de avaliação do desafio; (b) uma tarefa assíncrona
real: a **retentativa de cotação 2 min após circuito aberto** (spec §1.3/§2);
(c) a fila de handoffs. Volume da demo: 10 conversas simultâneas (NFR-08),
~dezenas de eventos/min. Não há múltiplos consumidores, nem replay de stream,
nem ordenação global entre domínios.

## Decisão
**Nenhum broker.** O Postgres assume os três papéis com semântica de
mensageria completa:

| Necessidade | Mecanismo |
|---|---|
| Publicação consistente | **Transactional outbox**: eventos gravados na MESMA transação do turno (já garantido pela Etapa 6 §4.1 — "transação atômica por turno") |
| Fila de tarefas (`retry_quote`) | Tabela `conversations` (`retry_pending`, `retry_attempts`, `retry_lease_expires_at`) com claim via `FOR UPDATE SKIP LOCKED` |
| Fila de handoffs | Tabela `handoffs` (Etapa 8) — consumida por pull pelo Vendedor |
| Mensagem venenosa | Tabela **`dead_letters`** (migração `0002`) |
| Consumo futuro externo | Cursor sobre a outbox (`events`) com **schema público versionado** (Etapa 9 §3) |

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **RabbitMQ** | Exchange/fila maduras, DLQ nativa | +1 serviço gerenciado (~custo/operação) para dezenas de msg/min; consistência com o turno exigiria outbox de qualquer forma | Reserva |
| **Kafka** | Replay, ordering, stream | Ordem de grandeza errada; custo/ops máximos; sem caso de uso | Descartado |
| **SQS + LocalStack** | Gerenciado, barato | Nuvem AWS no loop da demo; LocalStack só p/ teste; +1 dependência externa | Descartado |
| **Postgres (outbox + SKIP LOCKED)** ✅ | Zero infra nova; transação = consistência grátis; DLQ/retry/lease implementáveis e TESTÁVEIS com relógio fake (TDD) | Polling (latência ≥ intervalo do worker — 15s é suficiente p/ retentativa de 2min); sem push | **Aceita** |

## Consequências
**Positivas:** consistência transacional out-of-the-box (o guia pede outbox —
nós JÁ somos o outbox); os dois testes do portão (kill/religar sem duplicar;
venenosa na DLQ) são testes de unidade com relógio fake, sem emulação de fila;
custo zero.
**Negativas/riscos:** polling não escala para notificação sub-segundo (a UX
atual não precisa — turno síncrono); lease exige relógio e disciplina
(colunas de lease na `0002`).
**Gatilhos de migração (dor medida, não antecipada):** > 1.000 handoffs/dia ·
consumidores externos reais com push · necessidade de replay/stream ·
polling visível em p95 → migrar tarefa p/ RabbitMQ/SQS mantendo o envelope de
evento público (§3) — o contrato não muda, só o transporte.
