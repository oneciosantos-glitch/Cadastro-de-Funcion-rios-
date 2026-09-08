"""Tema visual do Sistema de Cadastro de Funcionarios (versao web).

Inclui CSS, helpers para cabecalho, cartoes, tags, tabela estilizada
e paleta de cores dos graficos.
"""

from html import escape

import streamlit as st

# ---------- paleta ----------
AZUL = "#2E86AB"
AREIA = "#E8C547"
VERDE = "#4CAF50"
VERMELHO = "#E74C3C"
AZUL_CLARO = "#5DADE2"
CINZA = "#95A5A6"
ROXO = "#8E44AD"
LARANJA = "#E67E22"

CORES_GRAFICO = [AZUL, AREIA, VERDE, VERMELHO, AZUL_CLARO]

_CSS = """<style>
/* ----- fundo principal ----- */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
}

/* ----- cartao / card ----- */
div.cartao {
    background: #ffffff;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 14px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border: 1px solid #eaeaea;
}
div.cartao h4 {
    margin: 0 0 12px 0;
    font-size: 17px;
    font-weight: 700;
    color: #2c3e50;
}
div.cartao .linha {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid #f0f0f0;
    font-size: 14px;
}
div.cartao .linha:last-child { border-bottom: none; }
div.cartao .rot { color: #7f8c8d; font-weight: 500; }
div.cartao .val { color: #2c3e50; font-weight: 600; }

/* ----- cartao de evento (contrato / ferias / afastamento) ----- */
div.cartao-evento {
    background: #ffffff;
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 18px;
    box-shadow: 0 3px 14px rgba(0,0,0,0.07);
    border-left: 5px solid var(--cor-barra, #2E86AB);
}
div.cartao-evento h3 {
    margin: 0 0 14px 0;
    font-size: 18px;
    font-weight: 700;
    color: #2c3e50;
    display: flex;
    align-items: center;
    gap: 8px;
}
div.cartao-evento .campo {
    display: flex;
    align-items: baseline;
    padding: 7px 0;
    border-bottom: 1px solid #f0f0f0;
    font-size: 14px;
}
div.cartao-evento .campo:last-child { border-bottom: none; }
div.cartao-evento .campo .lbl {
    color: #7f8c8d;
    font-weight: 500;
    min-width: 170px;
    flex-shrink: 0;
}
div.cartao-evento .campo .vlr {
    color: #2c3e50;
    font-weight: 600;
    flex-grow: 1;
}
div.cartao-evento .situacao {
    margin-top: 10px;
    padding: 8px 14px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
    display: inline-block;
}
div.cartao-evento .situacao.ok {
    background: #e9f7ee;
    color: #1b7a2e;
}
div.cartao-evento .situacao.alerta {
    background: #fdf1dc;
    color: #a67c00;
}
div.cartao-evento .situacao.info {
    background: #eaf2fb;
    color: #2471a3;
}
div.cartao-evento .situacao.perigo {
    background: #fdecea;
    color: #c0392b;
}
div.cartao-evento .situacao.roxo {
    background: #f4ecf7;
    color: #6c3483;
}
div.cartao-evento .barra-progresso {
    margin-top: 12px;
    background: #ecf0f1;
    border-radius: 8px;
    height: 10px;
    overflow: hidden;
}
div.cartao-evento .barra-progresso .preenchimento {
    height: 100%;
    border-radius: 8px;
    background: linear-gradient(90deg, var(--cor-barra, #2E86AB), var(--cor-barra-clara, #5DADE2));
    transition: width 0.4s;
}

/* ----- prazo de experiencia com data ----- */
div.cartao-prazo {
    background: #ffffff;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    border-left: 4px solid var(--cor-barra, #E8C547);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
}
div.cartao-prazo .prazo-dias {
    font-weight: 700;
    color: #2c3e50;
    font-size: 18px;
}
div.cartao-prazo .prazo-data {
    color: #7f8c8d;
    font-weight: 500;
}
div.cartao-prazo .prazo-status {
    padding: 3px 10px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 12px;
}
div.cartao-prazo .prazo-status.ativo {
    background: #eaf2fb;
    color: #2471a3;
}
div.cartao-prazo .prazo-status.alerta {
    background: #fdf1dc;
    color: #a67c00;
}
div.cartao-prazo .prazo-status.vencido {
    background: #fdecea;
    color: #c0392b;
}

/* ----- tag ----- */
div.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 4px;
}
.tag-verde  { background: #e9f7ee; color: #1b7a2e; }
.tag-vermelho { background: #fdecea; color: #c0392b; }
.tag-amarelo { background: #fdf1dc; color: #a67c00; }
.tag-azul   { background: #eaf2fb; color: #2471a3; }
.tag-cinza  { background: #f0f0f0; color: #7f8c8d; }
.tag-roxo   { background: #f4ecf7; color: #6c3483; }

/* ----- cabecalho ----- */
div.cabecalho {
    background: linear-gradient(135deg, #2E86AB 0%, #1a6d8e 100%);
    border-radius: 14px;
    padding: 24px 30px;
    margin-bottom: 20px;
    color: #ffffff;
}
div.cabecalho h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
}
div.cabecalho p {
    margin: 4px 0 0 0;
    font-size: 14px;
    opacity: 0.85;
}

/* ----- metricas com fundo ----- */
[data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #7f8c8d !important;
}

/* ----- sidebar ----- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
}
section[data-testid="stSidebar"] .stRadio label {
    color: #ecf0f1 !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] .stCaption {
    color: #bdc3c7 !important;
}

/* ----- alerta vencida removido (usuario nao quer ver vencidas) ----- */

/* ----- alerta gozo proximo (30 dias) ----- */
div.alerta-ferias-gozo-proximo {
    background: linear-gradient(135deg, #fdf1dc 0%, #fce9c7 100%);
    border: 2px solid #E8C547;
    border-radius: 14px;
    padding: 20px 26px;
    margin-bottom: 18px;
    box-shadow: 0 3px 14px rgba(232, 197, 71, 0.18);
}
div.alerta-ferias-gozo-proximo h3 {
    margin: 0 0 10px 0;
    font-size: 20px;
    font-weight: 700;
    color: #a67c00;
    display: flex;
    align-items: center;
    gap: 10px;
}
div.alerta-ferias-gozo-proximo .detalhe {
    font-size: 14px;
    color: #5d4e00;
    padding: 6px 0;
    border-bottom: 1px solid rgba(232, 197, 71, 0.25);
}
div.alerta-ferias-gozo-proximo .detalhe:last-child {
    border-bottom: none;
}
div.alerta-ferias-gozo-proximo .detalhe .lbl {
    color: #8a7000;
    font-weight: 500;
    min-width: 160px;
    display: inline-block;
}
div.alerta-ferias-gozo-proximo .detalhe .vlr {
    color: #1a1a1a;
    font-weight: 700;
}

/* ----- alerta ferias 4 meses ----- */
div.alerta-ferias-4-meses {
    background: linear-gradient(135deg, #fef3e2 0%, #fde8c8 100%);
    border: 2px solid #F39C12;
    border-radius: 14px;
    padding: 20px 26px;
    margin-bottom: 18px;
    box-shadow: 0 3px 14px rgba(243, 156, 18, 0.18);
}
div.alerta-ferias-4-meses h3 {
    margin: 0 0 10px 0;
    font-size: 20px;
    font-weight: 700;
    color: #e67e22;
    display: flex;
    align-items: center;
    gap: 10px;
}
div.alerta-ferias-4-meses .detalhe {
    font-size: 14px;
    color: #6e4a00;
    padding: 6px 0;
    border-bottom: 1px solid rgba(243, 156, 18, 0.2);
}
div.alerta-ferias-4-meses .detalhe:last-child {
    border-bottom: none;
}
div.alerta-ferias-4-meses .detalhe .lbl {
    color: #a05e00;
    font-weight: 500;
    min-width: 160px;
    display: inline-block;
}
div.alerta-ferias-4-meses .detalhe .vlr {
    color: #1a1a1a;
    font-weight: 700;
}

/* ----- secao de todos os prazos ----- */
div.secao-todos-prazos {
    background: #f0f4f8;
    border: 1px solid #c5d4e0;
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 12px;
}
div.secao-todos-prazos h4 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    color: #2c5282;
}

/* ----- tabela (Styler wrapper) ----- */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
}

/* ----- SaaS table overrides ----- */
.stDataFrame table {
    border-collapse: collapse !important;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
    font-size: 13px !important;
}
.stDataFrame thead th {
    background: #F5F5F5 !important;
    color: #424242 !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-bottom: 2px solid #E0E0E0 !important;
    padding: 10px 12px !important;
}
.stDataFrame tbody td {
    border: none !important;
    border-bottom: 1px solid #ECECEC !important;
    padding: 8px 12px !important;
}
.stDataFrame tbody tr:hover {
    background-color: #F5F5F5 !important;
}
</style>"""


def aplicar():
    st.markdown(_CSS, unsafe_allow_html=True)


def cabecalho(titulo, subtitulo=""):
    html = f"<div class='cabecalho'><h1>{escape(titulo)}</h1>"
    if subtitulo:
        html += f"<p>{escape(subtitulo)}</p>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def marca(nome="Cadastro de Funcionarios",
           detalhe="Gestao de pessoal e eventos trabalhistas"):
    st.sidebar.markdown(
        f"<div style='text-align:center;padding:12px 0'>"
        f"<span style='font-size:18px;font-weight:700;color:#ecf0f1'>"
        f"{escape(nome)}</span><br>"
        f"<span style='font-size:11px;color:#bdc3c7'>"
        f"{escape(detalhe)}</span></div>",
        unsafe_allow_html=True)


def tag(texto, tipo="neutro"):
    cores = {"verde": "tag-verde", "vermelho": "tag-vermelho",
             "amarelo": "tag-amarelo", "azul": "tag-azul",
             "neutro": "tag-cinza", "roxo": "tag-roxo"}
    cls = cores.get(tipo, "tag-cinza")
    st.markdown(f"<div class='tag {cls}'>{escape(texto)}</div>",
                unsafe_allow_html=True)


def cartao(titulo, itens, etiqueta=None):
    """Bloco branco com pares rotulo/valor. `itens` = lista de tuplas."""
    linhas = "".join(
        f"<div class='linha'><span class='rot'>{escape(str(r))}</span>"
        f"<span class='val'>{escape(str(v))}</span></div>" for r, v in itens)
    topo = f"<h4>{escape(titulo)}</h4>" if titulo else ""
    fim = f"<div style='margin-top:10px'>{etiqueta}</div>" if etiqueta else ""
    st.markdown(f"<div class='cartao'>{topo}{linhas}{fim}</div>",
                unsafe_allow_html=True)


def cartao_evento(titulo, icon, campos, situacao_texto, situacao_tipo,
                   cor_barra, cor_barra_clara, progresso_pct=None):
    """Cartao de evento (contrato de experiencia, ferias, afastamento etc).

    campos = lista de tuplas (rotulo, valor)
    situacao_tipo = 'ok' | 'alerta' | 'info' | 'perigo' | 'roxo'
    progresso_pct = 0.0-1.0 ou None (sem barra)
    """
    campos_html = "".join(
        f"<div class='campo'><span class='lbl'>{escape(str(r))}</span>"
        f"<span class='vlr'>{escape(str(v))}</span></div>"
        for r, v in campos)

    sit_cls = {
        "ok": "ok", "alerta": "alerta", "info": "info",
        "perigo": "perigo", "roxo": "roxo"
    }.get(situacao_tipo, "info")

    sit_html = (f"<div class='situacao {sit_cls}'>"
                f"{escape(situacao_texto)}</div>")

    barra_html = ""
    if progresso_pct is not None:
        pct = max(0, min(progresso_pct * 100, 100))
        barra_html = (
            f"<div class='barra-progresso'>"
            f"<div class='preenchimento' style='"
            f"--cor-barra:{cor_barra};--cor-barra-clara:{cor_barra_clara};"
            f"width:{pct:.1f}%'></div></div>")

    st.markdown(
        f"<div class='cartao-evento' style='"
        f"--cor-barra:{cor_barra};--cor-barra-clara:{cor_barra_clara}'>"
        f"<h3>{icon} {escape(titulo)}</h3>"
        f"{campos_html}{sit_html}{barra_html}</div>",
        unsafe_allow_html=True)


def cartao_prazo_experiencia(prazo_dias, data_fim, dias_restantes, status_tipo):
    """Cartao compacto para cada prazo de experiencia com data."""
    status_cls = {"ativo": "ativo", "alerta": "alerta", "vencido": "vencido"}
    status_texto = {"ativo": "Em curso", "alerta": "Vencendo", "vencido": "Encerrado"}
    cls = status_cls.get(status_tipo, "ativo")
    txt = status_texto.get(status_tipo, "Em curso")
    st.markdown(
        f"<div class='cartao-prazo' style='--cor-barra:"
        f"{AREIA if status_tipo == 'alerta' else VERMELHO if status_tipo == 'vencido' else AZUL}'>"
        f"<div><span class='prazo-dias'>{prazo_dias} dias</span>"
        f"<span class='prazo-data'> &rarr; {escape(str(data_fim))}</span></div>"
        f"<div><span style='font-size:13px;color:#7f8c8d'>{dias_restantes}d restantes</span> "
        f"<span class='prazo-status {cls}'>{txt}</span></div></div>",
        unsafe_allow_html=True)


# alerta_ferias_vencida REMOVIDO — usuario nao quer ver ferias vencidas no dashboard


def alerta_ferias_gozo_proximo(funcionario, campos):
    """Cartao amarelo para ferias com prazo de gozo vencendo em ate 30 dias."""
    linhas = "".join(
        f"<div class='detalhe'><span class='lbl'>{escape(str(r))}</span>"
        f"<span class='vlr'>{escape(str(v))}</span></div>"
        for r, v in campos)
    st.markdown(
        f"<div class='alerta-ferias-gozo-proximo'>"
        f"<h3>\u26A0\uFE0F Prazo de gozo vencendo em ate 30 dias</h3>"
        f"<div class='detalhe'><span class='lbl'>Funcionario</span>"
        f"<span class='vlr'>{escape(funcionario)}</span></div>"
        f"{linhas}</div>",
        unsafe_allow_html=True)


def alerta_ferias_4_meses(funcionario, campos):
    """Cartao laranja para alerta de 4 meses antes da liberacao de ferias."""
    linhas = "".join(
        f"<div class='detalhe'><span class='lbl'>{escape(str(r))}</span>"
        f"<span class='vlr'>{escape(str(v))}</span></div>"
        for r, v in campos)
    st.markdown(
        f"<div class='alerta-ferias-4-meses'>"
        f"<h3>\U0001F7E1 Alerta: liberacao de ferias em ate 4 meses</h3>"
        f"<div class='detalhe'><span class='lbl'>Funcionario</span>"
        f"<span class='vlr'>{escape(funcionario)}</span></div>"
        f"{linhas}</div>",
        unsafe_allow_html=True)


def secao_todos_prazos(titulo="Todos os prazos legais de experiencia"):
    """Cabecalho visual para a secao de todos os prazos."""
    st.markdown(
        f"<div class='secao-todos-prazos'><h4>"
        f"\U0001F4CC {escape(titulo)}</h4></div>",
        unsafe_allow_html=True)


def estilo_tabela(df, coluna_ferias="Ferias", coluna_exp="Status experiencia"):
    """Pinta as linhas conforme os eventos trabalhistas (sem vencida)."""
    def pintar(linha):
        cor = ""
        exp = str(linha.get(coluna_exp, ""))
        fer = str(linha.get(coluna_ferias, ""))
        if "atencao" in exp.lower() or "vence" in exp.lower() or "Encerrado" in exp:
            cor = "background-color: #FDF1DC"
        elif "liberada" in fer.lower():
            cor = "background-color: #E9F7EE"
        elif "alerta" in fer.lower():
            cor = "background-color: #FFF3E0"
        return [cor] * len(linha)

    return df.style.apply(pintar, axis=1)


def estilo_tabela_saas(df, tipo="experiencia"):
    """Estilo SaaS minimalista: zebra rows, cores de status, bordas finas.

    tipo = 'experiencia' | 'ferias'
    Retorna Styler pronto para st.dataframe().
    Compativel com pandas 1.x e 2.x+.

    Situacoes possiveis (experiencia):
      - "Atencao - vence em X dia(s)"
      - "Encerrado"
      - "Dentro do prazo (X dias restantes)"

    Situacoes possiveis (ferias):
      - "Alerta - liberacao em X dia(s)"   (alerta 4 meses)
      - "Liberada - Xd para gozo"         (liberada)
      - "Proxima de liberar"
      - "Em curso"
    """
    if df.empty:
        return df.style

    col_status = "Situacao"

    # --- cores de fundo por status ---
    def _cor_linha(linha):
        sit = str(linha.get(col_status, "")).lower()
        if "alerta" in sit or "atencao" in sit:
            bg = "#FFF3E0"
        elif "liberada" in sit:
            bg = "#E8F5E9"
        elif "encerrado" in sit:
            bg = "#F5F5F5"
        elif "proxima" in sit:
            bg = "#FFF8E1"
        else:
            bg = "#FFFFFF"
        return [f"background-color: {bg}"] * len(linha)

    # --- cor do texto da situacao ---
    def _txt_status(val):
        v = str(val).lower()
        if "alerta" in v or "atencao" in v:
            return "color: #E65100; font-weight: bold"
        if "liberada" in v:
            return "color: #2E7D32; font-weight: bold"
        if "encerrado" in v:
            return "color: #757575"
        if "dentro do prazo" in v:
            return "color: #1565C0"
        if "proxima" in v:
            return "color: #F57F17; font-weight: bold"
        return ""

    # --- monta Styler com maxima compatibilidade ---
    styler = df.style.apply(_cor_linha, axis=1)

    # Element-wise: .map() (pandas >= 2.0) ou .applymap() (pandas < 2.0)
    if col_status in df.columns:
        _elem_fn = getattr(styler, "map", None) or getattr(styler, "applymap")
        if _elem_fn is not None:
            styler = _elem_fn(_txt_status, subset=[col_status])

    styler = styler.set_properties(**{
        "border": "none",
        "border-bottom": "1px solid #E0E0E0",
        "padding": "8px 12px",
        "font-size": "13px",
        "font-family": "'Inter', 'Segoe UI', system-ui, sans-serif",
    }).set_table_styles([
        {"selector": "th", "props": [
            ("background-color", "#F5F5F5"),
            ("color", "#424242"),
            ("font-weight", "600"),
            ("font-size", "12px"),
            ("text-transform", "uppercase"),
            ("letter-spacing", "0.5px"),
            ("border-bottom", "2px solid #E0E0E0"),
            ("padding", "10px 12px"),
        ]},
        {"selector": "td", "props": [
            ("border", "none"),
            ("border-bottom", "1px solid #ECECEC"),
            ("padding", "8px 12px"),
        ]},
        {"selector": "", "props": [
            ("border-collapse", "collapse"),
            ("width", "100%"),
        ]},
    ])

    return styler
