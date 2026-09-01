# services/agent-api — Backend (Python 3.12/FastAPI → Railway)

Monolito modular (ADR-0002/0003): `conversation/` (puro) + portas `llm/`, `quoting/`, `handoff/` + `events/`, `privacy/`, `domain/`. Regras de dependência: C4 nível 3 (import-linter no CI).

- TDD obrigatório na lógica determinística; FakeLLM no CI (ADR-0005)
- Nasce na Fase 2 via Épico A/B (T-01..T-10)
