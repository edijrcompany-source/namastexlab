# ADR-0003 — Runtime Python 3.12 + FastAPI

**Status:** aceito (01/09/2026)

## Contexto
agent-api orquestra: state machine pura + cliente HTTP resiliente + 1 call de
LLM/turno + persistência de eventos. NFR-01 p95 < 5s por turno — dominado
pelo LLM (2-4s) e pelo legado (timeout 3s), não pela linguagem. O legado do
desafio (quote-api) é Python/FastAPI/pydantic.

## Decisão
**Python 3.12 + FastAPI + Pydantic v2** para o agent-api. Módulos de domínio
puros (stdlib), FastAPI apenas na borda `api/`. uv como gerenciador.

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Node/TypeScript** | Unifica linguagem com o front | Recriar validação pydantic-like; ecossistema async HTTP mais imaturo p/ testes de contrato com relógio fake (nosso padrão); diverge do ecossistema do legado | Descartada |
| **Go** | Performance, concorrência | Performance irrelevante (gargalo é I/O externo); verbosidade reduz velocidade de TDD em 3 dias | Descartada |
| **Python + Litro/Flask** | Menos mágica | FastAPI dá OpenAPI automática (insumo da Etapa 5), DI de portas, validação pydantic — ganho líquido positivo | Descartada |

## Consequências
**Positivas:** mesmo ecossistema do legado (padrões de teste/mock reaproveitados;
empatia técnica com o avaliador que escreveu o desafio em FastAPI) · pydantic
v2 casa com os schemas JSON da spec §4 · async nativo para I/O concorrente.
**Negativas:** duas linguagens no monorepo (py+ts) — aceito, bordas separadas
por diretório; performance de CPU não é fator aqui.
