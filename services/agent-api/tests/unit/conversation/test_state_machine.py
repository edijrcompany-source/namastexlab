"""Máquina de estados — codifica a TABELA da spec §1.3 + as 4 INVARIANTES.

Cada teste abaixo é uma LINHA da tabela (digitada da spec, não da impl —
divergência entre elas é bug de impl). Invariantes §1.3 em classe própria.
"""

import pytest

from app.conversation.state_machine import (
    ATIVOS,
    TERMINAIS,
    Efeito,
    Estado,
    Evento,
    criar_conversa,
    transitar,
)


@pytest.mark.unit
class TestLinha1Inicializacao:
    def test_criar_conversa_inicia_qualificando_saudando(self) -> None:
        t = criar_conversa()
        assert t.estado is Estado.QUALIFICANDO
        assert t.efeitos == (Efeito.SAUDAR_PEDIR_DADOS,)


@pytest.mark.unit
class TestQualificacao:
    def test_dados_completos_vao_para_confirmacao_com_eco(self) -> None:
        t = transitar(Estado.QUALIFICANDO, Evento.INFORMA_DADOS_COMPLETO)
        assert t.estado is Estado.CONFIRMANDO
        assert Efeito.ECO_CONFIRMACAO in t.efeitos

    def test_dados_parciais_pedem_apenas_faltantes(self) -> None:
        t = transitar(Estado.QUALIFICANDO, Evento.INFORMA_DADOS_PARCIAL)
        assert t.estado is Estado.QUALIFICANDO
        assert t.efeitos == (Efeito.PEDIR_FALTANTES,)

    def test_midia_pede_texto_e_mantem_estado(self) -> None:
        for estado in (Estado.QUALIFICANDO, Estado.CONFIRMANDO):
            t = transitar(estado, Evento.MIDIA)
            assert t.estado is estado
            assert t.efeitos == (Efeito.PEDIR_TEXTO_MIDIA,)

    def test_correcao_substitui_e_volta_a_confirmar(self) -> None:
        t = transitar(Estado.CONFIRMANDO, Evento.CORRIGE)
        assert t.estado is Estado.CONFIRMANDO
        assert Efeito.ECO_CONFIRMACAO in t.efeitos

    def test_confirma_chama_pre_elegibilidade_e_cotacao(self) -> None:
        t = transitar(Estado.CONFIRMANDO, Evento.CONFIRMA)
        assert t.estado is Estado.COTANDO
        assert Efeito.CHAMAR_COTACAO in t.efeitos

    def test_confirma_inelegivel_por_idade_recusa_sem_chamar_legado(self) -> None:
        t = transitar(Estado.CONFIRMANDO, Evento.CONFIRMA_INELIGIVEL_IDADE)
        assert t.estado is Estado.COTACAO_APRESENTADA
        assert t.efeitos == (Efeito.RECUSAR_IDADE_LOCAL,)
        assert Efeito.CHAMAR_COTACAO not in t.efeitos

    def test_confirma_ineligivel_por_veiculo_recusa_sem_chamar_legado(self) -> None:
        t = transitar(Estado.CONFIRMANDO, Evento.CONFIRMA_INELIGIVEL_VEICULO)
        assert t.estado is Estado.COTACAO_APRESENTADA
        assert t.efeitos == (Efeito.RECUSAR_VEICULO_LOCAL,)


@pytest.mark.unit
class TestCotacao:
    def test_quote_ok_apresenta(self) -> None:
        t = transitar(Estado.COTANDO, Evento.QUOTE_OK)
        assert t.estado is Estado.COTACAO_APRESENTADA
        assert t.efeitos == (Efeito.APRESENTAR_COTACAO,)

    @pytest.mark.parametrize(
        ("evento", "efeito"),
        [
            (Evento.QUOTE_RECUSADA_IDADE, Efeito.RECUSAR_EMPATICA_IDADE),
            (Evento.QUOTE_RECUSADA_VEICULO, Efeito.RECUSAR_EMPATICA_VEICULO),
        ],
    )
    def test_recusas_de_negocio(self, evento: Evento, efeito: Efeito) -> None:
        t = transitar(Estado.COTANDO, evento)
        assert t.estado is Estado.COTACAO_APRESENTADA
        assert t.efeitos == (efeito,)

    def test_falha_persistente_msg_honesta_e_retentativa(self) -> None:
        t = transitar(Estado.COTANDO, Evento.FALHA_PERSISTENTE)
        assert t.estado is Estado.COTACAO_APRESENTADA
        assert Efeito.MENSAGEM_FALHA_HONESTA in t.efeitos
        assert Efeito.AGENDAR_RETENTATIVA in t.efeitos

    def test_circuito_reaberto_na_mesma_conversa_vira_handoff_tecnico(self) -> None:
        t = transitar(Estado.COTANDO, Evento.CIRCUITO_REABERTO)
        assert t.estado is Estado.HANDOFF
        assert t.handoff_motivo == "falha_tecnica"


@pytest.mark.unit
class TestPosCotacao:
    def test_primeira_objecao_rebate(self) -> None:
        t = transitar(Estado.COTACAO_APRESENTADA, Evento.OBJECAO_PRECO)
        assert t.estado is Estado.OBJECAO
        assert t.efeitos == (Efeito.REBATER_OBJECAO,)

    def test_segunda_objecao_escala(self) -> None:
        t = transitar(Estado.OBJECAO, Evento.OBJECAO_PRECO)
        assert t.estado is Estado.HANDOFF
        assert t.handoff_motivo == "objecao_preco"

    def test_aceite_pos_objecao_handoff_fechamento(self) -> None:
        t = transitar(Estado.OBJECAO, Evento.ACEITA)
        assert t.estado is Estado.HANDOFF
        assert t.handoff_motivo == "aceite_fechamento"

    def test_aceite_direto_handoff_fechamento(self) -> None:
        t = transitar(Estado.COTACAO_APRESENTADA, Evento.ACEITA)
        assert t.estado is Estado.HANDOFF
        assert t.handoff_motivo == "aceite_fechamento"

    def test_rejeicao_encerra_perdido(self) -> None:
        for estado in (Estado.COTACAO_APRESENTADA, Estado.OBJECAO):
            t = transitar(estado, Evento.REJEITA)
            assert t.estado is Estado.ENCERRADA_PERDIDO
            assert Efeito.ENCERRAR_PERDIDO in t.efeitos

    def test_contestacao_de_recusa_idade_vira_handoff(self) -> None:
        t = transitar(Estado.COTACAO_APRESENTADA, Evento.CONTESTA_RECUSA)
        assert t.estado is Estado.HANDOFF
        assert t.handoff_motivo == "inelegivel_contestado"

    def test_aceitar_recusa_encerra_ineligivel(self) -> None:
        t = transitar(Estado.COTACAO_APRESENTADA, Evento.REJEITA_APOS_RECUSA)
        assert t.estado is Estado.ENCERRADA_PERDIDO_INELIGIVEL


@pytest.mark.unit
class TestTransversais:
    @pytest.mark.parametrize("estado", sorted(ATIVOS, key=str))
    def test_pede_humano_e_imediato_de_qualquer_estado_ativo(self, estado: Estado) -> None:
        t = transitar(estado, Evento.PEDE_HUMANO)
        assert t.estado is Estado.HANDOFF
        assert t.handoff_motivo == "preferencia_humana"

    def test_fora_de_escopo_primeira_vez_redireciona_mantendo(self) -> None:
        t = transitar(Estado.QUALIFICANDO, Evento.FORA_DE_ESCOPO, fora_escopo_anterior=False)
        assert t.estado is Estado.QUALIFICANDO
        assert t.efeitos == (Efeito.REDIRECIONAR_ESCOPO,)

    def test_fora_de_escopo_reincide_vira_handoff(self) -> None:
        t = transitar(Estado.QUALIFICANDO, Evento.FORA_DE_ESCOPO, fora_escopo_anterior=True)
        assert t.estado is Estado.HANDOFF
        assert t.handoff_motivo == "fora_escopo"

    @pytest.mark.parametrize("estado", sorted(ATIVOS, key=str))
    def test_inatividade_24h_encerra_sem_resposta(self, estado: Estado) -> None:
        t = transitar(estado, Evento.TIMEOUT_INATIVIDADE)
        assert t.estado is Estado.ENCERRADA_SEM_RESPOSTA


@pytest.mark.unit
class TestInvariantes:
    """As 4 invariantes da spec §1.3 — propriedades, não linhas."""

    def test_i1_apresentar_cotacao_so_existe_via_quote_ok(self) -> None:
        for estado in Estado:
            for evento in Evento:
                t = transitar(estado, evento)
                if Efeito.APRESENTAR_COTACAO in t.efeitos:
                    assert evento is Evento.QUOTE_OK, f"{estado}/{evento}"
                    assert estado is Estado.COTANDO

    def test_i2_handoff_e_absorvente(self) -> None:
        for evento in Evento:
            t = transitar(Estado.HANDOFF, evento)
            assert t.estado is Estado.HANDOFF

    def test_i3_corrige_sempre_termina_em_confirmacao(self) -> None:
        for estado in ATIVOS:
            t = transitar(estado, Evento.CORRIGE)
            assert t.estado is Estado.CONFIRMANDO

    def test_i4_terminais_sao_mudos(self) -> None:
        for estado in TERMINAIS:
            for evento in Evento:
                t = transitar(estado, evento)
                assert t.estado is estado
                assert t.efeitos == ()
                assert t.handoff_motivo is None
