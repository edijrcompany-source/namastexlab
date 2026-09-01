"""Máquina de estados da conversa — implementação LITERAL da tabela spec §1.3.

Puro: sem I/O, sem LLM, sem HTTP. O turn orchestrator (T-05) traduz intents
do LLM em Eventos e executa os Efeitos. As 4 invariantes (§1.3) são garantidas
por construção e testadas como propriedades.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Estado(StrEnum):
    QUALIFICANDO = "QUALIFICANDO"
    CONFIRMANDO = "CONFIRMANDO"
    COTANDO = "COTANDO"
    COTACAO_APRESENTADA = "COTACAO_APRESENTADA"
    OBJECAO = "OBJECAO"
    HANDOFF = "HANDOFF"
    ENCERRADA_GANHO_EM_ANDAMENTO = "ENCERRADA_GANHO_EM_ANDAMENTO"
    ENCERRADA_PERDIDO_INELIGIVEL = "ENCERRADA_PERDIDO_INELIGIVEL"
    ENCERRADA_PERDIDO = "ENCERRADA_PERDIDO"
    ENCERRADA_SEM_RESPOSTA = "ENCERRADA_SEM_RESPOSTA"


ATIVOS: frozenset[Estado] = frozenset(
    {
        Estado.QUALIFICANDO,
        Estado.CONFIRMANDO,
        Estado.COTANDO,
        Estado.COTACAO_APRESENTADA,
        Estado.OBJECAO,
    }
)
TERMINAIS: frozenset[Estado] = frozenset(
    {
        Estado.ENCERRADA_GANHO_EM_ANDAMENTO,
        Estado.ENCERRADA_PERDIDO_INELIGIVEL,
        Estado.ENCERRADA_PERDIDO,
        Estado.ENCERRADA_SEM_RESPOSTA,
    }
)


class Evento(StrEnum):
    # lead (classificados pelo LLM — spec §1.2)
    INFORMA_DADOS_COMPLETO = "INFORMA_DADOS_COMPLETO"
    INFORMA_DADOS_PARCIAL = "INFORMA_DADOS_PARCIAL"
    CORRIGE = "CORRIGE"
    CONFIRMA = "CONFIRMA"
    CONFIRMA_INELIGIVEL_IDADE = "CONFIRMA_INELIGIVEL_IDADE"
    CONFIRMA_INELIGIVEL_VEICULO = "CONFIRMA_INELIGIVEL_VEICULO"
    MIDIA = "MIDIA"
    OBJECAO_PRECO = "OBJECAO_PRECO"
    ACEITA = "ACEITA"
    REJEITA = "REJEITA"
    REJEITA_APOS_RECUSA = "REJEITA_APOS_RECUSA"
    PEDE_HUMANO = "PEDE_HUMANO"
    CONTESTA_RECUSA = "CONTESTA_RECUSA"
    FORA_DE_ESCOPO = "FORA_DE_ESCOPO"
    TIMEOUT_INATIVIDADE = "TIMEOUT_INATIVIDADE"
    # resultados do legado/ACL (spec §1.3)
    QUOTE_OK = "QUOTE_OK"
    QUOTE_RECUSADA_IDADE = "QUOTE_RECUSADA_IDADE"
    QUOTE_RECUSADA_VEICULO = "QUOTE_RECUSADA_VEICULO"
    FALHA_PERSISTENTE = "FALHA_PERSISTENTE"
    CIRCUITO_REABERTO = "CIRCUITO_REABERTO"


class Efeito(StrEnum):
    SAUDAR_PEDIR_DADOS = "SAUDAR_PEDIR_DADOS"
    PEDIR_FALTANTES = "PEDIR_FALTANTES"
    ECO_CONFIRMACAO = "ECO_CONFIRMACAO"
    PEDIR_TEXTO_MIDIA = "PEDIR_TEXTO_MIDIA"
    CHAMAR_COTACAO = "CHAMAR_COTACAO"
    RECUSAR_IDADE_LOCAL = "RECUSAR_IDADE_LOCAL"
    RECUSAR_VEICULO_LOCAL = "RECUSAR_VEICULO_LOCAL"
    APRESENTAR_COTACAO = "APRESENTAR_COTACAO"  # invariável I1: só via QUOTE_OK
    RECUSAR_EMPATICA_IDADE = "RECUSAR_EMPATICA_IDADE"
    RECUSAR_EMPATICA_VEICULO = "RECUSAR_EMPATICA_VEICULO"
    MENSAGEM_FALHA_HONESTA = "MENSAGEM_FALHA_HONESTA"
    AGENDAR_RETENTATIVA = "AGENDAR_RETENTATIVA"
    REBATER_OBJECAO = "REBATER_OBJECAO"
    REDIRECIONAR_ESCOPO = "REDIRECIONAR_ESCOPO"
    MENSAGEM_IDEMPOTENTE_HUMANO = "MENSAGEM_IDEMPOTENTE_HUMANO"
    ENCERRAR_PERDIDO = "ENCERRAR_PERDIDO"
    CAMPO_REJEITADO = "CAMPO_REJEITADO"


@dataclass(frozen=True)
class Transicao:
    estado: Estado
    efeitos: tuple[Efeito, ...]
    handoff_motivo: str | None = None


def criar_conversa() -> Transicao:
    """Linha 1 da tabela: primeira mensagem → saudação + pedido dos 3 dados."""
    return Transicao(Estado.QUALIFICANDO, (Efeito.SAUDAR_PEDIR_DADOS,))


# Tabela §1.3 — (estado, evento) → Transicao. Espelha a spec linha a linha.
_TABELA: dict[tuple[Estado, Evento], Transicao] = {
    # qualificação
    (Estado.QUALIFICANDO, Evento.INFORMA_DADOS_COMPLETO): Transicao(
        Estado.CONFIRMANDO, (Efeito.ECO_CONFIRMACAO,)
    ),
    (Estado.QUALIFICANDO, Evento.INFORMA_DADOS_PARCIAL): Transicao(
        Estado.QUALIFICANDO, (Efeito.PEDIR_FALTANTES,)
    ),
    (Estado.CONFIRMANDO, Evento.CORRIGE): Transicao(Estado.CONFIRMANDO, (Efeito.ECO_CONFIRMACAO,)),
    # cotação
    (Estado.CONFIRMANDO, Evento.CONFIRMA): Transicao(Estado.COTANDO, (Efeito.CHAMAR_COTACAO,)),
    (Estado.CONFIRMANDO, Evento.CONFIRMA_INELIGIVEL_IDADE): Transicao(
        Estado.COTACAO_APRESENTADA, (Efeito.RECUSAR_IDADE_LOCAL,)
    ),
    (Estado.CONFIRMANDO, Evento.CONFIRMA_INELIGIVEL_VEICULO): Transicao(
        Estado.COTACAO_APRESENTADA, (Efeito.RECUSAR_VEICULO_LOCAL,)
    ),
    (Estado.COTANDO, Evento.QUOTE_OK): Transicao(
        Estado.COTACAO_APRESENTADA, (Efeito.APRESENTAR_COTACAO,)
    ),
    (Estado.COTANDO, Evento.QUOTE_RECUSADA_IDADE): Transicao(
        Estado.COTACAO_APRESENTADA, (Efeito.RECUSAR_EMPATICA_IDADE,)
    ),
    (Estado.COTANDO, Evento.QUOTE_RECUSADA_VEICULO): Transicao(
        Estado.COTACAO_APRESENTADA, (Efeito.RECUSAR_EMPATICA_VEICULO,)
    ),
    (Estado.COTANDO, Evento.FALHA_PERSISTENTE): Transicao(
        Estado.COTACAO_APRESENTADA,
        (Efeito.MENSAGEM_FALHA_HONESTA, Efeito.AGENDAR_RETENTATIVA),
    ),
    (Estado.COTANDO, Evento.CIRCUITO_REABERTO): Transicao(
        Estado.HANDOFF, (), handoff_motivo="falha_tecnica"
    ),
    # pós-cotação
    (Estado.COTACAO_APRESENTADA, Evento.OBJECAO_PRECO): Transicao(
        Estado.OBJECAO, (Efeito.REBATER_OBJECAO,)
    ),
    (Estado.OBJECAO, Evento.OBJECAO_PRECO): Transicao(
        Estado.HANDOFF, (), handoff_motivo="objecao_preco"
    ),
    (Estado.OBJECAO, Evento.ACEITA): Transicao(
        Estado.HANDOFF, (), handoff_motivo="aceite_fechamento"
    ),
    (Estado.COTACAO_APRESENTADA, Evento.ACEITA): Transicao(
        Estado.HANDOFF, (), handoff_motivo="aceite_fechamento"
    ),
    (Estado.COTACAO_APRESENTADA, Evento.REJEITA): Transicao(
        Estado.ENCERRADA_PERDIDO, (Efeito.ENCERRAR_PERDIDO,)
    ),
    (Estado.OBJECAO, Evento.REJEITA): Transicao(
        Estado.ENCERRADA_PERDIDO, (Efeito.ENCERRAR_PERDIDO,)
    ),
    (Estado.COTACAO_APRESENTADA, Evento.CONTESTA_RECUSA): Transicao(
        Estado.HANDOFF, (), handoff_motivo="inelegivel_contestado"
    ),
    (Estado.COTACAO_APRESENTADA, Evento.REJEITA_APOS_RECUSA): Transicao(
        Estado.ENCERRADA_PERDIDO_INELIGIVEL, (Efeito.ENCERRAR_PERDIDO,)
    ),
}

# Estados terminais: ENCERRADA_GANHO_EM_ANDAMENTO nunca é alcançado por evento
# do lead (vem do handoff de fechamento) — a tabela não precisa de linhas.

# eventos transversais: PEDE_HUMANO/TIMEOUT/_FORA_DE_ESCOPO/MIDIA (nos ativos)
for _ativo in ATIVOS:
    _TABELA[(_ativo, Evento.PEDE_HUMANO)] = Transicao(
        Estado.HANDOFF, (), handoff_motivo="preferencia_humana"
    )
    _TABELA[(_ativo, Evento.TIMEOUT_INATIVIDADE)] = Transicao(Estado.ENCERRADA_SEM_RESPOSTA, ())
    _TABELA[(_ativo, Evento.MIDIA)] = Transicao(_ativo, (Efeito.PEDIR_TEXTO_MIDIA,))
    _TABELA[(_ativo, Evento.CORRIGE)] = Transicao(
        Estado.CONFIRMANDO,
        (Efeito.ECO_CONFIRMACAO,),  # invariável I3
    )


def transitar(
    estado: Estado,
    evento: Evento,
    *,
    fora_escopo_anterior: bool = False,
) -> Transicao:
    """Aplica a tabela §1.3. Terminais são mudos; HANDOFF é absorvente (I2/I4)."""
    if estado in TERMINAIS:  # invariável I4
        return Transicao(estado, ())
    if estado is Estado.HANDOFF:  # invariável I2 — só Vendedor sai daqui
        return Transicao(Estado.HANDOFF, (Efeito.MENSAGEM_IDEMPOTENTE_HUMANO,))

    if evento is Evento.FORA_DE_ESCOPO:  # transversal com memória (spec §1.3)
        if fora_escopo_anterior:
            return Transicao(Estado.HANDOFF, (), handoff_motivo="fora_escopo")
        return Transicao(estado, (Efeito.REDIRECIONAR_ESCOPO,))

    return _TABELA.get((estado, evento), Transicao(estado, ()))
