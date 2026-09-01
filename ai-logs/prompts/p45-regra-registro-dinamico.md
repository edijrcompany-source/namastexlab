---
n: 45
quando: "2026-09-01 19:08"
commit_base: "ee7b8c1"
categoria: feedback
---

## Prompt (refinado)

O índice dos prompts não está atualizando dinamicamente conforme os commits. Crie uma rotina automática para isso: cada novo prompt deve ser a primeira ação commitar o prompt e atualizar o log, e como segunda ação revisar toda a arquitetura para nunca perder o contexto. Grave essa regra na memória.

## Resultado

Registrado via scripts/register_prompt.py (regra de negócio: primeira ação de todo prompt).
