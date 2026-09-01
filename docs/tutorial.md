# 📚 Tutorial — Primeiros Passos

> Diátaxis/Tutorial: aprender com as mãos no teclado. Tempo total: ~55 min.

## 1. Ambiente (10 min)

1. Clone o repo e abra no VS Code — o **Dev Container** sobe sozinho
   (Python 3.12 + Node 20 + Docker).
2. Sem VS Code? Requisitos: Docker, `make`, `uv`, `pnpm`.

## 2. Entenda o produto sem escrever nada (5 min)

```bash
make mock   # Prism sobe o agent-api MOCKADO em :4010 (contrato = fonte única)
```

Abra o front apontando para o mock — sinta o fluxo: conversa → qualificação →
cotação → handoff.

## 3. Suba tudo de verdade (10 min)

```bash
make dev    # agent-api :8001 · quote-api :8000 (instável DE PROPÓSITO) · postgres
```

`GET :8001/health` → `{"agent":"ok","legado":"ok"}`. Derrube o quote-api e
veja a resiliência agir (retry → circuito → mensagem honesta).

## 4. Leia o contexto (10 min)

1. `AGENTS.md` inteiro — bússola do projeto (regras invioláveis + armadilhas).
2. `docs/README.md` — mapa das 21 etapas e status.
3. A spec da área que vai tocar: `docs/fase-0-negocio-e-requisitos/etapa-3-spec.md`.

## 5. Primeiro PR com TDD (15-20 min)

1. Pegue um ticket do template — comece por um `good first issue` (T-02 masking).
2. **Teste primeiro** (red) → implementação mínima (green) → refatore.
3. `make lint && make test` → PR pequeno citando a seção da spec
   (ex.: "implementa spec §3").

## Próximos passos

- [How-to](./how-to.md) para tarefas do dia a dia · [Referência](./referencia.md)
  para consulta · [Explicação](./README.md) para entender as decisões.
