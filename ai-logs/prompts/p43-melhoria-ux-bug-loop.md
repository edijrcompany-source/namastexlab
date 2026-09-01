---
n: 43
quando: 2026-09-01 19:03  (base: c40720e)
categoria: bug
---

## Prompt (refinado)

Preciso de melhoria de interface e revisão dos modelos de negócio: quando coloco resposta fora do modelo, ele apenas repete a pergunta sem informar onde errei; corrija com precisão para casos distintos dentro de 99% de cobertura. E quando pede a idade, fico preso em loop sem entender o motivo — revise e corrija também.

## Resultado

Bugs corrigidos: regex de idade em prioridade (4 níveis, sem loop em "30"/"tenho 30"/"idade 30") + feedback de rejeição com motivo. Cobertura 100%, evals 16/16.
