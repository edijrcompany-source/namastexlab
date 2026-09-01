"""Regressão dos bugs de UX: loop de idade + falta de feedback em rejeição.

Cada teste valida um caso REAL que o usuário reportou:
1. "30" sem "anos" → deve extrair idade (loop eliminado)
2. "tenho 30" → deve extrair idade (loop eliminado)
3. "idade 30" → deve extrair idade (loop eliminado)
4. "200 anos" → deve explicar POR QUE rejeitou (não apenas repetir a pergunta)
5. Feedback contextual: rejeição → motivo + re-pergunta
"""

import pytest

from app.conversation.orchestrator import TurnOrchestrator
from app.domain.extraction import extrair_campos
from app.i18n import carregar
from app.llm.fake import FakeLLM
from tests.unit.conversation.test_orchestrator import StubACL


def orquestrador() -> TurnOrchestrator:
    return TurnOrchestrator(llm=FakeLLM(), acl=StubACL(), catalogo=carregar())


@pytest.mark.unit
class TestLoopDeIdadeCorrigido:
    """Regex ampla: aceita N, tenho N, idade N — não apenas 'N anos'."""

    @pytest.mark.parametrize(
        "texto, esperado",
        [
            ("30", 30),
            ("tenho 30", 30),
            ("idade 30", 30),
            ("30 anos", 30),
            ("Onix 2022, tenho 30, CEP 01310-100", 30),
            ("Onix 2022, 30 anos, CEP 01310-100", 30),
            ("minha idade é 45", 45),
        ],
    )
    def test_extrai_idade_em_varias_formas(self, texto: str, esperado: int) -> None:
        assert extrair_campos(texto).idade == esperado

    def test_fluxo_completo_sem_loop(self) -> None:
        """O usuário informa '30' e o sistema NÃO fica preso pedindo idade."""
        orch = orquestrador()
        conv = orch.iniciar()
        # fornece veículo e CEP primeiro
        orch.processar(conv.id, texto="Onix 2022, CEP 01310-100")
        # agora fornece apenas "30" (sem "anos")
        conv = orch.processar(conv.id, texto="30")
        assert conv.dados.idade == 30
        assert conv.estado.value == "CONFIRMANDO"  # completo → eco, não loop


@pytest.mark.unit
class TestFeedbackDeRejeicao:
    """Quando um valor é rejeitado, o Agente EXPLICA o motivo antes de re-perguntar."""

    def test_idade_200_explica_motivo(self) -> None:
        campos = extrair_campos("200 anos")
        assert campos.idade is None
        assert "idade" in campos.rejeicoes
        assert "0-120" in campos.rejeicoes["idade"]

    def test_ano_2050_explica_motivo(self) -> None:
        campos = extrair_campos("carro de 2050")
        assert campos.veiculo_ano is None
        assert "veiculo_ano" in campos.rejeicoes

    def test_fluxo_200_anos_feedback_no_chat(self) -> None:
        """O usuário informa 200 anos e RECEBE uma explicação, não apenas repetição."""
        orch = orquestrador()
        conv = orch.iniciar()
        conv = orch.processar(conv.id, texto="Onix 2022, CEP 01310-100")
        conv = orch.processar(conv.id, texto="200 anos")
        resposta = conv.historico[-1].texto
        assert "0-120" in resposta or "idade" in resposta.lower()
        # estado NÃO deve ter avançado (idade continua faltando)
        assert conv.estado.value == "QUALIFICANDO"

    def test_rejeicoes_nao_acumulam_entre_turnos(self) -> None:
        """Rejeição do turno anterior NÃO reaparece no turno seguinte."""
        orch = orquestrador()
        conv = orch.iniciar()
        conv = orch.processar(conv.id, texto="200 anos")  # rejeita
        conv = orch.processar(conv.id, texto="Onix 2022, CEP 01310-100")  # ok
        # este turno não tem rejeições novas
        resposta = conv.historico[-1].texto
        assert "0-120" not in resposta  # não repete a rejeição antiga

    def test_fluxo_recuperacao_pos_erro(self) -> None:
        """Rejeita → explica → usuário corrige → continua normalmente."""
        orch = orquestrador()
        conv = orch.iniciar()
        conv = orch.processar(conv.id, texto="Onix 2022, CEP 01310-100")
        conv = orch.processar(conv.id, texto="200 anos")  # rejeita
        assert conv.dados.idade is None
        conv = orch.processar(conv.id, texto="tenho 30")  # corrige
        assert conv.dados.idade == 30
        assert conv.estado.value == "CONFIRMANDO"


@pytest.mark.unit
class TestPedirCampoComHint:
    """As mensagens de pedido agora incluem hints de formato."""

    def test_pedir_idade_tem_hint(self) -> None:
        cat = carregar()
        assert "número" in cat["agent"]["pedir_campo"]["idade"].lower()

    def test_pedir_cep_tem_hint(self) -> None:
        cat = carregar()
        assert "8 dígitos" in cat["agent"]["pedir_campo"]["cep"]

    def test_campo_invalido_no_catalogo(self) -> None:
        cat = carregar()
        assert "campo_invalido" in cat["agent"]
        assert "{campo}" in cat["agent"]["campo_invalido"]
        assert "{motivo}" in cat["agent"]["campo_invalido"]


@pytest.mark.unit
class TestPrioridadeDeExtracao:
    """A extração de idade tem PRIORIDADE: 'N anos' > 'tenho N' > 'idade N' > standalone."""

    def test_label_rejeitado(self) -> None:
        """'idade 200' via label → rejeita com motivo."""
        campos = extrair_campos("idade 200")
        assert campos.idade is None
        assert "0-120" in campos.rejeicoes.get("idade", "")

    def test_tenho_rejeitado(self) -> None:
        """'tenho 200' via 'tenho N' → rejeita com motivo."""
        campos = extrair_campos("tenho 200")
        assert campos.idade is None
        assert "0-120" in campos.rejeicoes.get("idade", "")

    def test_standalone_rejeitado(self) -> None:
        """'500' standalone → rejeita com motivo."""
        campos = extrair_campos("500")
        assert campos.idade is None
        assert "0-120" in campos.rejeicoes.get("idade", "")

    def test_fallback_contextual(self) -> None:
        """Número de 2 dígitos em contexto após remoção de padrões."""
        # após remover ano "2022" e CEP, sobra "e eu 42" → idade contextual
        campos = extrair_campos("Gol 2022, e eu 42, cep 01310-100")
        assert campos.idade == 42

    def test_nao_acha_idade_em_texto_sem_idade(self) -> None:
        """Se não há idade no texto, retorna None sem rejeição."""
        campos = extrair_campos("Gol 2022, cep 01310-100")
        assert campos.idade is None
        assert "idade" not in campos.rejeicoes
