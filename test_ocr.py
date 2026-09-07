"""Testes para o modulo ocr_cadastro."""

import pytest
from ocr_cadastro import (
    _extrair_com_regex,
    _extrair_registro,
    _extrair_contrato,
    mesclar_campos,
    campos_para_sistema,
    _converte_data,
)


# --- Textos de teste simulando documentos reais ---

TEXTO_REGISTRO = """Ficha de Registro de Empregado
Empregado Beneficiários
MICHEL LUIS ALBUQUERQUE NUNES
Residência
Travessa BREVES, 766, JURUNAS, BELEM, PA, - CEP: 66025-662
Matrícula eSocial Nº
16460 16460
Cédula de Identidade Data de emissão Órgão
4747819
CTPS Série Data de expedição da CTPS UF CTPS CPF
0067258 1230 02/09/2022 PA 006.725.812-30
Doc. militar Categoria Cor Sexo Grau de instrução
280154720658 RA Parda Masculino Ensino Médio Completo
Deficiência Telefone Residencial Telefone Celular
Não 91-980781242
Cargo Função C.B.O.
AUXILIAR DE SERVIÇOS GERAIS AUXILIAR DE SERVIÇOS GERAIS 514320
Data de Admissão Salário Por Horário de Trabalho
08/09/2026 R$ 1.694,46 Mês das 14:00 as 22:20
FGTS 08/09/2026
PROGRAMA DE INTEGRAÇÃO SOCIAL - PIS
000.00000.00-0
Estado civil nacionalidade
Solteiro
Filiação
Pai
MAURO LUIS NUNES
FILIAÇÃO
Mãe
SILVIA MARA CALDAS DE ALBUQUERQUE
Cédula de Identidade
Data de nascimento 26/07/1990
Título Eleitoral
057615141341
CNPJ: 23.585.374/0001-11"""

TEXTO_CONTRATO = """CONTRATO DE EXPERIÊNCIA
Pelo presente instrumento particular, de um lado EMPRESA LTDA,
CNPJ: 23.585.374/0001-11, e de outro lado o Sr(a). MICHEL LUIS ALBUQUERQUE NUNES, domiciliado
CTPS Nº: 0067258 série 1230
Exercerá a função de AUXILIAR DE SERVIÇOS GERAIS e mais as
local de trabalho situa-se na Avenida CONSELHEIRO FURTADO, 76, BATISTA CAMPOS, BELEM-PA, podendo
remuneração de: R$ 1.694,46
prazo deste contrato é de 45 dias corridos, com início em: 08/09/2026 e término em: 22/10/2026
horário das 14:00 as 22:20"""


class TestConverteData:
    def test_dd_mm_yyyy(self):
        assert _converte_data("08/09/2026") == "2026-09-08"

    def test_dd_mm_yyyy_com_ponto(self):
        assert _converte_data("08.09.2026") == "2026-09-08"

    def test_ja_iso(self):
        assert _converte_data("2026-09-08") == "2026-09-08"


class TestExtrairRegistro:
    def setup_method(self):
        self.campos = _extrair_registro(TEXTO_REGISTRO)

    def test_nome(self):
        assert self.campos["nome"] == "MICHEL LUIS ALBUQUERQUE NUNES"

    def test_matricula(self):
        assert self.campos["matricula"] == "16460"

    def test_cpf(self):
        assert self.campos["cpf"] == "006.725.812-30"

    def test_rg(self):
        assert self.campos["rg"] == "4747819"

    def test_data_nascimento(self):
        assert self.campos["data_nascimento"] == "1990-07-26"

    def test_estado_civil(self):
        assert self.campos["estado_civil"] == "Solteiro"

    def test_nome_pai(self):
        assert self.campos["nome_pai"] == "MAURO LUIS NUNES"

    def test_nome_mae(self):
        assert self.campos["nome_mae"] == "SILVIA MARA CALDAS DE ALBUQUERQUE"

    def test_ctps_numero(self):
        assert self.campos["ctps_numero"] == "0067258"

    def test_ctps_serie(self):
        assert self.campos["ctps_serie"] == "1230"

    def test_cargo(self):
        assert "AUXILIAR" in self.campos.get("cargo", "")
        # Nao deve estar duplicado
        cargo = self.campos.get("cargo", "")
        metade = len(cargo) // 2
        assert cargo[:metade].strip().upper() != cargo[metade:].strip().upper() or len(cargo.split()) <= 5

    def test_cbo(self):
        assert self.campos.get("cbo") == "514320"

    def test_admissao(self):
        assert self.campos["admissao"] == "2026-09-08"

    def test_salario(self):
        assert self.campos["salario"] == "1.694,46"

    def test_sexo(self):
        assert self.campos.get("sexo") == "Masculino"

    def test_cor_raca(self):
        assert self.campos.get("cor_raca") == "Parda"

    def test_grau_instrucao(self):
        assert self.campos.get("grau_instrucao") == "Ensino Médio Completo"

    def test_telefone(self):
        assert self.campos.get("telefone") == "91980781242"

    def test_cnpj_empregador(self):
        assert self.campos.get("cnpj_empregador") == "23.585.374/0001-11"

    def test_pis(self):
        assert self.campos.get("pis") == "000.00000.00-0"

    def test_deficiencia(self):
        assert self.campos.get("deficiencia") == "Não"


class TestExtrairContrato:
    def setup_method(self):
        self.campos = _extrair_contrato(TEXTO_CONTRATO)

    def test_ctps_numero(self):
        assert self.campos["ctps_numero"] == "0067258"

    def test_ctps_serie(self):
        assert self.campos["ctps_serie"] == "1230"

    def test_loja(self):
        assert "CONSELHEIRO FURTADO" in self.campos.get("loja", "")

    def test_salario(self):
        assert self.campos["salario"] == "1.694,46"

    def test_experiencia_dias(self):
        assert self.campos["experiencia_dias"] == 45

    def test_contrato_inicio(self):
        assert self.campos["contrato_inicio"] == "2026-09-08"

    def test_contrato_fim(self):
        assert self.campos["contrato_fim"] == "2026-10-22"

    def test_admissao(self):
        assert self.campos["admissao"] == "2026-09-08"

    def test_cnpj(self):
        assert self.campos.get("cnpj_empregador") == "23.585.374/0001-11"


class TestMesclarCampos:
    def test_mescla_campos(self):
        reg = {"nome": "JOAO", "cpf": "123.456.789-00", "cbo": "514320"}
        cont = {"loja": "LOJA 1", "cargo": "AUXILIAR", "experiencia_dias": 45}
        mesclado = mesclar_campos(reg, cont)
        # Dados pessoais do registro
        assert mesclado["nome"] == "JOAO"
        assert mesclado["cpf"] == "123.456.789-00"
        # Campos do contrato
        assert mesclado["loja"] == "LOJA 1"
        assert mesclado["cargo"] == "AUXILIAR"
        assert mesclado["experiencia_dias"] == 45
        # CBO permanece do registro
        assert mesclado["cbo"] == "514320"

    def test_contrato_nao_sobrescreve_dados_pessoais(self):
        reg = {"nome": "JOAO SILVA", "cpf": "111.111.111-11"}
        cont = {"nome": "NOME ERRADO"}
        mesclado = mesclar_campos(reg, cont)
        assert mesclado["nome"] == "JOAO SILVA"

    def test_contrato_sobrescreve_salario(self):
        reg = {"salario": "1.000,00"}
        cont = {"salario": "1.500,00"}
        mesclado = mesclar_campos(reg, cont)
        assert mesclado["salario"] == "1.500,00"


class TestCamposParaSistema:
    def test_campos_basicos(self):
        campos = {
            "matricula": "123",
            "nome": "JOAO SILVA",
            "rg": "12345",
            "cpf": "123.456.789-00",
            "telefone": "91999999999",
            "cargo": "AUXILIAR",
            "loja": "LOJA 1",
            "admissao": "2026-09-08",
            "experiencia_dias": 45,
        }
        sistema = campos_para_sistema(campos)
        assert sistema["matricula"] == "123"
        assert sistema["nome"] == "JOAO SILVA"
        assert sistema["situacao"] == "Ativo"
        assert sistema["experiencia_dias"] == 45

    def test_telefone_formatado(self):
        campos = {"telefone": "91999999999", "nome": "X"}
        sistema = campos_para_sistema(campos)
        assert "(91)" in sistema["telefone"]

    def test_cpf_formatado(self):
        campos = {"cpf": "12345678900", "nome": "X"}
        sistema = campos_para_sistema(campos)
        assert sistema["cpf"] == "123.456.789-00"

    def test_observacao_com_extras(self):
        campos = {
            "nome": "X",
            "salario": "1.500,00",
            "cbo": "514320",
            "sexo": "Masculino",
        }
        sistema = campos_para_sistema(campos)
        assert "Salario" in sistema.get("observacao", "")
        assert "CBO" in sistema.get("observacao", "")
        assert "Sexo" in sistema.get("observacao", "")


class TestIntegracaoOCR:
    """Teste de integracao com os PDFs reais."""

    def test_registro_completo(self):
        """Testa extracao do PDF real da Ficha de Registro."""
        try:
            from ocr_cadastro import ler_documento
            with open("/nfs/105093785/uploads/Ficha_Registro_de_Empregado.pdf", "rb") as f:
                texto = ler_documento(f)
        except FileNotFoundError:
            pytest.skip("PDF de teste nao disponivel")

        campos = _extrair_com_regex(texto, "registro")
        assert campos["nome"] == "MICHEL LUIS ALBUQUERQUE NUNES"
        assert campos["matricula"] == "16460"
        assert campos["cpf"] == "006.725.812-30"
        assert campos.get("cargo", "").startswith("AUXILIAR")
        assert campos.get("cbo") == "514320"
        assert campos.get("sexo") == "Masculino"
        assert campos.get("cor_raca") == "Parda"
        assert campos.get("grau_instrucao") == "Ensino Médio Completo"

    def test_contrato_completo(self):
        """Testa extracao do PDF real do Contrato de Experiencia."""
        try:
            from ocr_cadastro import ler_documento
            with open("/nfs/105093785/uploads/Contrato_de_Experiência.pdf", "rb") as f:
                texto = ler_documento(f)
        except FileNotFoundError:
            pytest.skip("PDF de teste nao disponivel")

        campos = _extrair_com_regex(texto, "contrato")
        assert campos.get("experiencia_dias") == 45
        assert campos.get("contrato_inicio") == "2026-09-08"
        assert campos.get("contrato_fim") == "2026-10-22"
        assert "CONSELHEIRO FURTADO" in campos.get("loja", "")

    def test_mesclagem_completa(self):
        """Testa mesclagem dos dois PDFs reais."""
        try:
            from ocr_cadastro import ler_documento
            with open("/nfs/105093785/uploads/Ficha_Registro_de_Empregado.pdf", "rb") as f:
                texto_reg = ler_documento(f)
            with open("/nfs/105093785/uploads/Contrato_de_Experiência.pdf", "rb") as f:
                texto_cont = ler_documento(f)
        except FileNotFoundError:
            pytest.skip("PDFs de teste nao disponiveis")

        campos_reg = _extrair_com_regex(texto_reg, "registro")
        campos_cont = _extrair_com_regex(texto_cont, "contrato")
        mesclado = mesclar_campos(campos_reg, campos_cont)
        sistema = campos_para_sistema(mesclado)

        # Verificar campos criticos
        assert sistema["nome"] == "MICHEL LUIS ALBUQUERQUE NUNES"
        assert sistema["matricula"] == "16460"
        assert sistema["cpf"] == "006.725.812-30"
        assert sistema["experiencia_dias"] == 45
        assert sistema["situacao"] == "Ativo"
        assert "CONSELHEIRO FURTADO" in sistema.get("loja", "")
        assert sistema["cargo"].startswith("AUXILIAR")
        # CBO deve estar na observacao
        assert "514320" in sistema.get("observacao", "")
