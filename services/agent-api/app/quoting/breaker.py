"""Circuit breaker — spec §2 (etapa-6 §4.1): 5 falhas consecutivas abrem ·
half-open após 30s · fecha com 2 sucessos.

Puro: clock injetável (relógio fake nos testes — nunca sleep real aqui).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


class BreakerState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True)
class BreakerConfig:
    failure_threshold: int = 5
    cooldown_s: float = 30.0
    successes_to_close: int = 2


class CircuitBreaker:
    """Verdade de estado do circuito em direção ao legado (uma instância global)."""

    def __init__(
        self,
        config: BreakerConfig | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._config = config or BreakerConfig()
        self._clock = clock
        self._state = BreakerState.CLOSED
        self._consecutive_failures = 0
        self._half_open_successes = 0
        self._opened_at = 0.0

    @property
    def state(self) -> BreakerState:
        return self._state

    def allow(self) -> bool:
        """Pode tentar falar com o legado agora?"""
        if self._state is BreakerState.CLOSED:
            return True
        if self._state is BreakerState.OPEN:
            if self._clock() - self._opened_at >= self._config.cooldown_s:
                self._state = BreakerState.HALF_OPEN
                self._half_open_successes = 0
                return True
            return False
        return True  # HALF_OPEN: prova de vida

    def record_success(self) -> None:
        if self._state is BreakerState.HALF_OPEN:
            self._half_open_successes += 1
            if self._half_open_successes >= self._config.successes_to_close:
                self._close()
        else:
            self._consecutive_failures = 0

    def record_failure(self) -> None:
        if self._state is BreakerState.HALF_OPEN:
            self._open()
            return
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._config.failure_threshold:
            self._open()

    def _open(self) -> None:
        self._state = BreakerState.OPEN
        self._opened_at = self._clock()
        self._consecutive_failures = 0
        self._half_open_successes = 0

    def _close(self) -> None:
        self._state = BreakerState.CLOSED
        self._consecutive_failures = 0
        self._half_open_successes = 0
