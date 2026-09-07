"""Banco de dados SQLite para o sistema de funcionarios."""

import os
import shutil
import sqlite3
from datetime import date

def _descobrir_dados_dir():
    """Descobre um diretorio gravavel para o banco de dados.

    Ordem de prioridade:
    1. SISTEMA_DADOS_DIR (variavel de ambiente)
    2. /mount/data/dados  (Streamlit Cloud – disco efemero gravavel)
    3. <pasta do script>/dados  (execucao local)
    4. /tmp/sistema_funcionarios/dados (fallback universal)
    """
    env_dir = os.environ.get("SISTEMA_DADOS_DIR")
    if env_dir:
        return env_dir

    candidatos = [
        os.path.join("/mount", "data", "dados"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados"),
        os.path.join("/tmp", "sistema_funcionarios", "dados"),
    ]
    for c in candidatos:
        try:
            os.makedirs(c, exist_ok=True)
            teste = os.path.join(c, ".write_test")
            with open(teste, "w") as f:
                f.write("ok")
            os.remove(teste)
            return c
        except (OSError, PermissionError):
            continue

    # Ultimo recurso absoluto
    fallback = os.path.join("/tmp", "sistema_funcionarios", "dados")
    os.makedirs(fallback, exist_ok=True)
    return fallback


DADOS_DIR = _descobrir_dados_dir()
DB_PATH = os.path.join(DADOS_DIR, "funcionarios.db")
FOTOS_DIR = os.path.join(DADOS_DIR, "fotos")


class Banco:
    """Acesso ao banco SQLite com WAL para multiusuario."""

    def __init__(self, multiusuario=False):
        global DADOS_DIR, DB_PATH, FOTOS_DIR
        self.multiusuario = multiusuario
        # Tenta conectar no caminho principal; se falhar, usa /tmp
        try:
            os.makedirs(DADOS_DIR, exist_ok=True)
            os.makedirs(FOTOS_DIR, exist_ok=True)
            self.conn = sqlite3.connect(DB_PATH, timeout=30,
                                         check_same_thread=False)
        except (sqlite3.OperationalError, OSError, PermissionError):
            DADOS_DIR = os.path.join("/tmp", "sistema_funcionarios", "dados")
            DB_PATH = os.path.join(DADOS_DIR, "funcionarios.db")
            FOTOS_DIR = os.path.join(DADOS_DIR, "fotos")
            os.makedirs(DADOS_DIR, exist_ok=True)
            os.makedirs(FOTOS_DIR, exist_ok=True)
            self.conn = sqlite3.connect(DB_PATH, timeout=30,
                                         check_same_thread=False)
        if multiusuario:
            self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.row_factory = sqlite3.Row
        self._criar_tabelas()
        self._migrar()

    def _criar_tabelas(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                rg TEXT DEFAULT '',
                cpf TEXT DEFAULT '',
                telefone TEXT DEFAULT '',
                admissao TEXT NOT NULL,
                loja TEXT DEFAULT '',
                situacao TEXT DEFAULT 'Ativo',
                cargo TEXT DEFAULT '',
                experiencia_dias INTEGER,
                foto TEXT,
                observacao TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS combos (
                tipo TEXT NOT NULL,
                valor TEXT NOT NULL,
                UNIQUE(tipo, valor)
            );
        """)
        self.conn.commit()

    def _migrar(self):
        """Adiciona coluna demissao se nao existir (compatibilidade)."""
        cols = [r[1] for r in self.conn.execute(
            "PRAGMA table_info(funcionarios)").fetchall()]
        if "demissao" not in cols:
            self.conn.execute(
                "ALTER TABLE funcionarios ADD COLUMN demissao TEXT DEFAULT NULL")
            self.conn.commit()

    # ---- combos ----

    COMBOS_PADRAO = {
        "loja": ["Loja 01 - Matriz", "Loja 02 - Centro"],
        "situacao": ["Ativo", "Desligado", "Ferias", "Afastado", "Licenca"],
        "cargo": ["Vendedor", "Gerente", "Caixa", "Estoquista", "Auxiliar"],
    }

    def listar_combo(self, tipo):
        self._garantir_combos_padrao(tipo)
        rows = self.conn.execute(
            "SELECT valor FROM combos WHERE tipo=? ORDER BY valor",
            (tipo,)).fetchall()
        return [r["valor"] for r in rows]

    def add_combo(self, tipo, valor):
        self.conn.execute(
            "INSERT OR IGNORE INTO combos(tipo, valor) VALUES(?, ?)",
            (tipo, valor.strip()))
        self.conn.commit()

    def _garantir_combos_padrao(self, tipo):
        for v in self.COMBOS_PADRAO.get(tipo, []):
            self.conn.execute(
                "INSERT OR IGNORE INTO combos(tipo, valor) VALUES(?, ?)",
                (tipo, v))
        self.conn.commit()

    # ---- CRUD ----

    def pesquisar(self, termo="", loja="", situacao="", cargo=""):
        sql = "SELECT * FROM funcionarios WHERE 1=1"
        params = []
        if termo:
            sql += " AND (matricula LIKE ? OR nome LIKE ? OR cpf LIKE ? " \
                   "OR rg LIKE ? OR telefone LIKE ?)"
            t = f"%{termo}%"
            params += [t, t, t, t, t]
        if loja:
            sql += " AND loja = ?"
            params.append(loja)
        if situacao:
            sql += " AND situacao = ?"
            params.append(situacao)
        if cargo:
            sql += " AND cargo = ?"
            params.append(cargo)
        sql += " ORDER BY nome"
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def obter(self, id_):
        row = self.conn.execute(
            "SELECT * FROM funcionarios WHERE id=?", (id_,)).fetchone()
        return dict(row) if row else None

    def inserir(self, dados):
        cols = ", ".join(dados.keys())
        placeholders = ", ".join("?" for _ in dados)
        self.conn.execute(
            f"INSERT INTO funcionarios({cols}) VALUES({placeholders})",
            list(dados.values()))
        self.conn.commit()

    def atualizar(self, id_, dados):
        sets = ", ".join(f"{k}=?" for k in dados)
        self.conn.execute(
            f"UPDATE funcionarios SET {sets} WHERE id=?",
            list(dados.values()) + [id_])
        self.conn.commit()

    def excluir(self, id_):
        reg = self.obter(id_)
        if reg and reg.get("foto"):
            self.remover_foto(reg["foto"])
        self.conn.execute("DELETE FROM funcionarios WHERE id=?", (id_,))
        self.conn.commit()

    def matricula_existe(self, matricula, exceto_id=None):
        sql = "SELECT 1 FROM funcionarios WHERE matricula=?"
        params = [matricula]
        if exceto_id:
            sql += " AND id != ?"
            params.append(exceto_id)
        return self.conn.execute(sql, params).fetchone() is not None

    def proxima_matricula(self):
        row = self.conn.execute(
            "SELECT MAX(CAST(matricula AS INTEGER)) FROM funcionarios"
        ).fetchone()
        if row and row[0] is not None:
            return str(int(row[0]) + 1).zfill(4)
        return "0001"

    # ---- fotos ----

    def caminho_foto(self, nome_relativo):
        if not nome_relativo:
            return None
        caminho = os.path.join(FOTOS_DIR, nome_relativo)
        return caminho if os.path.isfile(caminho) else None

    def salvar_foto(self, caminho_origem):
        """Copia um arquivo de foto para a pasta dados/fotos/."""
        import uuid
        ext = os.path.splitext(caminho_origem)[1].lower() or ".png"
        nome = f"{uuid.uuid4().hex}{ext}"
        destino = os.path.join(FOTOS_DIR, nome)
        shutil.copy2(caminho_origem, destino)
        return nome

    def salvar_foto_bytes(self, dados_bytes, nome_original):
        """Salva foto recebida como bytes (upload web)."""
        import uuid
        ext = os.path.splitext(nome_original)[1].lower() or ".png"
        nome = f"{uuid.uuid4().hex}{ext}"
        destino = os.path.join(FOTOS_DIR, nome)
        with open(destino, "wb") as fp:
            fp.write(dados_bytes)
        return nome

    def remover_foto(self, nome_relativo):
        caminho = self.caminho_foto(nome_relativo)
        if caminho:
            os.remove(caminho)

    def fechar(self):
        self.conn.close()
