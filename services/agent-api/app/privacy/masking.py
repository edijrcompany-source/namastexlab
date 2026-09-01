"""Masking de PII — spec §3 (etapa-3-spec.md), padrões exatos.

Módulo PURO (sem I/O, sem framework — regra C4 §3): string → string.

Ordem de aplicação OBRIGATÓRIA: CPF → e-mail → telefone → placa → CEP.
O telefone precisa vir antes do CEP: o sufixo de um telefone (ex.: "97224-258")
casaria o padrão de CEP e produziria máscara quebrada.
"""

from __future__ import annotations

import re

_CPF = re.compile(r"(\d{3}\.\d{3}\.\d{3})-(\d{2})")
_EMAIL = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_TELEFONE = re.compile(r"(\+55\s?\d{2}\s?)9?\d{4}-?(\d{4})")
_PLACA = re.compile(r"\b([A-Z]{3})-?\d[A-Za-z0-9](\d{2})\b")
_CEP = re.compile(r"(\d{2})\d{3}-?\d{3}")


def _mask_basico(texto: str) -> str:
    """Itens 1-4 da spec §3 — aplicados ANTES de o texto ir ao LLM."""
    texto = _CPF.sub(r"***.***.***-\2", texto)
    texto = _EMAIL.sub(r"\1***@\2", texto)
    texto = _TELEFONE.sub(r"\1*****-\2", texto)
    return _PLACA.sub(r"\1**\2", texto)


def mask_for_llm(texto: str) -> str:
    """Mascara PII antes de enviar ao provedor de LLM (spec §3, itens 1-4).

    O CEP permanece ÍNTEGRO: é necessário à qualificação e à cotação
    (agravo de região) — decisão LGPD da etapa-2 §3.2.
    """
    return _mask_basico(texto)


def mask_for_output(texto: str) -> str:
    """Mascara PII em QUALQUER saída: logs, timeline, exports, evals (NFR-12).

    Inclui o CEP (item 5): mantém apenas os 2 primeiros dígitos — os mesmos
    que o agravo de região usa, suficiente para operação.
    """
    return _CEP.sub(r"\1***-***", _mask_basico(texto))
