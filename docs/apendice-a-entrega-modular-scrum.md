# Apêndice A — Padrão de Entrega Modular com Scrum

> Acrescentado na fase de certificação (01/09/2026). Convive com o trunk-based
> do ADR-0011: branches **curtos por fatia vertical**, PR com preview, merge
> cedo — o Scrum aqui organiza o *backlog e o aceite*, não cria long-lived branches.

## A.1 Ritmo

| Prática | Norma |
|---|---|
| Sprint | **1–2 semanas**; kickoff com o backlog priorizado da spec de desenvolvimento (`etapa-3-tasks.md`) |
| Backlog | **Fatias verticais demonstráveis** — cada história cruza banco → API → front (nunca "só o back") |
| Definition of Ready | A da Etapa 2 §4 + a fatia estar mapeada num cenário C1-C6 ou NFR |
| Review | Demo da fatia no **preview da Vercel** (cada PR gera URL própria) |
| Retrpective | Alimenta a RETRO.md (Etapa 21) ao fim de cada sprint |

## A.2 A fatia vertical (unidade de entrega)

```
1 história = 1 fatia demonstrável
   banco:     migração/tabela (Etapa 8)          ┐
   API:       endpoint + testes (§5.4, gates)     ├─ 1 PR · 1 preview · 1 demo
   front:     UI consumindo types do contrato     ┘
```

- História que não toca as 3 camadas precisa justificar no PR (ex.: refactor).
- **Nenhuma história fecha sem validação visual.**

## A.3 PR padrão (gate + preview + evidência)

Todo PR de fatia contém:

1. **Preview Vercel** (automático) — link no PR;
2. **Evidência visual**: screenshot(s) ou vídeo curto da jornada (ex.: C1 no preview);
3. **Checklist de aceite** (do template `.github/PULL_REQUEST_TEMPLATE.md`):
   spec § citada · testes primeiro · NFRs atingidos · PII/zero-preço verificados;
4. **Aceite humano por feature** — 1 approval (CODEOWNERS); IA nunca fecha sozinha (regra da Fase 3).

## A.4 Rastreabilidade

fatia → user story (etapa-2) → cenário C1-C6 (spec §11) → PR (evidência visual)
→ commit gitmoji. A auditoria final usa essa cadeia item a item.
