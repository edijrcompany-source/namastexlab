# 🗺️ Diagramas as-code (Mermaid)

> Etapa 12 §4 — renderizam no GitHub e no portal. Fonte da verdade das regras
> continua sendo a **spec** (tabela §1.3 é o que os testes executam); estes
> diagramas são a vista humana. Divergência diagrama↔tabela = bug de doc.

## Máquina de estados da conversa (spec §1)

```mermaid
stateDiagram-v2
    [*] --> QUALIFICANDO : primeira mensagem
    QUALIFICANDO --> CONFIRMANDO : dados completos (eco)
    QUALIFICANDO --> QUALIFICANDO : dados parciais / mídia
    CONFIRMANDO --> COTANDO : confirma
    CONFIRMANDO --> CONFIRMANDO : corrige campo
    COTANDO --> COTACAO_APRESENTADA : QUOTE_OK
    COTANDO --> COTACAO_APRESENTADA : recusa 422 (sem cotação)
    COTANDO --> COTACAO_APRESENTADA : falha persistente (sem cotação, retry_pending)
    COTACAO_APRESENTADA --> OBJECAO : 1ª objeção (rebatida)
    OBJECAO --> HANDOFF : 2ª objeção
    OBJECAO --> HANDOFF : aceite (fechamento)
    COTACAO_APRESENTADA --> HANDOFF : aceite
    COTACAO_APRESENTADA --> ENCERRADA_PERDIDO_INELIGIVEL : aceita recusa
    COTACAO_APRESENTADA --> ENCERRADA_PERDIDO : rejeita
    HANDOFF --> HANDOFF : mensagens idempotentes
    ENCERRADA_PERDIDO_INELIGIVEL --> [*]
    ENCERRADA_PERDIDO --> [*]

    note right of COTANDO
        ACL: timeout 3s · 3 tentativas
        breaker 5/30s/2
    end note
    note right of HANDOFF
        Absorvente: só Vendedor tira
        (6 motivos auditáveis)
    end note
```

*Qualquer estado ativo → `HANDOFF` por `preferencia_humana`/`fora_escopo`
(imediato) — omitido para legibilidade; inatividade 24h → `ENCERRADA_SEM_RESPOSTA`.*

## Containers (C4 nível 2 — ADR-0001/0008)

```mermaid
flowchart TB
    subgraph VERCEL["Vercel · região gru1"]
        WEB["apps/web\nNext.js — chat, fila, timeline"]
    end
    subgraph RAILWAY["Railway · região São Paulo"]
        AGENT["agent-api\nPython/FastAPI — monolito modular"]
        LEGADO["quote-api\n(legado do desafio — instável)"]
        PG[("Postgres 16\nevents · conversations · handoffs")]
    end
    LLM["LLM provider (externo)\ngpt-4o-mini · JSON mode"]

    USER([Lead / Avaliador]) -->|HTTPS| WEB
    WEB -->|HTTPS + CORS · turno síncrono| AGENT
    AGENT -->|"HTTP :8000 interno · timeout 3s + retry + breaker"| LEGADO
    AGENT --> PG
    AGENT -->|"HTTPS · chave em secret · PII mascarada"| LLM
```

## Fluxo de um turno (spec §C4 nível 3)

```mermaid
sequenceDiagram
    participant F as apps/web
    participant A as api/
    participant M as privacy/masking
    participant C as conversation/ (núcleo)
    participant L as llm/ + price-guard
    participant Q as quoting/ (ACL)
    participant E as events/ (Postgres)

    F->>A: POST /messages (X-Correlation-Id, Idempotency-Key)
    A->>M: mascarar PII
    M->>C: mensagem mascarada + estado
    C->>L: 1 call/turno (intent+extração+resposta)
    L-->>C: JSON validado (preço só com quote_id)
    C->>Q: se CONFIRMA → cotar
    Q->>Q: 3 tentativas · backoff · breaker
    Q-->>C: QUOTE_OK / recusa / falha
    C->>E: eventos do turno (transação única)
    C-->>A: reply + estado + eventos
    A-->>F: 200 TurnoResponse
```
