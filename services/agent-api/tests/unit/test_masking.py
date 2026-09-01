"""Masking de PII — codifica a spec §3 (etapa-3-spec.md), tabela exata.

Regras de ouro testadas aqui:
- padrões e substituições EXATOS da spec §3;
- ordem de aplicação (telefone ANTES de CEP — evita captura parcial);
- mask_for_llm = itens 1-4 (CEP íntegro: necessário ao negócio);
- mask_for_output = itens 1-5 (CEP mascarado em logs/timeline/saídas);
- idempotência (mascarar 2x = mesmo resultado — NFR-12 depende disso).
"""
import pytest

from app.privacy.masking import mask_for_llm, mask_for_output


@pytest.mark.unit
class TestCpf:
    def test_mascara_mantendo_dois_ultimos_digitos(self) -> None:
        assert mask_for_output("cpf 389.083.863-43") == "cpf ***.***.***-43"

    def test_cpf_no_meio_de_fala_real_do_dataset(self) -> None:
        texto = "Cep 07624-954, cpf 662.011.621-35, tenho 30 anos"
        assert mask_for_output(texto) == "Cep 07***-***, cpf ***.***.***-35, tenho 30 anos"


@pytest.mark.unit
class TestEmail:
    def test_mascara_mantendo_inicial_e_dominio(self) -> None:
        assert mask_for_output("ursula.souza@gmail.com") == "u***@gmail.com"

    def test_email_com_underscore_e_numeros(self) -> None:
        assert mask_for_llm("joao_pereira12@bol.com.br") == "j***@bol.com.br"


@pytest.mark.unit
class TestTelefone:
    def test_celular_com_nove(self) -> None:
        assert mask_for_output("+55 21 97224-2584") == "+55 21 *****-2584"

    def test_fixo_sem_nove(self) -> None:
        assert mask_for_output("+55 11 3722-2584") == "+55 11 *****-2584"

    def test_sem_espacos(self) -> None:
        assert mask_for_output("+5521972242584") == "+5521*****-2584"


@pytest.mark.unit
class TestPlaca:
    def test_formato_mercosul(self) -> None:
        assert mask_for_output("a placa é GGE4X30 se precisar") == "a placa é GGE**30 se precisar"

    def test_formato_antigo(self) -> None:
        assert mask_for_output("ABC1234") == "ABC**34"


@pytest.mark.unit
class TestCep:
    def test_mascarado_na_saida(self) -> None:
        assert mask_for_output("CEP 01310-100") == "CEP 01***-***"

    def test_cep_sem_hifen(self) -> None:
        assert mask_for_output("01310100") == "01***-***"

    def test_cep_inTEGRO_antes_do_llm(self) -> None:
        # spec §3: CEP vai íntegro ao LLM (necessário à qualificação/cotação)
        assert mask_for_llm("CEP 01310-100 e cpf 389.083.863-43") == "CEP 01310-100 e cpf ***.***.***-43"


@pytest.mark.unit
class TestOrdemEComposicao:
    def test_telefone_nao_e_parcialmente_mascarado_como_cep(self) -> None:
        # sufixo "97224-258" casaria o regex de CEP se aplicado antes
        texto = "meu whats é +55 21 97224-2584, chama lá"
        assert mask_for_output(texto) == "meu whats é +55 21 *****-2584, chama lá"

    def test_texto_sem_pii_permance_intacto(self) -> None:
        texto = "Oi, queria fazer um seguro pro meu carro"
        assert mask_for_output(texto) == texto

    def test_pii_multipla_na_mesma_mensagem(self) -> None:
        texto = "meu email é ursula.souza@gmail.com e o whats é esse mesmo +55 21 97224-2584"
        assert mask_for_output(texto) == "meu email é u***@gmail.com e o whats é esse mesmo +55 21 *****-2584"


@pytest.mark.unit
class TestIdempotencia:
    @pytest.mark.parametrize(
        "texto",
        [
            "cpf 389.083.863-43",
            "ursula.souza@gmail.com",
            "+55 21 97224-2584",
            "placa GGE4X30 cep 01310-100",
            "nada sensível aqui",
        ],
    )
    def test_mascarar_duas_vezes_nao_muda(self, texto: str) -> None:
        uma = mask_for_output(texto)
        assert mask_for_output(uma) == uma

    def test_llm_tambem_idempotente(self) -> None:
        texto = "cpf 389.083.863-43 cep 01310-100"
        uma = mask_for_llm(texto)
        assert mask_for_llm(uma) == uma
