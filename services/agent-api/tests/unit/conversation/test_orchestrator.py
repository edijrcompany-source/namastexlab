"""C1-C6 (spec §11) de verdade: FakeLLM + StubACL — offline, determinístico.

Alvo: provar o fluxo de ponta a ponta do Agente pelas regras da spec antes da
API existir (T-07 só expõe o que aqui já funciona).
"""

import pytest

from app.conversation.orchestrator import TurnOrchestrator
from app.domain.ports import QuoteRefused, TransientQuoteError
from app.i18n import carregar
from app.llm.fake import FakeLLM
from app.quoting.breaker import CircuitBreaker

COTACAO_OK = {
    "plano_id": "essencial",
    "plano_nome": "Essencial",
    "premio_mensal": 155.87,
    "franquia": 4500.0,
    "coberturas": ["colisao", "roubo", "furto"],
    "carencia": {"coberturas": ["roubo", "furto"], "dias": 30},
    "primeiro_pagamento_pro_rata": {
        "dias_no_mes": 30,
        "dias_cobrados": 17,
        "valor_primeiro_pagamento": 88.33,
    },
    "moeda": "BRL",
}
PLANOS = [
    {
        "id": "essencial",
        "nome": "Essencial",
        "base_mensal": 119.90,
        "franquia": 4500.0,
        "coberturas": ["colisao", "roubo", "furto"],
    },
    {
        "id": "completo",
        "nome": "Completo",
        "base_mensal": 209.90,
        "franquia": 3000.0,
        "coberturas": ["colisao", "roubo", "furto", "terceiros", "vidros"],
    },
    {
        "id": "premium",
        "nome": "Premium",
        "base_mensal": 339.90,
        "franquia": 1500.0,
        "coberturas": [
            "colisao",
            "roubo",
            "furto",
            "terceiros",
            "vidros",
            "carro_reserva",
            "assistencia_24h",
        ],
    },
]


class StubACL:
    """ACL falsa: devolve a cotação fixture na primeira chamada."""

    def __init__(self, cotacao=COTACAO_OK, recusa=None, transiente=False) -> None:
        self.cotacao = cotacao
        self.recusa = recusa
        self.transiente = transiente
        self.breaker = CircuitBreaker(clock=lambda: 0.0)

    def cotar(self, payload):
        if self.recusa:
            raise QuoteRefused(self.recusa)
        if self.transiente:
            raise TransientQuoteError("falha_apos_3_tentativas", attempts=3)
        return dict(self.cotacao)

    def planos(self):
        return [dict(p) for p in PLANOS]


def orquestrador(acl=None) -> TurnOrchestrator:
    return TurnOrchestrator(
        llm=FakeLLM(), acl=acl if acl is not None else StubACL(), catalogo=carregar()
    )


def _turno(orch, conversa, texto):
    return orch.processar(conversa.id, texto=texto)


@pytest.mark.unit
def test_c1_caminho_feliz_ate_handoff_de_fechamento() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    assert "três coisas" in conv.historico[-1].texto or "veículo" in conv.historico[-1].texto

    _turno(orch, conv, "Onix 2022, tenho 30 anos e o CEP é 01310-100")
    assert conv.estado.value == "CONFIRMANDO"
    assert "é isso?" in conv.historico[-1].texto.lower()

    _turno(orch, conv, "é isso")
    assert conv.estado.value == "COTACAO_APRESENTADA"
    resposta = conv.historico[-1].texto
    assert "R$ 155,87" in resposta  # byte a byte da API (NFR-09)
    assert "R$ 4.500,00" in resposta  # franquia formatada
    assert "30 dias" in resposta  # carência obrigatória (§6.4)
    assert "R$ 88,33" in resposta  # pró-rata (§6.4)
    assert any(e["type"] == "quote_succeeded" for e in conv.eventos)

    _turno(orch, conv, "fechado!")
    assert conv.estado.value == "HANDOFF"
    assert conv.handoff["motivo"] == "aceite_fechamento"
    assert any(e["type"] == "handoff_requested" for e in conv.eventos)


@pytest.mark.unit
def test_c2_objecao_rebatida_e_segunda_escala() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    _turno(orch, conv, "Onix 2022, 30 anos, CEP 01310-100")
    _turno(orch, conv, "é isso")
    _turno(orch, conv, "tá caro, vi mais barato na Porto")
    assert conv.estado.value == "OBJECAO"
    assert "franquia" in conv.historico[-1].texto  # comparativo real, sem desconto
    _turno(orch, conv, "ainda acho caro, consegue desconto?")
    assert conv.estado.value == "HANDOFF"
    assert conv.handoff["motivo"] == "objecao_preco"


@pytest.mark.unit
def test_c3_recusa_idade_local_sem_chamar_o_legado() -> None:
    acl = StubACL()
    orch = orquestrador(acl)
    conv = orch.iniciar()
    _turno(orch, conv, "Gol 2004, tenho 79 anos, CEP 01310-100")
    _turno(orch, conv, "é isso")
    assert conv.estado.value == "COTACAO_APRESENTADA"
    assert "75 anos" in conv.historico[-1].texto
    assert not any(e["type"] == "quote_requested" for e in conv.eventos)  # pré-check
    _turno(orch, conv, "ok, obrigado")
    assert conv.estado.value == "ENCERRADA_PERDIDO_INELIGIVEL"


@pytest.mark.unit
def test_c4_recusa_contestada_vira_handoff() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    _turno(orch, conv, "Gol 2004, tenho 79 anos, CEP 01310-100")
    _turno(orch, conv, "é isso")
    _turno(orch, conv, "tenho certeza? conheço gente que conseguiu")
    assert conv.estado.value == "HANDOFF"
    assert conv.handoff["motivo"] == "inelegivel_contestado"


@pytest.mark.unit
def test_c5_falha_persistente_mensagem_honesta_sem_preco() -> None:
    orch = orquestrador(acl=StubACL(transiente=True))
    conv = orch.iniciar()
    _turno(orch, conv, "Onix 2022, 30 anos, CEP 01310-100")
    _turno(orch, conv, "é isso")
    resposta = conv.historico[-1].texto
    assert "R$" not in resposta  # SEM preço inventado (§6.6)
    assert "instável" in resposta or "instavel" in resposta
    assert conv.retry_pending is True
    assert any(e["type"] == "retry_scheduled" for e in conv.eventos)


@pytest.mark.unit
def test_c6_pedido_de_humano_e_imediato() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    _turno(orch, conv, "quero falar com uma pessoa")
    assert conv.estado.value == "HANDOFF"
    assert conv.handoff["motivo"] == "preferencia_humana"
    # idempotente: outra mensagem não sai do HANDOFF
    _turno(orch, conv, "oi?")
    assert conv.estado.value == "HANDOFF"
    assert "encaminhei" in conv.historico[-1].texto


@pytest.mark.unit
def test_pii_do_lead_chega_mascarada_ao_historico() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    _turno(orch, conv, "Onix 2022, 30 anos, CEP 01310-100, cpf 389.083.863-43")
    msg = next(m for m in conv.historico if m.role == "lead")
    assert "389.083.863-43" not in msg.texto
    assert "***.***.***-43" in msg.texto


@pytest.mark.unit
def test_midia_pede_texto() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    conv = orch.processar(conv.id, midia=("document", "[documento] CNH_frente.pdf"))
    assert "escrever" in conv.historico[-1].texto


@pytest.mark.unit
def test_fora_de_escopo_redireciona_depois_escala() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    _turno(orch, conv, "quero contratar seguro de vida")
    assert conv.estado.value == "QUALIFICANDO"  # 1ª: redirect
    _turno(orch, conv, "seguro de vida mesmo")
    assert conv.estado.value == "HANDOFF"
    assert conv.handoff["motivo"] == "fora_escopo"


@pytest.mark.unit
def test_store_in_memory_persiste_e_lista_handoffs() -> None:
    orch = orquestrador()
    conv = orch.iniciar()
    _turno(orch, conv, "quero falar com uma pessoa")
    pendentes = orch.store.handoffs_pendentes()
    assert [c.id for c in pendentes] == [conv.id]
    assert orch.store.obter(conv.id) is conv
    assert orch.store.apagar(conv.id) is True
    assert orch.store.obter(conv.id) is None
