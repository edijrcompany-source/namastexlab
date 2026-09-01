"""Price-guard — spec §4.3: zero-tolerance a preço sem origem (NFR-09).

Função PURA: valida os valores monetários da fala do LLM contra as cotações
REais da conversa. Violação ⇒ regenerar 1x ⇒ fallback canônico (orchestrator).
"""

from __future__ import annotations

import re

_RE_MOEDA = re.compile(r"R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?|R\$\s?\d+(?:,\d{2})?")


def _valores_validos(cotacoes: list[dict]) -> set[str]:
    """Todas as representações legítimas de dinheiro da conversa."""
    validos: set[str] = set()
    for cot in cotacoes:
        candidatos = [
            cot.get("premio_mensal"),
            cot.get("franquia"),
            (cot.get("primeiro_pagamento_pro_rata") or {}).get("valor_primeiro_pagamento"),
        ]
        for valor in candidatos:
            if valor is None:
                continue
            centavos = round(float(valor) * 100)
            validos.add(f"{centavos // 100:,}".replace(",", ".") + f",{centavos % 100:02d}")
            validos.add(str(int(valor)) if float(valor).is_integer() else str(valor))
            validos.add(f"{float(valor):.2f}")
            validos.add(f"{float(valor):.2f}".replace(".", ","))
    return validos


def validar_resposta(resposta: str, cotacoes: list[dict]) -> bool:
    """True se TODO R$ citado tem origem nas cotações da conversa.

    Sem cotações na conversa ⇒ qualquer R$ é violação (inviável o Agente citar
    preço sem cotação — guardrail da métrica norte).
    """
    validos = _valores_validos(cotacoes)
    for m in _RE_MOEDA.finditer(resposta):
        bruto = m.group(0)
        numero = bruto.replace("R$", "").strip()
        if numero not in validos:
            return False
    return True


def contem_valor_monetario(resposta: str) -> bool:
    """A fala cita algum R$? (usado pela mensagem de falha honesta §6.6)."""
    return _RE_MOEDA.search(resposta) is not None
