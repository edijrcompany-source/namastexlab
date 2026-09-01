"""Extração e VALIDAÇÃO com feedback — spec §4.4 + UX fix (loop de idade).

Bug corrigido: regex de idade só casava "N anos" — agora também "tenho N",
"idade N" e N isolado quando os outros campos já foram preenchidos.
Valores REJEITADOS agora geram `rejeicoes` com motivo (o Agente explica o erro).
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

_RE_ANO = re.compile(r"\b(19|20)\d{2}\b")
_RE_CEP = re.compile(r"\b(\d{5})-?(\d{3})\b")
_RE_DATA = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_RE_TELEFONE = re.compile(r"\+55\s?\d{2}\s?9?\d{4}-?\d{4}|\+55\s?\d{2}\s?\d{4}-?\d{4}")
_RE_DIA = re.compile(r"dia\s+(\d{1,2})|\b(\d{1,2})\s+do\s+mes(?:ês)?\b", re.IGNORECASE)

# idade em PRIORIDADE: explícito primeiro, standalone por último (evita falso-positivo)
_RE_IDADE_EXPLICITO = re.compile(r"(\d{1,3})\s*anos", re.IGNORECASE)
_RE_IDADE_TENHO = re.compile(r"tenho\s+(\d{1,3})", re.IGNORECASE)
_RE_IDADE_LABEL = re.compile(r"idade\s*[é:=]?\s*(\d{1,3})", re.IGNORECASE)
_RE_IDADE_STANDALONE = re.compile(r"^\s*(\d{1,3})\s*$")

CAMPOS = ("veiculo_texto", "veiculo_ano", "idade", "cep", "data_inicio")


@dataclass(frozen=True)
class Campos:
    veiculo_texto: str | None = None
    veiculo_ano: int | None = None
    idade: int | None = None
    cep: str | None = None
    data_inicio: str | None = None
    rejeicoes: dict[str, str] = field(default_factory=dict, compare=False)

    def merge(self, outro: Campos) -> Campos:
        """CORRIGE substitui campo a campo (spec §1.3: nunca duplica)."""
        dados = {}
        for campo in CAMPOS:
            novo = getattr(outro, campo)
            dados[campo] = novo if novo is not None else getattr(self, campo)
        # rejeicoes do turno atual (não acumulam entre turnos)
        dados["rejeicoes"] = dict(outro.rejeicoes) if outro.rejeicoes else {}
        return Campos(**dados)

    def faltantes(self) -> tuple[str, ...]:
        obrigatorios = ("veiculo_ano", "idade", "cep")
        return tuple(c for c in obrigatorios if getattr(self, c) is None)

    def completo(self) -> bool:
        return not self.faltantes()

    def inelegivel(self, hoje: dt.date | None = None) -> str | None:
        hoje = hoje or dt.date.today()
        if self.idade is not None and self.idade > 75:
            return "idade"
        if self.veiculo_ano is not None and (hoje.year - self.veiculo_ano) > 20:
            return "veiculo"
        return None


def _extrair_idade(texto: str) -> tuple[int | None, str | None]:
    """Extrai idade com PRIORIDADE: explícito → tenho → label → standalone.

    Standalone (apenas "30") é o ÚLTIMO recurso porque é mais suscetível a
    falsos-positivos. Remove ano/CEP/telefone/datas antes de tentar standalone.
    """
    # 1ª PRIORIDADE: "N anos" (mais confiável)
    for m in _RE_IDADE_EXPLICITO.finditer(texto):
        valor = int(m.group(1))
        if 0 <= valor <= 120:
            return valor, None
        return None, f"idade {valor} está fora do intervalo válido (0-120)"

    # 2ª: "tenho N"
    for m in _RE_IDADE_TENHO.finditer(texto):
        valor = int(m.group(1))
        if 0 <= valor <= 120:
            return valor, None
        return None, f"idade {valor} está fora do intervalo válido (0-120)"

    # 3ª: "idade N" ou "idade: N"
    for m in _RE_IDADE_LABEL.finditer(texto):
        valor = int(m.group(1))
        if 0 <= valor <= 120:
            return valor, None
        return None, f"idade {valor} está fora do intervalo válido (0-120)"

    # 4ª (último recurso): standalone — remove ruído ANTES de aceitar
    # só tenta se a msg INTEIRA é um número (não dentro de outra frase)
    m = _RE_IDADE_STANDALONE.match(texto.strip())
    if m:
        valor = int(m.group(1))
        if 0 <= valor <= 120:
            return valor, None
        return None, f"idade {valor} está fora do intervalo válido (0-120)"

    # dentro de frase com outros campos: remove padrões conhecidos e procura
    # um número isolado que parece idade
    texto_limpo = _RE_ANO.sub(" ", texto)
    texto_limpo = _RE_CEP.sub(" ", texto_limpo)
    texto_limpo = _RE_TELEFONE.sub(" ", texto_limpo)
    texto_limpo = _RE_DIA.sub(" ", texto_limpo)
    texto_limpo = _RE_DATA.sub(" ", texto_limpo)

    # procura número isolado (não parte de palavra) no range 16-100 (idade plausível)
    for m in re.finditer(r"\b(\d{2})\b", texto_limpo):
        valor = int(m.group(1))
        if 16 <= valor <= 100:  # range plausível para idade em contexto
            return valor, None

    return None, None


def _extrair_ano(texto: str, data_inicio: str | None) -> tuple[int | None, str | None]:
    texto_sem_data = _RE_DATA.sub(" ", texto) if data_inicio else texto
    ano: int | None = None
    motivo: str | None = None
    for m in _RE_ANO.finditer(texto_sem_data):
        valor = int(m.group(0))
        if 1950 <= valor <= dt.date.today().year + 1:
            ano = valor
            break
        motivo = f"ano {valor} não é válido (precisa ser entre 1950 e {dt.date.today().year + 1})"
    return ano, motivo


def extrair_campos(texto: str) -> Campos:
    """Extrai + valida + TRACKING de rejeições com motivo."""
    rejeicoes: dict[str, str] = {}

    # data de início
    data_inicio = None
    m = _RE_DATA.search(texto)
    if m:
        try:
            dt.date.fromisoformat(m.group(1))
            data_inicio = m.group(1)
        except ValueError:
            rejeicoes["data_inicio"] = f"data {m.group(1)} é inválida"

    # ano do veículo
    ano, motivo_ano = _extrair_ano(texto, data_inicio)
    if motivo_ano and ano is None:
        rejeicoes["veiculo_ano"] = motivo_ano

    # idade
    idade, motivo_idade = _extrair_idade(texto)
    if motivo_idade and idade is None:
        rejeicoes["idade"] = motivo_idade

    # CEP
    cep = None
    m = _RE_CEP.search(texto)
    if m:
        cep = f"{m.group(1)}-{m.group(2)}"

    # veiculo_texto
    veiculo_texto = None
    if ano is not None:
        m = _RE_ANO.search(texto)
        prefixo = texto[: m.start()].strip(" ,;.")
        palavras = prefixo.split()[-3:] if prefixo else []
        veiculo_texto = " ".join([*palavras, str(ano)]) if palavras else str(ano)

    return Campos(
        veiculo_texto=veiculo_texto,
        veiculo_ano=ano,
        idade=idade,
        cep=cep,
        data_inicio=data_inicio,
        rejeicoes=rejeicoes,
    )
