"""Modelos da conversa (snapshot + histórico) — spec §5.1/§5.2."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.conversation.state_machine import Estado
from app.domain.extraction import Campos


def _agora() -> datetime:
    return datetime.now(UTC)


@dataclass
class Mensagem:
    role: str  # lead | agente
    tipo: str  # text | image | audio | document
    texto: str  # PII já mascarada (spec §3)
    criado_em: datetime = field(default_factory=_agora)


@dataclass
class Conversa:
    id: str
    estado: Estado = Estado.QUALIFICANDO
    dados: Campos = field(default_factory=Campos)
    historico: list[Mensagem] = field(default_factory=list)
    cotacoes: list[dict] = field(default_factory=list)
    eventos: list[dict] = field(default_factory=list)
    fora_escopo_anterior: bool = False
    circuito_reaberturas: int = 0
    retry_pending: bool = False
    handoff: dict | None = None
    correlation_id: str | None = None
    criada_em: datetime = field(default_factory=_agora)
    atualizada_em: datetime = field(default_factory=_agora)

    def proximo_seq(self) -> int:
        return len(self.eventos) + 1

    def registrar_evento(self, tipo: str, payload: dict | None = None) -> None:
        self.eventos.append(
            {
                "seq": self.proximo_seq(),
                "type": tipo,
                "payload": payload or {},
                "correlation_id": self.correlation_id,
                "criado_em": _agora().isoformat(),
            }
        )
        self.atualizada_em = _agora()
