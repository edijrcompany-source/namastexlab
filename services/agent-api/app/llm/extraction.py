"""Extração e VALIDAÇÃO de campos da qualificação — spec §4.4.

Regra DURA, fora do LLM: mesmo com LLM real, os campos passam por aqui.
Campo inválido é DESCARTADO (o fluxo pede de novo — nunca vai ao legado errado).
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

_RE_ANO = re.compile(r"\b(19|20)\d{2}\b")
_RE_IDADE = re.compile(r"(\d{1,3})\s*anos", re.IGNORECASE)
_RE_CEP = re.compile(r"\b(\d{5})-?(\d{3})\b")
_RE_DATA = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

CAMPOS = ("veiculo_texto", "veiculo_ano", "idade", "cep", "data_inicio")


@dataclass(frozen=True)
class Campos:
    veiculo_texto: str | None = None
    veiculo_ano: int | None = None
    idade: int | None = None
    cep: str | None = None
    data_inicio: str | None = None

    def merge(self, outro: Campos) -> Campos:
        """CORRIGE substitui campo a campo (spec §1.3: nunca duplica)."""
        dados = {}
        for campo in CAMPOS:
            novo = getattr(outro, campo)
            dados[campo] = novo if novo is not None else getattr(self, campo)
        return Campos(**dados)

    def faltantes(self) -> tuple[str, ...]:
        """Campos OBRIGATÓRIOS ausentes (data_inicio é opcional — spec §5.1)."""
        obrigatorios = ("veiculo_ano", "idade", "cep")
        return tuple(c for c in obrigatorios if getattr(self, c) is None)

    def completo(self) -> bool:
        return not self.faltantes()

    def inelegivel(self, hoje: dt.date | None = None) -> str | None:
        """Pré-elegibilidade de cortesia (US-07/H1): retorna o motivo ou None.

        A verdade SEMPRE é a resposta da API — isto evita queimar chamadas óbvias.
        """
        hoje = hoje or dt.date.today()
        # pré-check é CORTESIA (H1): só os casos-limite óbvios da spec §6.5
        # (idade 76+ · veículo >20 anos). Idade <18 fica para a API decidir.
        if self.idade is not None and self.idade > 75:
            return "idade"
        if self.veiculo_ano is not None and (hoje.year - self.veiculo_ano) > 20:
            return "veiculo"
        return None


def extrair_campos(texto: str) -> Campos:
    """Extrai + valida. Idade 0-120 · ano 1950..ano_atual+1 · CEP normalizado."""
    ano = None
    for m in _RE_ANO.finditer(texto):
        valor = int(m.group(0))
        if 1950 <= valor <= dt.date.today().year + 1:
            ano = valor
            break

    idade = None
    m = _RE_IDADE.search(texto)
    if m and 0 <= int(m.group(1)) <= 120:
        idade = int(m.group(1))

    cep = None
    m = _RE_CEP.search(texto)
    if m:
        cep = f"{m.group(1)}-{m.group(2)}"

    data_inicio = None
    m = _RE_DATA.search(texto)
    if m:
        try:
            dt.date.fromisoformat(m.group(1))
            data_inicio = m.group(1)
        except ValueError:
            data_inicio = None  # inválida → descartada (spec §4.4)

    veiculo_texto = None
    if ano is not None:
        m = _RE_ANO.search(texto)
        prefixo = texto[: m.start()].strip(" ,;.")
        palavras = prefixo.split()[-3:] if prefixo else []
        veiculo_texto = " ".join([*palavras, str(ano)]) if palavras else str(ano)

    return Campos(
        veiculo_texto=veiculo_texto, veiculo_ano=ano, idade=idade, cep=cep, data_inicio=data_inicio
    )
