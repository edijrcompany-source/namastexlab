"""Branches restantes do orchestrator/LLM/formatting/i18n — até 100%."""

import httpx
import pytest

from app.formatting import format_brl
from app.i18n import _caminho_catalogo, carregar
from app.llm.fake import FakeLLM
from app.llm.port import TurnoLLM
from tests.unit.conversation.test_orchestrator import StubACL, orquestrador


@pytest.mark.unit
def test_conversa_inexistente_levanta_keyerror() -> None:
    with pytest.raises(KeyError):
        orquestrador().processar("nao-existe", texto="oi")


@pytest.mark.unit
def test_sem_texto_e_sem_midia_e_valueerror() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    with pytest.raises(ValueError):
        orch.processar(conv.id)


@pytest.mark.unit
def test_recusa_veiculo_pela_api_vira_recusa_empatica() -> None:
    acl = StubACL(recusa="Veiculo com mais de 20 anos nao e aceito.")
    orch = orquestrador(acl)
    conv = orch.iniciar()
    orch.processar(conv.id, texto="Onix 2022, 30 anos, CEP 01310-100")
    orch.processar(conv.id, texto="é isso")
    assert conv.estado.value == "COTACAO_APRESENTADA"
    assert "20 anos" in conv.historico[-1].texto
    assert any(e["type"] == "quote_refused" for e in conv.eventos)


@pytest.mark.unit
def test_recusa_idade_pela_api() -> None:
    acl = StubACL(recusa="Idade acima do limite de aceitacao (75 anos).")
    orch = orquestrador(acl)
    conv = orch.iniciar()
    orch.processar(conv.id, texto="Onix 2022, 74 anos, CEP 01310-100")  # local ok
    orch.processar(conv.id, texto="é isso")
    assert "75 anos" in conv.historico[-1].texto


@pytest.mark.unit
def test_pre_elegibilidade_local_de_veiculo() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    orch.processar(conv.id, texto="Gol 1998, 40 anos, CEP 01310-100")
    orch.processar(conv.id, texto="é isso")
    assert "20 anos" in conv.historico[-1].texto
    assert not any(e["type"] == "quote_requested" for e in conv.eventos)


@pytest.mark.unit
def test_circuito_reaberto_na_mesma_conversa_vira_handoff_tecnico() -> None:
    acl = StubACL(transiente=True)
    # breaker já aberto + conversa já teve 1 abertura ⇒ CIRCUITO_REABERTO
    acl.breaker._state = acl.breaker._state.__class__("open")
    orch = orquestrador(acl)
    conv = orch.iniciar()
    conv.circuito_reaberturas = 1
    orch.processar(conv.id, texto="Onix 2022, 30 anos, CEP 01310-100")
    orch.processar(conv.id, texto="é isso")
    assert conv.estado.value == "HANDOFF"
    assert conv.handoff["motivo"] == "falha_tecnica"


class LLMViolador:
    """Viola o price-guard N vezes seguidas para exercitar regeneração/fallback."""

    def __init__(self, violacoes: int) -> None:
        self._violacoes = violacoes
        self._chamadas = 0

    def completar(self, **_: object) -> TurnoLLM:
        self._chamadas += 1
        if self._chamadas <= self._violacoes:
            return TurnoLLM("pede_humano", "Consigo por R$ 49,99!")
        return TurnoLLM("pede_humano", "Claro, vou te transferir.")


@pytest.mark.unit
def test_price_guard_regenera_quando_llm_corrige() -> None:
    orch = orquestrador()
    orch._llm = LLMViolador(1)
    conv = orch.iniciar()
    orch.processar(conv.id, texto="quero falar com uma pessoa")
    assert conv.estado.value == "HANDOFF"
    assert conv.historico[-1].texto == "Claro, vou te transferir."
    assert not any(e["type"] == "price_guard_violation" for e in conv.eventos)


@pytest.mark.unit
def test_price_guard_fallback_canonico_apos_segunda_violacao() -> None:
    orch = orquestrador()
    orch._llm = LLMViolador(99)
    conv = orch.iniciar()
    orch.processar(conv.id, texto="quero falar com uma pessoa")
    assert conv.estado.value == "HANDOFF"
    assert "R$" not in conv.historico[-1].texto  # fallback canônico, sem preço
    assert any(e["type"] == "price_guard_violation" for e in conv.eventos)


@pytest.mark.unit
def test_midia_por_marcador_de_texto_tambem_pede_texto() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    conv = orch.processar(conv.id, texto="[documento] CNH_frente.pdf")
    assert "escrever" in conv.historico[-1].texto


@pytest.mark.unit
def test_corrige_campo_no_eco() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    orch.processar(conv.id, texto="Onix 2022, 30 anos, CEP 01310-100")
    conv = orch.processar(conv.id, texto="não, a idade está errada, tenho 31 anos")
    assert conv.dados.idade == 31
    assert conv.estado.value == "CONFIRMANDO"


@pytest.mark.unit
def test_comparativo_de_planos_quando_acl_nao_expoe_planos() -> None:
    class AclSemPlanos(StubACL):
        def planos(self):  # type: ignore[override]
            raise httpx.ConnectError("sem planos")

    orch = orquestrador(acl=AclSemPlanos())
    conv = orch.iniciar()
    orch.processar(conv.id, texto="Onix 2022, 30 anos, CEP 01310-100")
    orch.processar(conv.id, texto="é isso")
    conv = orch.processar(conv.id, texto="tá caro")
    assert "comparação" in conv.historico[-1].texto  # intro presente, comparativo vazio


@pytest.mark.unit
class TestFormattingI18n:
    def test_centavos_arredondam_para_cima(self) -> None:
        assert format_brl(0.999) == "R$ 1,00"

    def test_caminho_por_env(self, tmp_path, monkeypatch) -> None:
        arquivo = tmp_path / "pt-BR.json"
        arquivo.write_text("{}", encoding="utf-8")
        monkeypatch.setenv("MESSAGES_PATH", str(arquivo))
        assert _caminho_catalogo() == arquivo
        assert carregar() == {}

    def test_caminho_repo_quando_sem_env_nem_container(self, monkeypatch) -> None:
        monkeypatch.delenv("MESSAGES_PATH", raising=False)
        caminho = _caminho_catalogo()
        assert caminho.name == "pt-BR.json"


@pytest.mark.unit
class TestFakeLLMDireto:
    def test_intents_por_estado(self) -> None:
        llm = FakeLLM()
        assert (
            llm.completar(
                estado="QUALIFICANDO", dados=None, historico=[], mensagem="oi tudo bem"
            ).intent
            == "outro"
        )
        assert (
            llm.completar(
                estado="COTACAO_APRESENTADA", dados=None, historico=[], mensagem="quero"
            ).intent
            == "aceita"
        )
        assert (
            llm.completar(
                estado="QUALIFICANDO",
                dados=None,
                historico=[],
                mensagem="quero cotar meu onix 2022",
            ).intent
            == "informa_dados"
        )
