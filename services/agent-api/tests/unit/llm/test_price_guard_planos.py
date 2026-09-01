"""Price-guard com /planos como fonte legítima (spec §6.8) — T-09/T-10."""

import pytest

from app.domain.price_guard import validar_resposta

PLANOS = [
    {"nome": "Essencial", "base_mensal": 119.90, "franquia": 4500.0},
    {"nome": "Completo", "base_mensal": 209.90, "franquia": 3000.0},
]


@pytest.mark.unit
class TestGuardComPlanos:
    def test_franquia_de_plano_nao_cotado_e_legitima(self) -> None:
        # comparativo de objeção (§6.8): franquia do Completo vem de /planos
        assert validar_resposta("Completo: franquia R$ 3.000,00", [], PLANOS)

    def test_base_mensal_de_plano_e_legitima(self) -> None:
        assert validar_resposta("a partir de R$ 119,90", [], PLANOS)

    def test_valor_fora_de_planos_e_cotacoes_bloqueia(self) -> None:
        assert not validar_resposta("por R$ 49,99", [], PLANOS)

    def test_sem_planos_e_sem_cotacoes_qualquer_preco_bloqueia(self) -> None:
        assert not validar_resposta("R$ 3.000,00", [], [])

    def test_cotacao_continua_valida_com_planos_presentes(self) -> None:
        cot = [{"premio_mensal": 155.87, "franquia": 4500}]
        assert validar_resposta("R$ 155,87/mês", cot, PLANOS)

    def test_plano_sem_franquia_nao_quebra(self) -> None:
        assert validar_resposta("sem preço algum", [], [{"nome": "X"}])
