"""FakeLLM — motor rule-based DETERMINÍSTICO (ADR-0005): CI offline e modo
local SEM chave de LLM. O sistema inteiro funciona com ele (avaliador testa
sem segredo nenhum); LLM real pluga pela mesma porta (env LLM_PROVIDER).

Keywords espelham o dataset do desafio (padrões reais de fala dos leads).
"""

from __future__ import annotations

import re

from app.domain.extraction import Campos, extrair_campos
from app.domain.ports import TurnoLLM

_HUMANO = re.compile(r"\b(humana?|pessoa|atendente|vendedor)\b", re.IGNORECASE)
_OBJECAO = re.compile(
    r"\b(car[oa]|salgad[oa]|desconto|barat|concorrente|porto|azul|bradesco|sulamerica)\b",
    re.IGNORECASE,
)
_ACEITA = re.compile(
    r"\b(fechado|fechando|pode emitir|vamos nessa|gostei|aceito|quero)\b", re.IGNORECASE
)
_REJEITA = re.compile(
    r"\b(n[aã]o preciso|obrigad[oa]|deixa pra l[aá]|vou ficar|n[aã]o vou)\b",
    re.IGNORECASE,
)
_MEDIA = re.compile(r"^\[(documento|imagem|audio)\]", re.IGNORECASE)
_ESCOPO = re.compile(
    r"\b(seguro de (vida|saude|saúde)|plano de saude|saúde|residencial)\b", re.IGNORECASE
)
_CONTESTA = re.compile(r"\b(certeza|conheco|conheço|consegui)\b", re.IGNORECASE)
_CONFIRMA = re.compile(
    r"^\s*(é isso|e isso|isso|sim|confirmo|correto|pode cotar|cotar|manda|ok)\s*[.!]?\s*$",
    re.IGNORECASE,
)
_CORRIGE = re.compile(r"\b(nao é|não é|errado|nao|não)\b", re.IGNORECASE)

INTENTS = (
    "pede_humano",
    "midia",
    "fora_de_escopo",
    "objecao_preco",
    "aceita",
    "rejeita",
    "contesta",
    "confirma",
    "corrige",
    "informa_dados",
    "outro",
)


class FakeLLM:
    def completar(
        self,
        *,
        estado: str,
        dados: Campos,
        historico: list[str],
        mensagem: str,
        aviso_correcao: bool = False,
    ) -> TurnoLLM:
        texto = mensagem.strip()
        campos = extrair_campos(texto)

        def turno(intent: str, resposta: str = "") -> TurnoLLM:
            return TurnoLLM(intent, resposta, campos)

        if _MEDIA.match(texto):
            return turno("midia")
        if _HUMANO.search(texto):
            return turno("pede_humano")
        if _ESCOPO.search(texto):
            return turno("fora_de_escopo")

        pos_cotacao = estado in ("COTACAO_APRESENTADA", "OBJECAO", "COTANDO")
        if pos_cotacao:
            if _ACEITA.search(texto):
                return turno("aceita")
            if _OBJECAO.search(texto) and not _CONFIRMA.match(texto):
                return turno("objecao_preco")
            if _REJEITA.search(texto):
                return turno("rejeita")
            if _CONTESTA.search(texto):
                return turno("contesta")

        if _CONFIRMA.match(texto):
            return turno("confirma")
        if estado == "CONFIRMANDO" and _CORRIGE.search(texto) and not campos.completo():
            return turno("corrige")

        if campos.faltantes() != ("veiculo_ano", "idade", "cep") or campos.completo():
            return turno("informa_dados")
        return turno(
            "informa_dados"
            if any(getattr(campos, c) is not None for c in ("veiculo_ano", "idade", "cep"))
            else "outro"
        )
