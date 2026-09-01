# PRD — Agente de Vendas AutoSeguro (uma página)

**Projeto:** resposta ao desafio FDE/AI Engineer da Namastex · **Versão:** 1.0 (01/09/2026)

## Problema
Leads de seguro auto chegam por WhatsApp e dependem de 4 vendedores humanos para
qualificar, cotar (num legado que falha 20% e demora 8s em 10% das vezes) e
decidir. ~30% dos leads são inelegíveis e mesmo assim queimam funil; 20% das
conversas terminam sem resposta.

## Escopo (in)
1. Agente conversacional web que qualifica (veículo+ano, idade, CEP), cota via
   API `/quote` com resiliência (timeout 3s, 3 tentativas, circuit breaker
   5/30s/2) e apresenta cotação completa (prêmio, franquia, carência 30d, pró-rata).
2. Critério de handoff humano explícito com 6 motivos auditáveis.
3. Zero preço inventado (guardrail por código) e PII mascarada em 100% das saídas.
4. Pipeline Bronze→Silver do dataset; suite de evals (extração, handoff,
   adversarial de 20 ataques).
5. Demo pública: front Next/Vercel + agent-api/quote-api/Postgres no Railway.
6. `ai-logs/` e log de execução exportável (entregáveis do desafio).

## Fora de escopo (out)
Emissão de apólice/boleto · WhatsApp real · multi-idioma · alterar o
`quote-service` · auth de usuário final · painéis além da fila de handoff.

## Critérios de aceite (top)
- C1-C6 da spec (`etapa-3-spec.md` §11) passando em CI contra legado mockado.
- NFR-09 (0 preços inventados), NFR-12 (0 PII em logs) e NFR-14 (20/20
  adversarial) — **blockers**, falham o build.
- TRA ≥ 70% em bateria simulada de conversas elegíveis.
- Log de execução completo exportável do caminho feliz.

## Métrica norte
**TRA ≥ 70%** — % de leads elegíveis com cotação correta ponta a ponta sem
humano, guardrails de zero-preço-inventado e TTFC < 2 min.

## Fontes
Desafio: `namastex-fde-challenge/` (somente leitura) · Spec: `etapa-3-spec.md` ·
Glossário: `etapa-1-linguagem-ubiqua.md` · NFRs: `etapa-2-requisitos-e-nfrs.md`.
