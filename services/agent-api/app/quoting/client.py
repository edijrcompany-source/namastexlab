"""QuoteAcl — anti-corruption layer do legado (spec §2, ADR da Etapa 4 §C4).

Política: timeout 3s/tentativa · 3 tentativas · backoff exponencial 500ms/1000ms
+ jitter U(0,250ms) · breaker 5/30s/2 (só transientes contam) · 422 = recusa de
negócio (sem retry) · 400 = bug do nosso lado (sem retry).

Tudo injetável (http/clock/sleeper/rng) — os testes rodem offline e sem dormir.
"""

from __future__ import annotations

import os
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

from app.domain.ports import QuoteClientBug, QuoteRefused, TransientQuoteError
from app.quoting.breaker import CircuitBreaker


@dataclass(frozen=True)
class QuoteAclConfig:
    timeout_ms: int = 3000
    max_attempts: int = 3
    backoff_base_ms: float = 500.0
    backoff_multiplier: float = 2.0
    jitter_max_ms: float = 250.0

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> QuoteAclConfig:
        """Defaults da spec §2, overridables por env (etapa-6 §4.1 — wiring na T-07)."""
        env = env if env is not None else dict(os.environ)
        return cls(
            timeout_ms=int(env.get("QUOTE_TIMEOUT_MS", cls.timeout_ms)),
            max_attempts=int(env.get("QUOTE_MAX_ATTEMPTS", cls.max_attempts)),
        )


class QuoteAcl:
    def __init__(
        self,
        base_url: str,
        http: httpx.Client | None = None,
        config: QuoteAclConfig | None = None,
        breaker: CircuitBreaker | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._config = config or QuoteAclConfig()
        self._http = http or httpx.Client(timeout=self._config.timeout_ms / 1000)
        self.breaker = breaker or CircuitBreaker(clock=clock)
        self._sleeper = sleeper
        # S311: jitter de backoff NÃO é uso criptográfico — é aleatoriedade de escala
        self._rng = rng or random.Random()  # noqa: S311

    def cotar(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Cota no legado. Levanta QuoteRefused (negócio), QuoteClientBug (nosso
        erro) ou TransientQuoteError (3 falhas/circuito). Sucesso retorna o JSON."""
        if not self.breaker.allow():
            raise TransientQuoteError("circuito_aberto")

        for attempt in range(1, self._config.max_attempts + 1):
            try:
                resp = self._http.post(f"{self._base_url}/quote", json=payload)
            except (httpx.TimeoutException, httpx.TransportError):
                self._register_failure(attempt)
                continue

            if resp.status_code == 200:
                self.breaker.record_success()
                return resp.json()
            if resp.status_code == 422:
                raise QuoteRefused(resp.json().get("motivo", "recusa_sem_motivo"))
            if resp.status_code == 400:
                raise QuoteClientBug(resp.json().get("detalhe", "payload_invalido"))
            # 5xx (e qualquer outro inesperado do legado): transiente
            self._register_failure(attempt)

        raise TransientQuoteError(
            f"falha_apos_{self._config.max_attempts}_tentativas",
            attempts=self._config.max_attempts,
        )

    def _register_failure(self, attempt: int) -> None:
        self.breaker.record_failure()
        if attempt < self._config.max_attempts:
            base = self._config.backoff_base_ms * (self._config.backoff_multiplier ** (attempt - 1))
            self._sleeper((base + self._rng.uniform(0, self._config.jitter_max_ms)) / 1000)
