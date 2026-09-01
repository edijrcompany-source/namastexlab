"""Últimas branches para o gate de 100%: terminais mudos, intent 'outro',
rejeição com cotação, fallbacks e efeitos não-textuais."""

import pytest

from app.conversation.state_machine import Efeito, Estado
from app.domain.price_guard import validar_resposta
from tests.unit.conversation.test_orchestrator import orquestrador


@pytest.mark.unit
def test_conversa_encerrada_e_muda() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    for msg in ("Gol 2004, 79 anos, CEP 01310-100", "é isso", "ok, obrigado"):
        orch.processar(conv.id, texto=msg)
    assert conv.estado is Estado.ENCERRADA_PERDIDO_INELIGIVEL
    antes = len(conv.historico)
    conv = orch.processar(conv.id, texto="ainda aí?")  # terminal é mudo (I4)
    assert len(conv.historico) == antes + 1  # só a msg do lead, sem resposta
    assert conv.historico[-1].role == "lead"


@pytest.mark.unit
def test_intent_outro_pede_o_que_falta() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    conv = orch.processar(conv.id, texto="oi, tudo bem?")  # nada extraível
    assert conv.estado is Estado.QUALIFICANDO
    assert "marca" in conv.historico[-1].texto.lower()


@pytest.mark.unit
def test_intent_outro_com_dados_completos_ped_veiculo_default() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    orch.processar(conv.id, texto="Onix 2022, 30 anos, CEP 01310-100")  # completo
    assert conv.estado is Estado.CONFIRMANDO
    conv = orch.processar(conv.id, texto="hm, entendi")  # outro com tudo preenchido
    assert (
        "modelo" in conv.historico[-1].texto.lower()
        or "veículo" in conv.historico[-1].texto.lower()
    )


@pytest.mark.unit
def test_rejeicao_com_cotacao_encerra_perdido() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    for msg in ("Onix 2022, 30 anos, CEP 01310-100", "é isso"):
        orch.processar(conv.id, texto=msg)
    assert conv.cotacoes  # há cotação: REJEITA comum (não pós-recusa)
    conv = orch.processar(conv.id, texto="não vou querer, obrigado")
    assert conv.estado is Estado.ENCERRADA_PERDIDO


@pytest.mark.unit
def test_responder_com_efeitos_vazios_usa_fallback_de_espera() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    orch._responder(conv, ())  # transição sem efeitos textuais
    assert "encaminhei" in conv.historico[-1].texto


@pytest.mark.unit
def test_efeito_nao_textual_nao_gera_texto() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    assert orch._texto_do_efeito(conv, Efeito.CHAMAR_COTACAO) == ""


@pytest.mark.unit
def test_efeito_idempotente_humano_tem_texto() -> None:
    # alcançável apenas por transição direta (o HANDOFF faz early-return)
    orch = orquestrador()
    conv = orch.iniciar()
    assert "encaminhei" in orch._texto_do_efeito(conv, Efeito.MENSAGEM_IDEMPOTENTE_HUMANO)


@pytest.mark.unit
def test_price_guard_cotacao_sem_prorata() -> None:
    cot = [{"premio_mensal": 209.9, "franquia": 3000}]  # sem pro_rata → None/continue
    assert validar_resposta("R$ 209,90/mês, franquia R$ 3.000,00", cot)
    assert not validar_resposta("R$ 100,00", cot)
