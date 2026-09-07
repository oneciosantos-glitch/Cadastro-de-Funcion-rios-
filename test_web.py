"""Testes da interface Streamlit (AppTest).
Requer streamlit >= 1.31.
Execute: python -m unittest test_web -v
"""

import os
import shutil
import tempfile
import unittest
from datetime import date

DADOS_TMP = tempfile.mkdtemp(prefix="teste_web_")
os.environ["SISTEMA_DADOS_DIR"] = DADOS_TMP

from database import Banco


def _preencher_banco():
    banco = Banco()
    banco.inserir({"matricula": "0001", "nome": "Teste Web",
                   "rg": "", "cpf": "", "telefone": "",
                   "admissao": "2025-01-10", "loja": "Loja 01 - Matriz",
                   "situacao": "Ativo", "cargo": "Vendedor",
                   "experiencia_dias": 45, "foto": None,
                   "observacao": ""})
    banco.fechar()


try:
    from streamlit.testing.v1 import AppTest
    HAS_APP_TEST = True
except ImportError:
    HAS_APP_TEST = False


@unittest.skipUnless(HAS_APP_TEST, "streamlit AppTest nao disponivel")
class TestWebDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _preencher_banco()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(DADOS_TMP, ignore_errors=True)

    def test_dashboard_carrega(self):
        at = AppTest.from_file("streamlit_app.py")
        at.run(timeout=60)
        self.assertNotEqual(len(at.main), 0)

    def test_pagina_consultar(self):
        at = AppTest.from_file("streamlit_app.py")
        at.run(timeout=60)
        # Navegar para pagina Consultar
        at.sidebar.radio[0].set_value("\U0001F50D Consultar")
        at.run(timeout=60)
        self.assertNotEqual(len(at.main), 0)

    def test_pagina_eventos(self):
        at = AppTest.from_file("streamlit_app.py")
        at.run(timeout=60)
        at.sidebar.radio[0].set_value("\U0001F4CB Eventos")
        at.run(timeout=60)
        self.assertNotEqual(len(at.main), 0)


if __name__ == "__main__":
    unittest.main()
