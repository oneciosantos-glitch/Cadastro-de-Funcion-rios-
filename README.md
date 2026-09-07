# Sistema de Cadastro de Funcionarios

Cadastro completo de funcionarios com controle de experiencia e ferias,
dashboard com turnover, exportacao Excel e acesso multiusuario.

## Funcionalidades

- **CRUD com foto** – cadastro, edicao e exclusao; foto anexavel (camera ou arquivo)
- **Contratos de experiencia** – 30 / 45 / 60 / 90 dias com alerta de vencimento
- **Ferias** – regras CLT: 20 de 24 meses (<1 ano) e 8 de 12 meses (>1 ano)
- **Dashboard** – turnover mensal, por loja, por cargo, tempo de casa
- **Exportacao** – planilha Excel (.xlsx) ou CSV
- **Login** – senha via `.streamlit/secrets.toml` ou variavel `SISTEMA_SENHA`
- **Multiusuario** – SQLite em modo WAL, seguro para varios acessos simultaneos

## Instalacao

```bash
pip install -r requirements.txt
```

## Uso

```bash
streamlit run streamlit_app.py
```

Acesse no navegador: `http://localhost:8501`

## Seguranca

Copie o arquivo de exemplo e defina sua senha:

```bash
cp .streamlit/secrets.toml.exemplo .streamlit/secrets.toml
# edite secrets.toml e troque "suaSenhaAqui" pela senha desejada
```

Ou defina a senha no ambiente:

```bash
export SISTEMA_SENHA="suaSenha"
```

Sem nenhuma senha configurada, qualquer pessoa com o link podera acessar.

## Estrutura de Pastas

```
sistema_funcionarios/
\u251c\u2500\u2500 streamlit_app.py       # Aplicativo web principal
\u251c\u2500\u2500 calculos.py             # Regras de negocio
\u251c\u2500\u2500 database.py             # Banco de dados SQLite
\u251c\u2500\u2500 dashboard.py            # Metricas e graficos
\u251c\u2500\u2500 exportador.py           # Exportacao Excel/CSV
\u251c\u2500\u2500 estilo.py               # Estilos visuais (cartoes, cores)
\u251c\u2500\u2500 test_sistema.py         # Testes de negocio
\u251c\u2500\u2500 test_dashboard.py       # Testes do dashboard
\u251c\u2500\u2500 test_web.py             # Testes da interface
\u251c\u2500\u2500 requirements.txt
\u251c\u2500\u2500 dados/                  # Banco + fotos (criado automaticamente)
\u2514\u2500\u2500 .streamlit/
    \u251c\u2500\u2500 config.toml
    \u251c\u2500\u2500 secrets.toml.exemplo
    \u2514\u2500\u2500 secrets.toml  (nao versionar!)
```

## Testes

```bash
python -m unittest test_sistema test_dashboard -v
```

## Regras de Ferias

| Tempo de casa | Periodo aquisitivo | Liberacao |
|---------------|--------------------|----------|
| Menos de 1 ano | 24 meses | 20 meses |
| 1 ano ou mais | 12 meses | 8 meses |

## Contratos de Experiencia

Prazos disponiveis: **30, 45, 60 e 90 dias** (conforme CLT).
O sistema alerta quando faltam 7 dias ou menos para o vencimento.
