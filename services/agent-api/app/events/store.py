"""Store — porta de persistência (T-06). v1: InMemoryStore (dev sem Docker e
testes). Impl Postgres/SQLAlchemy pluga pela mesma porta (dívida registrada no
plano — ver docs/plano-implementacao.md §marcos).
"""

from __future__ import annotations

from typing import Protocol

from app.conversation.models import Conversa


class Store(Protocol):
    def salvar(self, conversa: Conversa) -> None: ...
    def obter(self, conversation_id: str) -> Conversa | None: ...
    def handoffs_pendentes(self) -> list[Conversa]: ...
    def apagar(self, conversation_id: str) -> bool: ...


class InMemoryStore:
    """Volátil — processos de dev/teste. Sem segredos, sem PII externa."""

    def __init__(self) -> None:
        self._dados: dict[str, Conversa] = {}

    def salvar(self, conversa: Conversa) -> None:
        self._dados[conversa.id] = conversa

    def obter(self, conversation_id: str) -> Conversa | None:
        return self._dados.get(conversation_id)

    def handoffs_pendentes(self) -> list[Conversa]:
        return [
            c
            for c in self._dados.values()
            if c.estado.value == "HANDOFF" and c.handoff and c.handoff.get("status") == "pendente"
        ]

    def apagar(self, conversation_id: str) -> bool:
        return self._dados.pop(conversation_id, None) is not None
