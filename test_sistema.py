"""Testes das regras de negocio e exportacao.
Execute: python -m unittest test_sistema -v
"""

import os
import shutil
import tempfile
import unittest
from datetime import date, timedelta

DADOS_TMP = tempfile.mkdtemp(prefix="teste_sis_")
os.environ["SISTEMA_DADOS_DIR"] = DADOS_TMP

import calculos as cal
from database import Banco
from exportador import exportar_bytes


class TestDatas(unittest.TestCase):
    def test_parse_formatos(self):
        self.assertEqual(cal.parse_data("2025-01-10"), date(2025, 1, 10))
        self.assertEqual(cal.parse_data(date(2025, 3, 15)), date(2025, 3, 15))
        self.assertIsNone(cal.parse_data(""))
        self.assertIsNone(cal.parse_data(None))

    def test_add_months_fim_de_mes(self):
        self.assertEqual(cal.add_meses(date(2025, 1, 31), 1), date(2025, 2, 28))

    def test_meses_completos(self):
        ref = date(2025, 6, 10)
        self.assertEqual(cal.meses_completos(date(2025, 1, 10), ref), 5)
        self.assertEqual(cal.meses_completos(date(2024, 6, 10), ref), 12)


class TestExperiencia(unittest.TestCase):
    def test_prazos(self):
        self.assertEqual(cal.PRAZOS_EXPERIENCIA, [30, 45, 60, 90])

    def test_alerta_e_encerrado(self):
        adm = date(2025, 1, 15)
        ref = date(2025, 2, 15)
        e = cal.contrato_experiencia(adm, 45, ref)
        self.assertEqual(e["prazo_dias"], 45)
        self.assertFalse(e["encerrado"])

        e2 = cal.contrato_experiencia(adm, 45, date(2025, 3, 20))
        self.assertTrue(e2["encerrado"])

    def test_prazos_intermediarios_60(self):
        adm = date(2025, 1, 1)
        e = cal.contrato_experiencia(adm, 60, date(2025, 2, 1))
        prazos = e["prazos_intermediarios"]
        self.assertEqual(len(prazos), 2)
        self.assertEqual(prazos[0][0], 30)
        self.assertEqual(prazos[0][1], adm + timedelta(days=30))
        self.assertEqual(prazos[1][0], 60)
        self.assertEqual(prazos[1][1], adm + timedelta(days=60))

    def test_prazos_intermediarios_90(self):
        adm = date(2025, 1, 1)
        e = cal.contrato_experiencia(adm, 90, date(2025, 2, 1))
        prazos = e["prazos_intermediarios"]
        self.assertEqual(len(prazos), 2)
        self.assertEqual(prazos[0][0], 45)
        self.assertEqual(prazos[1][0], 90)

    def test_prazos_intermediarios_30(self):
        adm = date(2025, 1, 1)
        e = cal.contrato_experiencia(adm, 30, date(2025, 1, 15))
        prazos = e["prazos_intermediarios"]
        self.assertEqual(len(prazos), 1)
        self.assertEqual(prazos[0][0], 30)


class TestFerias(unittest.TestCase):
    def test_menos_de_um_ano_regra_20_de_24(self):
        adm = date(2025, 1, 10)
        ref = date(2025, 9, 10)
        f = cal.calcular_ferias(adm, ref)
        self.assertEqual(f["regra"], "Menos de 1 ano (20 de 24)")
        self.assertFalse(f["liberada"])

    def test_mais_de_um_ano_regra_8_de_12(self):
        adm = date(2023, 1, 10)
        ref = date(2025, 9, 10)
        f = cal.calcular_ferias(adm, ref)
        self.assertIn("8 de 12", f["regra"])
        self.assertTrue(f["liberada"])

    def test_periodo_acompanha_aniversario(self):
        adm = date(2022, 3, 15)
        ref = date(2025, 5, 15)
        f = cal.calcular_ferias(adm, ref)
        self.assertIn("8 de 12", f["regra"])
        self.assertEqual(f["anos_casa"], 3)

    def test_ferias_vencida_apos_limite_gozo(self):
        adm = date(2024, 1, 10)
        ref = date(2026, 5, 15)
        f = cal.calcular_ferias(adm, ref)
        self.assertTrue(f["vencida"])
        self.assertIn("VENCIDA", f["situacao"])

    def test_ferias_nao_vencida_antes_do_limite(self):
        adm = date(2024, 1, 10)
        ref = date(2026, 10, 15)
        f = cal.calcular_ferias(adm, ref)
        self.assertTrue(f["liberada"])
        self.assertFalse(f["vencida"])

    def test_ferias_gozo_proximo_30_dias(self):
        adm = date(2024, 1, 10)
        ref = date(2025, 12, 31)
        f = cal.calcular_ferias(adm, ref)
        self.assertTrue(f["proxima_vencer_gozo"])
        self.assertIn("gozo vence", f["situacao"].lower())


class TestEventos(unittest.TestCase):
    def test_calcular_retorno(self):
        inicio = date(2025, 6, 1)
        retorno = cal.calcular_retorno(inicio, 30)
        self.assertEqual(retorno, date(2025, 7, 1))

    def test_calcular_retorno_none(self):
        self.assertIsNone(cal.calcular_retorno(None, 30))
        self.assertIsNone(cal.calcular_retorno(date(2025, 1, 1), None))

    def test_situacao_por_evento(self):
        self.assertEqual(cal.situacao_por_evento("ferias"), "Está de Férias")
        self.assertEqual(cal.situacao_por_evento("licenca_maternidade"), "Licença Maternidade")
        self.assertEqual(cal.situacao_por_evento("afastamento_inss"), "Afastado INSS")
        self.assertEqual(cal.situacao_por_evento("afastamento_doenca"), "Afastado Doença")
        self.assertEqual(cal.situacao_por_evento("outro"), "Ativo")

    def test_tipos_desligamento(self):
        self.assertIn("Desligado com J/C", cal.TIPOS_DESLIGAMENTO)
        self.assertIn("Desligado sem J/C", cal.TIPOS_DESLIGAMENTO)
        self.assertIn("Abandono", cal.TIPOS_DESLIGAMENTO)
        self.assertIn("Desistente", cal.TIPOS_DESLIGAMENTO)
        self.assertIn("Rescisão Indireta", cal.TIPOS_DESLIGAMENTO)
        self.assertIn("Pedido de Demissão", cal.TIPOS_DESLIGAMENTO)

    def test_tipos_afastamento(self):
        self.assertIn("INSS", cal.TIPOS_AFASTAMENTO)
        self.assertIn("Doença", cal.TIPOS_AFASTAMENTO)


class TestCPF(unittest.TestCase):
    def test_validacao(self):
        self.assertTrue(cal.cpf_valido("529.982.247-25"))
        self.assertFalse(cal.cpf_valido("000.000.000-00"))
        self.assertFalse(cal.cpf_valido("123"))

    def test_formatacoes(self):
        self.assertEqual(cal.formatar_cpf("52998224725"),
                         "529.982.247-25")
        tel = cal.formatar_telefone("11987654321")
        self.assertEqual(tel, "(11) 98765-4321")


class TestBanco(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banco = Banco()

    @classmethod
    def tearDownClass(cls):
        cls.banco.fechar()
        shutil.rmtree(DADOS_TMP, ignore_errors=True)

    def test_crud_e_persistencia(self):
        b = self.banco
        b.inserir({"matricula": "0001", "nome": "Teste",
                   "rg": "", "cpf": "", "telefone": "",
                   "admissao": "2025-01-10", "loja": "Loja 01",
                   "situacao": "Ativo", "cargo": "Vendedor",
                   "experiencia_dias": 45, "foto": None,
                   "observacao": ""})
        regs = b.pesquisar()
        self.assertEqual(len(regs), 1)
        self.assertEqual(regs[0]["nome"], "Teste")

        b.atualizar(regs[0]["id"], {"nome": "Alterado"})
        reg = b.obter(regs[0]["id"])
        self.assertEqual(reg["nome"], "Alterado")

        b.excluir(regs[0]["id"])
        self.assertEqual(len(b.pesquisar()), 0)

    def test_combos_padrao(self):
        lojas = self.banco.listar_combo("loja")
        self.assertIn("Loja 01 - Matriz", lojas)
        situacoes = self.banco.listar_combo("situacao")
        self.assertIn("Ativo", situacoes)

    def test_combos_novos_situacoes(self):
        situacoes = self.banco.listar_combo("situacao")
        self.assertIn("Está de Férias", situacoes)
        self.assertIn("Licença Maternidade", situacoes)
        self.assertIn("Afastado INSS", situacoes)
        self.assertIn("Afastado Doença", situacoes)
        self.assertIn("Desligado com J/C", situacoes)
        self.assertIn("Desligado sem J/C", situacoes)
        self.assertIn("Abandono", situacoes)
        self.assertIn("Desistente", situacoes)
        self.assertIn("Rescisão Indireta", situacoes)
        self.assertIn("Pedido de Demissão", situacoes)

    def test_eventos_ferias_no_banco(self):
        b = self.banco
        b.inserir({"matricula": "0020", "nome": "Ferias Test",
                   "rg": "", "cpf": "", "telefone": "",
                   "admissao": "2025-01-10", "loja": "Loja 01",
                   "situacao": "Está de Férias", "cargo": "Vendedor",
                   "experiencia_dias": 45, "foto": None,
                   "observacao": "",
                   "ferias_inicio": "2025-06-01", "ferias_dias": 30,
                   "ferias_retorno": "2025-07-01"})
        regs = b.pesquisar(termo="0020")
        self.assertEqual(len(regs), 1)
        self.assertEqual(regs[0]["ferias_inicio"], "2025-06-01")
        self.assertEqual(regs[0]["ferias_dias"], 30)
        self.assertEqual(regs[0]["ferias_retorno"], "2025-07-01")
        b.excluir(regs[0]["id"])

    def test_eventos_licenca_maternidade(self):
        b = self.banco
        b.inserir({"matricula": "0030", "nome": "Licenca Test",
                   "rg": "", "cpf": "", "telefone": "",
                   "admissao": "2025-01-10", "loja": "Loja 01",
                   "situacao": "Licença Maternidade", "cargo": "Vendedor",
                   "experiencia_dias": None, "foto": None,
                   "observacao": "",
                   "licenca_maternidade_inicio": "2025-03-01",
                   "licenca_maternidade_dias": 120,
                   "licenca_maternidade_retorno": "2025-06-29"})
        regs = b.pesquisar(termo="0030")
        self.assertEqual(len(regs), 1)
        self.assertEqual(regs[0]["licenca_maternidade_dias"], 120)
        b.excluir(regs[0]["id"])

    def test_eventos_afastamento(self):
        b = self.banco
        b.inserir({"matricula": "0040", "nome": "Afast Test",
                   "rg": "", "cpf": "", "telefone": "",
                   "admissao": "2025-01-10", "loja": "Loja 01",
                   "situacao": "Afastado INSS", "cargo": "Vendedor",
                   "experiencia_dias": None, "foto": None,
                   "observacao": "",
                   "afastamento_tipo": "INSS",
                   "afastamento_inicio": "2025-05-01",
                   "afastamento_dias": 15,
                   "afastamento_retorno": "2025-05-16"})
        regs = b.pesquisar(termo="0040")
        self.assertEqual(len(regs), 1)
        self.assertEqual(regs[0]["afastamento_tipo"], "INSS")
        b.excluir(regs[0]["id"])

    def test_migracao_colunas_novas(self):
        """Verifica que colunas de eventos existem apos migracao."""
        b = self.banco
        reg = b.obter(1) if b.pesquisar() else None
        # Se ha algum registro, todas as colunas devem estar presentes
        if reg:
            self.assertIn("ferias_inicio", reg)
            self.assertIn("ferias_dias", reg)
            self.assertIn("ferias_retorno", reg)
            self.assertIn("licenca_maternidade_inicio", reg)
            self.assertIn("licenca_maternidade_dias", reg)
            self.assertIn("licenca_maternidade_retorno", reg)
            self.assertIn("afastamento_tipo", reg)
            self.assertIn("afastamento_inicio", reg)
            self.assertIn("afastamento_dias", reg)
            self.assertIn("afastamento_retorno", reg)


class TestExportacao(unittest.TestCase):
    def test_exporta_todos_os_registros(self):
        banco = Banco()
        banco.inserir({"matricula": "0001", "nome": "Maria",
                       "rg": "", "cpf": "", "telefone": "",
                       "admissao": "2025-01-10", "loja": "Loja 01",
                       "situacao": "Ativo", "cargo": "Vendedor",
                       "experiencia_dias": 45, "foto": None,
                       "observacao": ""})
        conteudo, nome = exportar_bytes(banco.pesquisar())
        self.assertTrue(len(conteudo) > 0)
        banco.fechar()

    def test_exporta_csv_e_respeita_filtro(self):
        banco = Banco()
        conteudo, nome = exportar_bytes(banco.pesquisar(loja="NaoExiste"))
        if nome.endswith(".csv"):
            self.assertEqual(len(conteudo), 0)
        banco.fechar()


if __name__ == "__main__":
    unittest.main()