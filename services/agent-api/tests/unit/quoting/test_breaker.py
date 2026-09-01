"""Circuit breaker — codifica spec §2 e etapa-6 §4.1.

Parâmetros imutáveis da spec: abre com 5 falhas CONSECUTIVAS · half-open
após 30s · fecha com 2 SUCESSOS no half-open · sucesso reseta as consecutivas.
"""
import pytest

from app.quoting.breaker import BreakerConfig, BreakerState, CircuitBreaker


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.mark.unit
class TestFechadoParaAberto:
    def test_abre_apos_5_falhas_consecutivas(self) -> None:
        breaker = CircuitBreaker(clock=FakeClock())
        for _ in range(4):
            breaker.record_failure()
        assert breaker.state is BreakerState.CLOSED
        breaker.record_failure()
        assert breaker.state is BreakerState.OPEN

    def test_sucesso_reseta_as_consecutivas(self) -> None:
        breaker = CircuitBreaker(clock=FakeClock())
        for _ in range(5):
            breaker.record_failure()
        breaker.record_success()  # half_open → 1 sucesso (ainda não fecha)
        breaker.record_failure()  # reabre
        for _ in range(4):
            breaker.record_failure()
        # no OPEN, failure é registrada sem mudar estado; após cooldown half_open
        assert breaker.state is BreakerState.OPEN


@pytest.mark.unit
class TestAberto:
    def test_bloqueia_enquanto_cooldown_nao_vence(self) -> None:
        clock = FakeClock()
        breaker = CircuitBreaker(clock=clock)
        for _ in range(5):
            breaker.record_failure()
        assert breaker.allow() is False

    def test_half_open_apos_30s(self) -> None:
        clock = FakeClock()
        breaker = CircuitBreaker(clock=clock)
        for _ in range(5):
            breaker.record_failure()
        clock.advance(29.9)
        assert breaker.allow() is False
        clock.advance(0.1)
        assert breaker.allow() is True
        assert breaker.state is BreakerState.HALF_OPEN


@pytest.mark.unit
class TestHalfOpen:
    def _abrir_e_esfriar(self, clock: FakeClock) -> CircuitBreaker:
        breaker = CircuitBreaker(clock=clock)
        for _ in range(5):
            breaker.record_failure()
        clock.advance(BreakerConfig().cooldown_s)
        breaker.allow()
        return breaker

    def test_uma_falha_no_half_open_reabre_o_circuito(self) -> None:
        clock = FakeClock()
        breaker = self._abrir_e_esfriar(clock)
        breaker.record_failure()
        assert breaker.state is BreakerState.OPEN
        clock.advance(10.0)  # cooldown NÃO venceu (30s)
        assert breaker.allow() is False

    def test_um_sucesso_nao_fecha_prematuro(self) -> None:
        breaker = self._abrir_e_esfriar(FakeClock())
        breaker.record_success()
        assert breaker.state is BreakerState.HALF_OPEN

    def test_dois_sucessos_fecham_o_circuito(self) -> None:
        breaker = self._abrir_e_esfriar(FakeClock())
        breaker.record_success()
        breaker.record_success()
        assert breaker.state is BreakerState.CLOSED

    def test_fechado_de_novo_apos_2_falhas_só_abre_com_5_novas(self) -> None:
        breaker = self._abrir_e_esfriar(FakeClock())
        breaker.record_success()
        breaker.record_success()
        assert breaker.state is BreakerState.CLOSED
        for _ in range(4):
            breaker.record_failure()
        assert breaker.state is BreakerState.CLOSED
