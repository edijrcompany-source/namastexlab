"""Portas do núcleo (C4 §3): contratos que as BORDAS implementam.

O core (conversation) importa SÓ daqui e de domain/* — nunca de app.llm/app.quoting.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.extraction import Campos


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
    ) -> TurnoLLM: ...


class QuoteRefused(Exception):
    """422 do legado: RECUSA DE NEGÓCIO. Sem retry; não conta no breaker."""

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)


class QuoteClientBug(Exception):
    """400 do legado: bug do nosso payload. Sem retry; não conta no breaker."""

    def __init__(self, detalhe: str) -> None:
        self.detalhe = detalhe
        super().__init__(detalhe)


class TransientQuoteError(Exception):
    """Falha transiente esgotada (3 tentativas) ou circuito aberto."""

    def __init__(self, motivo: str, attempts: int = 0) -> None:
        self.attempts = attempts
        super().__init__(motivo)
