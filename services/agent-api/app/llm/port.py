"""Porta LLMPort (ADR-0005) — 1 call/turno, saída estruturada (spec §4.1)."""

from __future__ import annotations

from typing import Protocol

from app.llm.extraction import Campos


class TurnoLLM:
    """Resultado do único call de LLM por turno (spec §4.1)."""

    def __init__(
        self,
        intent: str,
        resposta: str,
        campos: Campos | None = None,
    ) -> None:
        self.intent = intent
        self.resposta = resposta
        self.campos = campos or Campos()


class LLMPort(Protocol):
    def completar(
        self,
        *,
        estado: str,
        dados: Campos,
        historico: list[str],
        mensagem: str,
        aviso_correcao: bool = False,
    ) -> TurnoLLM:
        """Classifica intent + extrai campos + redige resposta (PT-BR).

        aviso_correcao=True quando o price-guard rejeitou a resposta anterior
        (2ª violação ⇒ orchestrator usa fallback canônico).
        """
        ...
