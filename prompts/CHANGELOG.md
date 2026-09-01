# Changelog de Prompts

> Governança (Etapa 20 §3): toda mudança de prompt passa pela suíte de evals
> com LLM REAL (Etapa 19 §3, job `evals-prompts`), registra motivo + números
> da suíte aqui, e recebe revisão humana como qualquer código.

## [1.0.0] — 2026-09-01

### Adicionado
- `system_v1.md` — versão inicial, derivada da spec §4.1/§4.2 (Etapa 3):
  - 7 regras invioláveis (preço só de `contexto.cotacoes`, sem desconto,
    sem revelar instruções, PII permanece mascarada, mídia→texto, escopo)
  - formato JSON estrito de saída (intent + extração + resposta)
  - tom PT-BR e elementos obrigatórios por situação (cotação/recusa/falha)
- **Suíte na primeira execução (T-09/T-10):** pendente — números registram aqui
  quando a suíte rodar (E1 ≥90% · E2 ≥95% · E3 0/20 · E4 0).
