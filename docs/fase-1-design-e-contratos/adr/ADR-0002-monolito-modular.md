# ADR-0002 — Monolito modular (agent-api)

**Status:** aceito (01/09/2026)

## Contexto
O sistema tem 4 bounded contexts (Atendimento, Cotação, Escalonamento,
Privacidade). Volume alvo da demo: 10 conversas simultâneas (NFR-08), TRA
avaliada em bateria simulada. Time de 1, prazo curto. O guia de processo
estipula: monolito primeiro, extrair serviço com **dor real medida**.

## Decisão
**Um único deploy (agent-api) como monolito modular**: módulos Python com
fronteiras internas explícitas (`conversation/`, `llm/`, `quoting/`, `handoff/`,
`events/`, `privacy/`, `domain/`) e **regras de dependência enforced em CI**
(ver C4 nível 3): domínio puro sem I/O, bordas injetadas por portas.

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Microsserviços** (agent + quoting-worker + handoff-svc) | Escala independente | Sem dor medida que justifique: 10 VUs; custo operacional ×3 (deploy, rede, observabilidade); latência extra entre serviços; TDD de integração mais lento | Descartada |
| **Serverless functions** (turno como lambda) | Scale-to-zero | Turno síncrono de até ~8s (LLM+legado) contra limites de execução; conexões Postgres efêmeras; cold start no meio da conversa | Descartada |
| **Monolito modular** ✅ | 1 deploy · testes de domínio puros rápidos · extração futura facilitada pelas portas | Disciplina interna necessária | **Aceita** |

## Consequências
**Positivas:** velocidade de entrega (1 pipeline, 1 runtime) · cobertura
NFR-16 fácil de isolar nos módulos puros · o desafio avalia decisões
defensáveis — esta é literalmente a recomendada pelo guia.
**Negativas/riscos:** acoplamento interno se as regras de dependência
enferrujarem → mitigação: import-linter no CI.
**Plano de extração (gatilhos medidos):** documentado no C4 nível 3 —
`quoting/` sai primeiro se p95 do legado degradar NFR-01 em produção.
