"""Erros da ACL — classificação da etapa-6 §3.2 (espelham o contrato do legado)."""

from __future__ import annotations


class QuoteRefused(Exception):
    """422 do legado: RECUSA DE NEGÓCIO (inelegível/plano inexistente).

    Sem retry e NÃO conta para o circuit breaker — não é falha.
    """

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)


class QuoteClientBug(Exception):
    """400 do legado: payload nosso inválido — bug do nosso lado.

    Sem retry (não vai magicamente corrigir); não conta para o breaker.
    O chamador loga ERROR e trata como falha técnica de produto (etapa-6 §3.2).
    """

    def __init__(self, detalhe: str) -> None:
        self.detalhe = detalhe
        super().__init__(detalhe)


class TransientQuoteError(Exception):
    """Falha TRANSIENTE esgotada (5xx/timeout nas 3 tentativas) ou circuito aberto.

    O chamador responde com a mensagem honesta (spec §6.6) — nunca inventa preço.
    """

    def __init__(self, motivo: str, attempts: int = 0) -> None:
        self.attempts = attempts
        super().__init__(motivo)
