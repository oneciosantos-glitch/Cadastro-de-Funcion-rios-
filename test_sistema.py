"""Testes das regras de negocio e exportacao.
Execute: python -m unittest test_sistema -v
"""

import os
import shutil
import tempfile
import unittest
from datetime import date

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
        # 15/jan + 45d = 1/mar -> em 15/fev ainda nao encerrou
        adm = date(2025, 1, 15)
        ref = date(2025, 2, 15)
        e = cal.contrato_experiencia(adm, 45, ref)
        self.assertEqual(e["prazo_dias"], 45)
        self.assertFalse(e["encerrado"])

        # apos o fim do contrato
        e2 = cal.contrato_experiencia(adm, 45, date(2025, 3, 20))
        self.assertTrue(e2["encerrado"])


class TestFerias(unittest.TestCase):
    def test_menos_de_um_ano_regra_20_de_24(self):
        adm = date(2025, 1, 10)
        ref = date(2025, 9, 10)  # 8 meses
        f = cal.calcular_ferias(adm, ref)
        self.assertEqual(f["regra"], "Menos de 1 ano (20 de 24)")
        self.assertFalse(f["liberada"])

    def test_mais_de_um_ano_regra_8_de_12(self):
        adm = date(2023, 1, 10)
        # Precisa ter 24+ meses de casa para regra 8/12
        ref = date(2025, 9, 10)  # 2 anos e 8 meses
        f = cal.calcular_ferias(adm, ref)
        self.assertIn("8 de 12", f["regra"])
        self.assertTrue(f["liberada"])

    def test_periodo_acompanha_aniversario(self):
        adm = date(2022, 3, 15)
        ref = date(2025, 5, 15)  # 3 anos + 2 meses
        f = cal.calcular_ferias(adm, ref)
        self.assertIn("8 de 12", f["regra"])
        self.assertEqual(f["anos_casa"], 3)

    def test_ferias_vencida_apos_limite_gozo(self):
        """Quando ref esta entre inicio e liberacao do novo periodo, ferias do periodo anterior estao vencidas."""
        adm = date(2024, 1, 10)
        # Aniv 2 anos = 10/jan/2026, novo periodo inicio=10/jan/2026
        # lib do novo periodo = 10/set/2026
        # Vencida: 10/jan/2026 < ref < 10/set/2026
        ref = date(2026, 5, 15)  # entre inicio e liberacao
        f = cal.calcular_ferias(adm, ref)
        self.assertTrue(f["vencida"])
        self.assertIn("VENCIDA", f["situacao"])

    def test_ferias_nao_vencida_antes_do_limite(self):
        """Apos liberacao do periodo atual, ferias nao estao vencidas."""
        adm = date(2024, 1, 10)
        # Lib do periodo atual (aniv 2026) = 10/set/2026
        ref = date(2026, 10, 15)  # apos liberacao
        f = cal.calcular_ferias(adm, ref)
        self.assertTrue(f["liberada"])
        self.assertFalse(f["vencida"])

    def test_ferias_gozo_proximo_30_dias(self):
        """Ferias com gozo vencendo em ate 30 dias gera alerta."""
        adm = date(2024, 1, 10)
        # Periodo 20/24: adm=10/jan/2024, lib=10/set/2025, gozo=10/jan/2026
        # Aniv 2025: inicio=10/jan/2025, lib=10/set/2025, gozo=10/jan/2026
        ref = date(2025, 12, 31)  # 10 dias antes do gozo
        f = cal.calcular_ferias(adm, ref)
        self.assertTrue(f["proxima_vencer_gozo"])
        self.assertIn("gozo vence", f["situacao"].lower())


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
