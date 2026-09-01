"""Testes do pipeline Bronze→Silver (spec §7 / US-13).

Transformações puras + smoke do pipeline com parquet fixture.
A fonte de masking é app.privacy.masking (1 fonte por fato — nunca duplicar).
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

from build_silver import (  # noqa: E402
    _PADRAO_CEP_CRU,
    _PADRAO_CPF_CRU,
    _PADRAO_EMAIL_CRU,
    _PADRAO_PLACA_CRU,
    _PADRAO_TELEFONE_CRU,
    mascarar_linha,
    normalizar_veiculo,
    transformar,
)


@pytest.mark.unit
class TestNormalizarVeiculo:
    def test_marca_modelo_ano_do_dicionario_fechado(self) -> None:
        marca, modelo, ano = normalizar_veiculo("Chevrolet Onix 2022")
        assert (marca, modelo, ano) == ("Chevrolet", "Onix", 2022)

    def test_marca_descoberta_pelo_modelo(self) -> None:
        # fala real do dataset: "e um Sandero 2022" (sem citar a marca)
        marca, modelo, ano = normalizar_veiculo("e um Sandero 2022")
        assert (marca, modelo, ano) == ("Renault", "Sandero", 2022)

    def test_veiculo_fora_do_dicionario_so_ano(self) -> None:
        marca, modelo, ano = normalizar_veiculo("BMW 320i 2020")
        assert (marca, modelo, ano) == (None, None, 2020)  # texto original é preservado

    def test_ano_ausente(self) -> None:
        assert normalizar_veiculo("Gol")[2] is None

    def test_case_insensitive(self) -> None:
        assert normalizar_veiculo("corolla cross 2015")[0] == "Toyota"


@pytest.mark.unit
class TestMascararLinha:
    def test_pii_da_fala_real_do_dataset(self) -> None:
        body, sender = mascarar_linha(
            "Cep 07624-954, cpf 662.011.621-35, tenho 30 anos", "Bruno Pereira"
        )
        assert "662.011.621-35" not in body
        assert "***.***.***-35" in body
        assert "07624-954" not in body
        assert "07***-***" in body  # CEP também na Silver (saída, não LLM)
        assert sender == "B***"

    def test_email_telefone_placa(self) -> None:
        body, _ = mascarar_linha(
            "ursula.souza@gmail.com +55 21 97224-2584 placa GGE4X30", "U"
        )
        assert "u***@gmail.com" in body and "+55 21 *****-2584" in body and "GGE**30" in body


@pytest.mark.unit
class TestTransformar:
    def _fixture(self, tmp_path: Path) -> Path:
        df = pd.DataFrame(
            [
                {
                    "conversation_id": "conv_00001",
                    "message_index": 0,
                    "timestamp": "2026-01-01T10:00:00",
                    "sender_role": "lead",
                    "sender_name": "Bruno Pereira",
                    "message_type": "text",
                    "message_body": "oi, cpf 662.011.621-35",
                    "channel": "whatsapp",
                    "conversation_outcome": "ganho",
                    "lead_idade_informada": 30,
                    "veiculo_texto": "Renault Sandero 2022",
                },
                {
                    "conversation_id": "conv_00001",
                    "message_index": 1,
                    "sender_role": "vendedor",
                    "sender_name": "Camila (Vendas)",
                    "message_type": "text",
                    "message_body": "Ola Bruno!",
                    "channel": "whatsapp",
                    "conversation_outcome": "ganho",
                    "lead_idade_informada": 30,
                    "veiculo_texto": "Renault Sandero 2022",
                },
            ]
        )
        caminho = tmp_path / "bronze.parquet"
        df.to_parquet(caminho, index=False)
        return caminho

    def test_ordenacao_por_message_index_nunca_timestamp(self, tmp_path: Path) -> None:
        # timestamps FORA de ordem no fixture: Silver deve ordenar por message_index
        bronze = self._fixture(tmp_path)
        silver, relatorio = transformar(bronze)
        bodies = silver[silver.sender_role == "lead"].message_body.tolist()
        assert bodies[0].startswith("oi,")  # index 0 veio antes apesar do timestamp

    def test_colunas_de_veiculo_normalizadas(self, tmp_path: Path) -> None:
        silver, _ = transformar(self._fixture(tmp_path))
        assert set(["marca", "modelo", "ano"]).issubset(silver.columns)
        linha = silver.iloc[0]
        assert linha["marca"] == "Renault" and linha["modelo"] == "Sandero" and linha["ano"] == 2022

    def test_relatorio_100_mascarado(self, tmp_path: Path) -> None:
        _, relatorio = transformar(self._fixture(tmp_path))
        assert relatorio["conversas"] == 1
        assert relatorio["pct_pii_mascarada"] == 100.0  # gate US-13/NFR-12
        assert relatorio["pct_veiculo_normalizado"] == 100.0

    def test_nenhum_padrao_cru_sobrevive(self, tmp_path: Path) -> None:
        silver, _ = transformar(self._fixture(tmp_path))
        todo_texto = " ".join(silver.message_body.tolist() + silver.sender_name.tolist())
        for padrao in (_PADRAO_CPF_CRU, _PADRAO_EMAIL_CRU, _PADRAO_TELEFONE_CRU, _PADRAO_PLACA_CRU, _PADRAO_CEP_CRU):
            assert not padrao.search(todo_texto), padrao.pattern
