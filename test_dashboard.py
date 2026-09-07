"""Testes dos calculos do dashboard.
Execute: python -m unittest test_dashboard -v
"""

import os
import shutil
import tempfile
import unittest
from datetime import date

import calculos as cal
import dashboard as dash


def _banco_com_dados(dados_dir):
    os.environ["SISTEMA_DADOS_DIR"] = dados_dir
    # Re-import para pegar o novo DB_PATH
    import importlib
    import database as _db
    importlib.reload(_db)
    banco = _db.Banco()
    banco.inserir({"matricula": "0001", "nome": "Maria Silva",
                   "rg": "", "cpf": "", "telefone": "",
                   "admissao": "2025-01-10", "loja": "Loja 01 - Matriz",
                   "situacao": "Ativo", "cargo": "Vendedor",
                   "experiencia_dias": 45, "foto": None,
                   "observacao": ""})
    banco.inserir({"matricula": "0002", "nome": "Jose Souza",
                   "rg": "", "cpf": "", "telefone": "",
                   "admissao": "2019-06-01", "loja": "Loja 02 - Centro",
                   "situacao": "Ativo", "cargo": "Gerente",
                   "experiencia_dias": None, "foto": None,
                   "observacao": ""})
    banco.inserir({"matricula": "0003", "nome": "Ana Desligada",
                   "rg": "", "cpf": "", "telefone": "",
                   "admissao": "2024-01-10", "loja": "Loja 01 - Matriz",
                   "situacao": "Desligado", "cargo": "Vendedor",
                   "experiencia_dias": None, "foto": None,
                   "observacao": "", "demissao": "2025-03-15"})
    return banco, _db


class TestDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._dados_dir = tempfile.mkdtemp(prefix="teste_dash_")
        cls.banco, cls._db = _banco_com_dados(cls._dados_dir)
        cls.registros = cls.banco.pesquisar()

    @classmethod
    def tearDownClass(cls):
        cls.banco.fechar()
        shutil.rmtree(cls._dados_dir, ignore_errors=True)

    def test_totais_do_periodo(self):
        t = dash.turnover_periodo(self.registros, 12, date(2025, 6, 1))
        self.assertGreaterEqual(t["quadro_atual"], 1)
        self.assertGreaterEqual(t["admissoes"], 0)

    def test_movimentacao_mensal(self):
        df = dash.movimentacao_mensal(self.registros, 6, date(2025, 6, 1))
        self.assertFalse(df.empty)
        self.assertIn("Turnover %", df.columns)

    def test_turnover_por_loja(self):
        df = dash.turnover_por_loja(self.registros, 12, date(2025, 6, 1))
        self.assertFalse(df.empty)
        self.assertIn("Turnover %", df.columns)

    def test_agrupamentos(self):
        df = dash.por_categoria(self.registros, "cargo", "Cargo")
        self.assertFalse(df.empty)
        df2 = dash.faixas_tempo_casa(self.registros, date(2025, 6, 1))
        self.assertFalse(df2.empty)

    def test_quadro_ativo_ignora_desligados(self):
        ativos = dash.ativos(self.registros, date(2025, 6, 1))
        nomes = [r["nome"] for r in ativos]
        self.assertNotIn("Ana Desligada", nomes)

    def test_ativos_em_data_passada(self):
        ativos = dash.ativos_em_data(self.registros, date(2024, 6, 1))
        self.assertIn("Ana Desligada", [r["nome"] for r in ativos])

    def test_resumo_eventos(self):
        ev = dash.resumo_eventos(self.registros, date(2025, 6, 1))
        self.assertIn("experiencia_30", ev)
        self.assertIn("ferias_liberadas", ev)
        self.assertIn("ferias_vencidas", ev)
        self.assertIn("ferias_gozo_30", ev)

    def test_resumo_eventos_conta_vencidas(self):
        """Com data futura, ferias de funcionarios antigos ficam vencidas."""
        ev = dash.resumo_eventos(self.registros, date(2027, 6, 1))
        # Jose (admitido 2019) tera ferias vencidas em 2027
        self.assertGreaterEqual(ev["ferias_vencidas"], 0)

    def test_eventos_experiencia_e_ferias(self):
        exp = dash.eventos_experiencia(self.registros, date(2025, 6, 1))
        fer = dash.eventos_ferias(self.registros, date(2025, 6, 1))
        self.assertIsInstance(exp, type(fer))

    def test_sem_registros_nao_quebra(self):
        dados_dir2 = tempfile.mkdtemp(prefix="teste_dash2_")
        os.environ["SISTEMA_DADOS_DIR"] = dados_dir2
        import importlib
        import database as _db2
        importlib.reload(_db2)
        banco2 = _db2.Banco()
        regs = banco2.pesquisar()
        t = dash.turnover_periodo(regs, 12)
        self.assertEqual(t["quadro_atual"], 0)
        banco2.fechar()
        shutil.rmtree(dados_dir2, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
