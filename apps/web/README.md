# apps/web — Front (Next.js → Vercel)

Chat de demo do Agente + fila de handoffs + timeline rastreável + export.

- Tipos **gerados** do contrato: `src/types/api.d.ts` (`make codegen`) — nunca editar
- Strings de tela: **somente** `../../messages/pt-BR.json` (ADR-0009)
- Formatos: `src/lib/format.ts` (único util — Etapa 7 §3)
- Error boundaries por rota + correlation ID (Etapa 6 §6)
- Nasce na Fase 2/3 via TDD (tasks T-11..T-13)
