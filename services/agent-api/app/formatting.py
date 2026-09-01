"""Formatos centralizados — etapa-7 §3: UM util por camada (backend).

Exibição pt-BR: R$ 1.234,56. Nenhum outro ponto do código formata moeda.
"""

from __future__ import annotations


def format_brl(valor: float) -> str:
    """209.9 → 'R$ 209,90' · 1234.5 → 'R$ 1.234,50' (pt-BR)."""
    inteiro = int(valor)
    centavos = round((valor - inteiro) * 100)
    if centavos == 100:  # arredondamento para cima (ex.: 0.999)
        inteiro += 1
        centavos = 0
    inteiro_txt = f"{inteiro:,}".replace(",", ".")
    return f"R$ {inteiro_txt},{centavos:02d}"
