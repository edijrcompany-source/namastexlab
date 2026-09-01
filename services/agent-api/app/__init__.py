"""agent-api — monolito modular (ADR-0002/0003).

Bordas em app.api; domínio puro em conversation/privacy/domain; portas
llm/quoting/handoff. Regras de dependência: docs/fase-1.../etapa-4 (C4 §3),
enforced por import-linter no CI.
"""
