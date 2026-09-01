"""Extração §4.4 · price-guard §4.3 · format_brl §7-3 · i18n/ULID — puros."""

import re
from datetime import date
from typing import ClassVar

import pytest

from app.domain.ids import ulid
from app.formatting import format_brl
from app.i18n import t
from app.llm.extraction import Campos, extrair_campos
from app.llm.price_guard import contem_valor_monetario, validar_resposta


@pytest.mark.unit
class TestExtracao:
    def test_extrai_tudo_de_uma_fala_solta(self) -> None:
        c = extrair_campos("meu carro é um onix 2022, tenho 30 anos e o cep é 01310-100")
        assert c.veiculo_ano == 2022
        assert c.idade == 30
        assert c.cep == "01310-100"

    def test_cep_sem_hifen_normaliza(self) -> None:
        assert extrair_campos("cep 01310100").cep == "01310-100"

    def test_ano_impossivel_descartado(self) -> None:
        assert extrair_campos("carro de 2030").veiculo_ano is None

    def test_idade_impossivel_descartada(self) -> None:
        assert extrair_campos("tenho 200 anos").idade is None

    def test_data_inicio_valida(self) -> None:
        assert extrair_campos("começar 2026-10-15").data_inicio == "2026-10-15"

    def test_data_invalida_descartada(self) -> None:
        assert extrair_campos("começar 2026-13-45").data_inicio is None

    def test_merge_substitui_campo_a_campo(self) -> None:
        base = Campos(veiculo_texto="Onix 2020", veiculo_ano=2020, idade=30, cep="01310-100")
        novo = Campos(idade=31)
        merged = base.merge(novo)
        assert merged.idade == 31
        assert merged.veiculo_ano == 2020

    def test_faltantes_e_completo(self) -> None:
        assert Campos(veiculo_ano=2022).faltantes() == ("idade", "cep")
        assert Campos(veiculo_ano=1, idade=2, cep="00000-000").completo()

    def test_inelegivel_idade_e_veiculo(self) -> None:
        hoje = date(2026, 9, 1)
        assert Campos(idade=79).inelegivel(hoje) == "idade"
        assert Campos(veiculo_ano=2004).inelegivel(hoje) == "veiculo"
        assert Campos(idade=30, veiculo_ano=2022).inelegivel(hoje) is None

    def test_menor_de_18_deixa_para_api(self) -> None:
        assert Campos(idade=17).inelegivel() is None  # a verdade é a API (H1)


@pytest.mark.unit
class TestPriceGuard:
    COT: ClassVar[list[dict]] = [
        {
            "premio_mensal": 155.87,
            "franquia": 4500,
            "primeiro_pagamento_pro_rata": {"valor_primeiro_pagamento": 88.33},
        }
    ]

    def test_preco_valido_passa(self) -> None:
        assert validar_resposta("Plano Essencial: R$ 155,87/mês", self.COT)

    def test_preco_inventado_bloqueia(self) -> None:
        assert not validar_resposta("Consigo por R$ 99,99!", self.COT)

    def test_sem_cotacao_qualquer_preco_bloqueia(self) -> None:
        assert not validar_resposta("Sai por R$ 129,90", [])

    def test_resposta_sem_preco_passa(self) -> None:
        assert validar_resposta("Sistema instável, volto já", [])

    def test_contem_valor(self) -> None:
        assert contem_valor_monetario("R$ 10,00") and not contem_valor_monetario("caro")


@pytest.mark.unit
class TestFormatBrl:
    def test_padroes(self) -> None:
        assert format_brl(209.9) == "R$ 209,90"
        assert format_brl(155.87) == "R$ 155,87"
        assert format_brl(1234.5) == "R$ 1.234,50"
        assert format_brl(4500) == "R$ 4.500,00"


@pytest.mark.unit
class TestI18nEIds:
    def test_t_interpolola(self) -> None:
        cat = {"a": {"b": "oi {nome}!"}}
        assert t("a.b", cat, nome="Zé") == "oi Zé!"

    def test_t_chave_orfa_retorna_crua(self) -> None:
        assert t("nao.existe", {}) == "nao.existe"

    def test_ulid_26_chars_crockford(self) -> None:
        valor = ulid()
        assert re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{26}", valor)
        assert ulid() != ulid()
