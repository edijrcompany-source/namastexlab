"""QuoteAcl — codifica spec §2 (timeout 3s · 3 tentativas · backoff 500/1000+jitter)
e a classificação de erros da etapa-6 §3.2 (422=negócio sem retry · 400=bug ·
5xx/timeout=transiente com retry · breaker conta SÓ transiente).

Inclui a simulação do NFR-04: 1.000 cotações com p_falha=0.30/tentativa ⇒
sucesso eventual ≥95% (matemática: 1−0.3³=97.3%).
"""

import random
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from app.quoting.breaker import CircuitBreaker
from app.quoting.client import QuoteAcl, QuoteAclConfig
from app.quoting.exceptions import QuoteClientBug, QuoteRefused, TransientQuoteError


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeSleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def make_acl(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    rng: random.Random | None = None,
    clock: FakeClock | None = None,
    sleeper: FakeSleeper | None = None,
) -> tuple[QuoteAcl, FakeSleeper]:
    """Monta a ACL com transporte mockado (sem rede — testável offline)."""
    sleeper = sleeper or FakeSleeper()
    acl = QuoteAcl(
        base_url="http://quote-api.test",
        http=httpx.Client(transport=httpx.MockTransport(handler)),
        config=QuoteAclConfig(timeout_ms=3000, max_attempts=3),
        breaker=CircuitBreaker(clock=clock or FakeClock()),
        clock=clock or FakeClock(),
        sleeper=sleeper,
        rng=rng or random.Random(0),
    )
    return acl, sleeper


def _503(_: httpx.Request) -> httpx.Response:
    return httpx.Response(503, json={"error": "upstream_unavailable", "message": "fora"})


PAYLOAD: dict[str, Any] = {"plano_id": "essencial", "idade": 30, "veiculo_ano": 2022}


@pytest.mark.unit
class TestCaminhoFeliz:
    def test_200_na_primeira_retorna_payload_sem_backoff(self) -> None:
        acl, sleeper = make_acl(lambda _: httpx.Response(200, json={"plano_id": "essencial"}))

        result = acl.cotar(PAYLOAD)

        assert result["plano_id"] == "essencial"
        assert sleeper.delays == []


@pytest.mark.unit
class TestRetryTransiente:
    def test_503_503_200_succeeds_na_terceira_com_dois_backoffs(self) -> None:
        calls = {"n": 0}

        def handler(_: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            return _503(None) if calls["n"] < 3 else httpx.Response(200, json={"ok": True})

        acl, sleeper = make_acl(handler)

        assert acl.cotar(PAYLOAD)["ok"] is True
        assert calls["n"] == 3
        assert len(sleeper.delays) == 2

    def test_backoff_exponencial_com_jitter_deterministico(self) -> None:
        rng = random.Random(7)
        j1, j2 = rng.uniform(0, 250), rng.uniform(0, 250)  # mesma sequência do client
        acl, sleeper = make_acl(_503, rng=random.Random(7))
        with pytest.raises(TransientQuoteError):
            acl.cotar(PAYLOAD)
        # sleeper recebe SEGUNDOS (spec §2 em ms → s)
        assert sleeper.delays == [(500.0 + j1) / 1000, (1000.0 + j2) / 1000]

    def test_3_tentativas_esgotam_e_levanta_transiente(self) -> None:
        calls = {"n": 0}

        def handler(r: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            return _503(r)

        acl, _ = make_acl(handler)
        with pytest.raises(TransientQuoteError) as exc:
            acl.cotar(PAYLOAD)
        assert exc.value.attempts == 3
        assert calls["n"] == 3

    @pytest.mark.parametrize("status", [500, 502, 503])
    def test_todos_os_5xx_sao_transientes(self, status: int) -> None:
        acl, _ = make_acl(lambda _: httpx.Response(status, json={}))
        with pytest.raises(TransientQuoteError):
            acl.cotar(PAYLOAD)

    def test_timeout_e_transiente(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("legado lento (8s)")

        acl, _ = make_acl(handler)
        with pytest.raises(TransientQuoteError):
            acl.cotar(PAYLOAD)

    def test_erro_de_conexao_e_transiente(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("recusado")

        acl, _ = make_acl(handler)
        with pytest.raises(TransientQuoteError):
            acl.cotar(PAYLOAD)


@pytest.mark.unit
class TestErrosDeNegocio:
    def test_422_levanta_recusa_sem_retry(self) -> None:
        calls = {"n": 0}

        def handler(_: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            return httpx.Response(422, json={"error": "cotacao_recusada", "motivo": "Idade acima"})

        acl, sleeper = make_acl(handler)
        with pytest.raises(QuoteRefused) as exc:
            acl.cotar(PAYLOAD)
        assert "Idade acima" in exc.value.motivo
        assert calls["n"] == 1  # SEM retry
        assert sleeper.delays == []

    def test_422_nao_conta_para_o_breaker(self) -> None:
        acl, _ = make_acl(
            lambda _: httpx.Response(422, json={"error": "cotacao_recusada", "motivo": "x"})
        )
        for _ in range(10):
            with pytest.raises(QuoteRefused):
                acl.cotar(PAYLOAD)
        assert acl.breaker.state.value == "closed"

    def test_400_e_bug_nosso_sem_retry_e_sem_breaker(self) -> None:
        calls = {"n": 0}

        def handler(_: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            return httpx.Response(400, json={"error": "payload_invalido", "detalhe": "idade"})

        acl, _ = make_acl(handler)
        with pytest.raises(QuoteClientBug):
            acl.cotar(PAYLOAD)
        assert calls["n"] == 1
        assert acl.breaker.state.value == "closed"


@pytest.mark.unit
class TestCircuitoAberto:
    def test_circuito_aberto_falha_rapido_sem_chamar_o_legado(self) -> None:
        calls = {"n": 0}

        def handler(_: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            return _503(None)

        acl, _ = make_acl(handler)
        for _ in range(1):  # 1 cotação = 3 tentativas = 3 falhas consecutivas
            with pytest.raises(TransientQuoteError):
                acl.cotar(PAYLOAD)
        # forçar abertura direta: mais 2 falhas consecutivas no breaker
        acl.breaker.record_failure()
        acl.breaker.record_failure()
        assert acl.breaker.state.value == "open"

        with pytest.raises(TransientQuoteError) as exc:
            acl.cotar(PAYLOAD)
        assert "circuito" in str(exc.value).lower()
        assert calls["n"] == 3  # nenhum request novo


@pytest.mark.unit
class TestSimulacaoNfr04:
    def test_mil_cotacoes_com_30pc_de_falha_por_tentativa(self) -> None:
        """NFR-04: p_falha=0.30/tentativa, 3 tentativas ⇒ sucesso ≥95%.

        Clock fake avança 60s por request: entre cotações o cooldown (30s) do
        breaker sempre vence — a simulação exercita retry + breaker juntos.
        """
        rng = random.Random(42)
        rolls = [rng.random() for _ in range(4000)]
        box = {"i": 0}
        clock = FakeClock()

        def handler(_: httpx.Request) -> httpx.Response:
            clock.advance(60.0)
            fail = rolls[box["i"] % len(rolls)] < 0.30
            box["i"] += 1
            if fail:
                return httpx.Response(503, json={"error": "upstream_unavailable"})
            return httpx.Response(200, json={"plano_id": "essencial"})

        acl, _ = make_acl(handler, clock=clock)

        ok = 0
        for _ in range(1000):
            try:
                acl.cotar(PAYLOAD)
                ok += 1
            except TransientQuoteError:
                pass  # recusa de negócio não existe nesta simulação
            except QuoteRefused:
                pass

        assert ok >= 950, f"sucesso eventual {ok}/1000 abaixo do NFR-04 (95%)"


@pytest.mark.unit
class TestConfigFromEnv:
    def test_defaults_da_spec(self) -> None:
        cfg = QuoteAclConfig.from_env(env={})
        assert cfg.timeout_ms == 3000
        assert cfg.max_attempts == 3

    def test_env_override(self) -> None:
        cfg = QuoteAclConfig.from_env(env={"QUOTE_TIMEOUT_MS": "1500", "QUOTE_MAX_ATTEMPTS": "5"})
        assert cfg.timeout_ms == 1500
        assert cfg.max_attempts == 5
