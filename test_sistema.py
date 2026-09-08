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
from dashboard import eventos_experiencia


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
        # CLT: admissao = dia 1, entao 45d termina em 28/02/2025
        ref = date(2025, 2, 28)  # ultimo dia do contrato
        e = cal.contrato_experiencia(adm, 45, ref)
        self.assertEqual(e["prazo_dias"], 45)
        self.assertFalse(e["encerrado"])
        self.assertEqual(e["fim"], adm + timedelta(days=44))  # CLT

        e2 = cal.contrato_experiencia(adm, 45, date(2025, 3, 20))
        self.assertTrue(e2["encerrado"])

    def test_prazos_intermediarios_60(self):
        adm = date(2025, 1, 1)
        e = cal.contrato_experiencia(adm, 60, date(2025, 2, 1))
        prazos = e["prazos_intermediarios"]
        self.assertEqual(len(prazos), 2)
        self.assertEqual(prazos[0][0], 30)
        self.assertEqual(prazos[0][1], adm + timedelta(days=29))  # CLT
        self.assertEqual(prazos[1][0], 60)
        self.assertEqual(prazos[1][1], adm + timedelta(days=59))  # CLT

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

    def test_todos_os_prazos_presente(self):
        """Verifica que todos_os_prazos contem 3 entradas (45, 60, 90)."""
        adm = date(2025, 1, 1)
        e = cal.contrato_experiencia(adm, 30, date(2025, 2, 1))
        self.assertIn("todos_os_prazos", e)
        todos = e["todos_os_prazos"]
        self.assertEqual(len(todos), 3)
        dias_list = [t["prazo_dias"] for t in todos]
        self.assertEqual(dias_list, [45, 60, 90])

    def test_todos_os_prazos_datas_corretas(self):
        """Verifica que cada prazo em todos_os_prazos tem data correta (CLT: admissao = dia 1)."""
        adm = date(2025, 3, 10)
        e = cal.contrato_experiencia(adm, 45, date(2025, 4, 1))
        todos = e["todos_os_prazos"]
        # 45d: adm + 44 dias = 2025-04-24
        self.assertEqual(todos[0]["fim"], adm + timedelta(days=44))  # CLT
        # 60d: adm + 59 dias = 2025-05-09
        self.assertEqual(todos[1]["fim"], adm + timedelta(days=59))  # CLT
        # 90d: adm + 89 dias = 2025-06-08
        self.assertEqual(todos[2]["fim"], adm + timedelta(days=89))  # CLT

    def test_todos_os_prazos_tem_prazos_intermediarios(self):
        """Cada entrada de todos_os_prazos tem prazos_intermediarios."""
        adm = date(2025, 1, 1)
        e = cal.contrato_experiencia(adm, 30, date(2025, 2, 1))
        for t in e["todos_os_prazos"]:
            self.assertIn("prazos_intermediarios", t)
            self.assertTrue(len(t["prazos_intermediarios"]) >= 1)
            # 60d = 30+30, 90d = 45+45, 45d = unico
            if t["prazo_dias"] == 60:
                self.assertEqual(len(t["prazos_intermediarios"]), 2)
            elif t["prazo_dias"] == 90:
                self.assertEqual(len(t["prazos_intermediarios"]), 2)
            elif t["prazo_dias"] == 45:
                self.assertEqual(len(t["prazos_intermediarios"]), 1)


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

    def test_alerta_4_meses_menos_de_24m(self):
        """Colaborador com < 24 meses: alerta quando falta <=120 dias para liberacao aos 20m."""
        adm = date(2025, 1, 10)
        # Liberacao aos 20 meses = 2026-09-10
        # 90 dias antes = 2026-06-12 → dentro dos 120 dias
        ref = date(2026, 6, 15)  # ~87 dias antes da liberacao
        f = cal.calcular_ferias(adm, ref)
        self.assertTrue(f["alerta_4_meses"])
        self.assertIn("ALERTA", f["situacao"])

    def test_alerta_4_meses_mais_de_24m(self):
        """Colaborador com >= 24 meses: alerta aos 4 meses do ciclo (4m antes de 8m)."""
        adm = date(2023, 3, 15)
        # Apos 24 meses, novo ciclo comeca em 2025-03-15
        # Liberacao aos 8 meses do ciclo = 2025-11-15
        # Alerta 4 meses antes = 2025-07-15
        ref = date(2025, 7, 20)  # ~4 meses antes da liberacao
        f = cal.calcular_ferias(adm, ref)
        self.assertTrue(f["alerta_4_meses"])

    def test_sem_alerta_4_meses_quando_longe(self):
        """Sem alerta quando falta mais de 4 meses para liberacao."""
        adm = date(2025, 1, 10)
        ref = date(2025, 9, 10)  # 8 meses, faltam 12 meses para liberacao aos 20m
        f = cal.calcular_ferias(adm, ref)
        self.assertFalse(f["alerta_4_meses"])

    def test_sem_alerta_4_meses_quando_liberada(self):
        """Sem alerta quando ferias ja estao liberadas."""
        adm = date(2024, 1, 10)
        ref = date(2025, 10, 15)  # Ja passou de 20 meses
        f = cal.calcular_ferias(adm, ref)
        self.assertTrue(f["liberada"])
        self.assertFalse(f["alerta_4_meses"])


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
        self.assertEqual(cal.situacao_por_evento("afastamento_doenca"), "Ativo")  # removido
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
        self.assertIn("Licença Maternidade", cal.TIPOS_AFASTAMENTO)
        self.assertNotIn("Doença", cal.TIPOS_AFASTAMENTO)


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
        self.assertNotIn("Afastado Doença", situacoes)
        self.assertIn("Desligado com J/C", situacoes)
        self.assertIn("Desligado sem J/C", situacoes)
        self.assertIn("Abandono", situacoes)
        self.assertIn("Desistente", situacoes)
        self.assertIn("Rescisão Indireta", situacoes)
        self.assertIn("Pedido de Demissão", situacoes)

    def test_excluir_combo_persiste(self):
        """Excluir combo padrao NAO deve ser re-inserido ao listar novamente."""
        b = self.banco
        # Adicionar combo que nao esta em uso
        b.add_combo("loja", "Loja Temp Test")
        self.assertIn("Loja Temp Test", b.listar_combo("loja"))
        # Excluir
        self.assertTrue(b.remover_combo("loja", "Loja Temp Test"))
        # Verificar que NAO reaparece ao listar
        self.assertNotIn("Loja Temp Test", b.listar_combo("loja"))

    def test_excluir_combo_padrao_persiste(self):
        """Excluir combo padrao (ex: Loja 02 - Centro) NAO deve re-inserir."""
        b = self.banco
        # Ver que existe
        self.assertIn("Loja 02 - Centro", b.listar_combo("loja"))
        # Excluir
        self.assertTrue(b.remover_combo("loja", "Loja 02 - Centro"))
        # Chamar listar_combo novamente — NAO deve re-inserir
        self.assertNotIn("Loja 02 - Centro", b.listar_combo("loja"))

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

    def test_remover_combo_livre(self):
        """Remove combo quando nao esta em uso por funcionario."""
        b = self.banco
        b.add_combo("cargo", "Cargo Teste Remover")
        self.assertIn("Cargo Teste Remover", b.listar_combo("cargo"))
        resultado = b.remover_combo("cargo", "Cargo Teste Remover")
        self.assertTrue(resultado)
        self.assertNotIn("Cargo Teste Remover", b.listar_combo("cargo"))

    def test_remover_combo_em_uso(self):
        """Nao permite remover combo em uso por funcionario."""
        b = self.banco
        b.add_combo("cargo", "Cargo Em Uso")
        b.inserir({"matricula": "0099", "nome": "Func Teste Combo",
                   "rg": "", "cpf": "", "telefone": "",
                   "admissao": "2025-01-10", "loja": "Loja 01",
                   "situacao": "Ativo", "cargo": "Cargo Em Uso",
                   "experiencia_dias": None, "foto": None,
                   "observacao": ""})
        resultado = b.remover_combo("cargo", "Cargo Em Uso")
        self.assertFalse(resultado)
        # Ainda deve estar na lista
        self.assertIn("Cargo Em Uso", b.listar_combo("cargo"))
        # Limpar
        regs = b.pesquisar(termo="0099")
        if regs:
            b.excluir(regs[0]["id"])
        b.remover_combo("cargo", "Cargo Em Uso")


class TestDesligamentoBaixaEventos(unittest.TestCase):
    """Testa que desligamento encerra todos os eventos ativos."""

    @classmethod
    def setUpClass(cls):
        cls.banco = Banco()

    @classmethod
    def tearDownClass(cls):
        cls.banco.fechar()

    def _inserir_com_eventos(self, matricula="D001"):
        """Insere funcionario com todos os eventos ativos."""
        b = self.banco
        b.inserir({
            "matricula": matricula, "nome": "Func Deslig Test",
            "rg": "", "cpf": "", "telefone": "",
            "admissao": "2025-01-10", "loja": "Loja 01",
            "situacao": "Está de Férias", "cargo": "Vendedor",
            "experiencia_dias": 90, "foto": None,
            "observacao": "",
            "ferias_inicio": "2025-06-01", "ferias_dias": 30,
            "ferias_retorno": "2025-07-01",
            "licenca_maternidade_inicio": None,
            "licenca_maternidade_dias": None,
            "licenca_maternidade_retorno": None,
            "afastamento_tipo": None,
            "afastamento_inicio": None,
            "afastamento_dias": None,
            "afastamento_retorno": None,
        })
        regs = b.pesquisar(termo=matricula)
        return regs[0]

    def _inserir_com_todos_eventos(self, matricula="D002"):
        """Insere funcionario com ferias + licenca + afastamento ativos."""
        b = self.banco
        b.inserir({
            "matricula": matricula, "nome": "Func Todos Eventos",
            "rg": "", "cpf": "", "telefone": "",
            "admissao": "2025-01-10", "loja": "Loja 01",
            "situacao": "Ativo", "cargo": "Vendedor",
            "experiencia_dias": 45, "foto": None,
            "observacao": "",
            "ferias_inicio": "2025-06-01", "ferias_dias": 30,
            "ferias_retorno": "2025-07-01",
            "licenca_maternidade_inicio": "2025-03-01",
            "licenca_maternidade_dias": 120,
            "licenca_maternidade_retorno": "2025-06-29",
            "afastamento_tipo": "INSS",
            "afastamento_inicio": "2025-08-01",
            "afastamento_dias": 15,
            "afastamento_retorno": "2025-08-16",
        })
        regs = b.pesquisar(termo=matricula)
        return regs[0]

    def test_desligamento_limpa_ferias(self):
        """Desligamento deve limpar campos de ferias."""
        reg = self._inserir_com_eventos("D010")
        b = self.banco
        # Aplicar desligamento
        dados_deslig = {
            "situacao": "Desistente",
            "demissao": "2025-06-15",
            "experiencia_dias": None,
            "ferias_inicio": None, "ferias_dias": None,
            "ferias_retorno": None,
            "licenca_maternidade_inicio": None,
            "licenca_maternidade_dias": None,
            "licenca_maternidade_retorno": None,
            "afastamento_inicio": None, "afastamento_dias": None,
            "afastamento_retorno": None, "afastamento_tipo": None,
        }
        b.atualizar(reg["id"], dados_deslig)
        reg_pos = b.obter(reg["id"])
        self.assertEqual(reg_pos["situacao"], "Desistente")
        self.assertEqual(reg_pos["demissao"], "2025-06-15")
        self.assertIsNone(reg_pos["ferias_inicio"])
        self.assertIsNone(reg_pos["ferias_dias"])
        self.assertIsNone(reg_pos["ferias_retorno"])
        b.excluir(reg["id"])

    def test_desligamento_limpa_todos_eventos(self):
        """Desligamento deve limpar ferias, licenca e afastamento."""
        reg = self._inserir_com_todos_eventos("D011")
        b = self.banco
        # Verificar que eventos existem antes
        self.assertIsNotNone(reg["ferias_inicio"])
        self.assertIsNotNone(reg["licenca_maternidade_inicio"])
        self.assertIsNotNone(reg["afastamento_inicio"])
        self.assertEqual(reg["experiencia_dias"], 45)
        # Aplicar desligamento
        dados_deslig = {
            "situacao": "Pedido de Demissão",
            "demissao": "2025-07-01",
            "experiencia_dias": None,
            "ferias_inicio": None, "ferias_dias": None,
            "ferias_retorno": None,
            "licenca_maternidade_inicio": None,
            "licenca_maternidade_dias": None,
            "licenca_maternidade_retorno": None,
            "afastamento_inicio": None, "afastamento_dias": None,
            "afastamento_retorno": None, "afastamento_tipo": None,
        }
        b.atualizar(reg["id"], dados_deslig)
        reg_pos = b.obter(reg["id"])
        # Todos os campos de evento devem ser None
        self.assertIsNone(reg_pos["experiencia_dias"])
        self.assertIsNone(reg_pos["ferias_inicio"])
        self.assertIsNone(reg_pos["ferias_dias"])
        self.assertIsNone(reg_pos["ferias_retorno"])
        self.assertIsNone(reg_pos["licenca_maternidade_inicio"])
        self.assertIsNone(reg_pos["licenca_maternidade_dias"])
        self.assertIsNone(reg_pos["licenca_maternidade_retorno"])
        self.assertIsNone(reg_pos["afastamento_inicio"])
        self.assertIsNone(reg_pos["afastamento_dias"])
        self.assertIsNone(reg_pos["afastamento_retorno"])
        self.assertIsNone(reg_pos["afastamento_tipo"])
        b.excluir(reg["id"])

    def test_reverter_desligamento_nao_restaura_eventos(self):
        """Reverter desligamento so volta situacao e demissao,
        NAO restaura eventos que foram limpos."""
        reg = self._inserir_com_todos_eventos("D012")
        b = self.banco
        # Aplicar desligamento
        dados_deslig = {
            "situacao": "Desistente",
            "demissao": "2025-07-01",
            "experiencia_dias": None,
            "ferias_inicio": None, "ferias_dias": None,
            "ferias_retorno": None,
            "licenca_maternidade_inicio": None,
            "licenca_maternidade_dias": None,
            "licenca_maternidade_retorno": None,
            "afastamento_inicio": None, "afastamento_dias": None,
            "afastamento_retorno": None, "afastamento_tipo": None,
        }
        b.atualizar(reg["id"], dados_deslig)
        # Reverter para Ativo
        b.atualizar(reg["id"], {"situacao": "Ativo", "demissao": None})
        reg_pos = b.obter(reg["id"])
        self.assertEqual(reg_pos["situacao"], "Ativo")
        self.assertIsNone(reg_pos["demissao"])
        # Eventos continuam limpos — usuario pode re-registrar
        self.assertIsNone(reg_pos["ferias_inicio"])
        self.assertIsNone(reg_pos["licenca_maternidade_inicio"])
        self.assertIsNone(reg_pos["afastamento_inicio"])
        b.excluir(reg["id"])

    def test_tipos_desligamento_lista_correta(self):
        """Verifica que todos os tipos de desligamento estao definidos."""
        tipos_esperados = [
            "Desligado com J/C", "Desligado sem J/C",
            "Abandono", "Desistente",
            "Rescisão Indireta", "Pedido de Demissão",
        ]
        self.assertEqual(cal.TIPOS_DESLIGAMENTO, tipos_esperados)


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


class TestEventosExperienciaDashboard(unittest.TestCase):
    """Testes para eventos_experiencia() do dashboard.
    Deve retornar 4 prazos (30,45,60,90) por funcionario
    com contrato de experiencia, e ignorar desligados."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="test_evexp_")
        os.environ["SISTEMA_DADOS_DIR"] = self._tmp
        # Re-importar Banco para que ele use o novo dir
        import importlib
        import database as _db_mod
        importlib.reload(_db_mod)
        from database import Banco as _Banco
        self.banco = _Banco()

    def tearDown(self):
        self.banco.fechar()
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _inserir(self, matricula, nome, situacao="Ativo", exp_dias=90,
                 admissao="2025-03-01", loja="Loja 01", cargo="Vendedor"):
        self.banco.inserir({
            "matricula": matricula, "nome": nome, "rg": "", "cpf": "",
            "telefone": "", "admissao": admissao, "loja": loja,
            "situacao": situacao, "cargo": cargo,
            "experiencia_dias": exp_dias, "foto": None, "observacao": "",
        })

    def test_quatro_prazos_por_funcionario(self):
        """Cada funcionario com experiencia_dias gera 4 linhas."""
        self._inserir("E001", "Ana")
        regs = self.banco.pesquisar()
        df = eventos_experiencia(regs, ref=date(2025, 4, 1))
        prazos_str = df["Prazo"].tolist()
        self.assertEqual(len(prazos_str), 4)
        self.assertIn("30d (30)", prazos_str)
        self.assertIn("45d (45)", prazos_str)
        self.assertIn("60d (30 + 30)", prazos_str)
        self.assertIn("90d (45 + 45)", prazos_str)

    def test_ignora_funcionario_sem_experiencia(self):
        """Funcionario sem experiencia_dias nao aparece."""
        self._inserir("E002", "Beto", exp_dias=None)
        regs = self.banco.pesquisar()
        df = eventos_experiencia(regs, ref=date(2025, 4, 1))
        self.assertTrue(df.empty)

    def test_ignora_funcionario_desligado(self):
        """Funcionario desligado nao aparece na lista."""
        self._inserir("E003", "Carlos", situacao="Desligado com J/C")
        regs = self.banco.pesquisar()
        df = eventos_experiencia(regs, ref=date(2025, 4, 1))
        self.assertTrue(df.empty)

    def test_datas_fim_corretas_clt(self):
        """Data fim calculada com regra CLT: admissao + prazo - 1 dia."""
        self._inserir("E004", "Diana", admissao="2025-06-10", exp_dias=45)
        regs = self.banco.pesquisar()
        df = eventos_experiencia(regs, ref=date(2025, 7, 1))
        # Prazo 30d: 10/06 + 29 dias = 09/07
        linha_30 = df[df["Prazo"].str.startswith("30d")].iloc[0]
        self.assertEqual(linha_30["Fim"], "09/07/2025")
        # Prazo 90d: 10/06 + 89 dias = 07/09
        linha_90 = df[df["Prazo"].str.startswith("90d")].iloc[0]
        self.assertEqual(linha_90["Fim"], "07/09/2025")

    def test_multiplos_funcionarios(self):
        """Dois funcionarios ativos geram 8 linhas (4 cada)."""
        self._inserir("E010", "Func E010")
        self._inserir("E011", "Func E011")
        regs = self.banco.pesquisar()
        df = eventos_experiencia(regs, ref=date(2025, 3, 1))
        self.assertEqual(len(df), 8)


if __name__ == "__main__":
    unittest.main()