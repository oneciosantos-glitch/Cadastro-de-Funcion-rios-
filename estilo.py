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

/* ----- cartao de evento (contrato / ferias) ----- */
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

/* ----- alerta de ferias vencida ----- */
div.alerta-ferias-vencida {
    background: linear-gradient(135deg, #fdecea 0%, #f9e0dc 100%);
    border: 2px solid #E74C3C;
    border-radius: 14px;
    padding: 20px 26px;
    margin-bottom: 18px;
    box-shadow: 0 3px 16px rgba(231, 76, 60, 0.18);
}
div.alerta-ferias-vencida h3 {
    margin: 0 0 10px 0;
    font-size: 20px;
    font-weight: 700;
    color: #c0392b;
    display: flex;
    align-items: center;
    gap: 10px;
}
div.alerta-ferias-vencida .detalhe {
    font-size: 14px;
    color: #6b1a1a;
    padding: 6px 0;
    border-bottom: 1px solid rgba(231, 76, 60, 0.15);
}
div.alerta-ferias-vencida .detalhe:last-child {
    border-bottom: none;
}
div.alerta-ferias-vencida .detalhe .lbl {
    color: #943126;
    font-weight: 500;
    min-width: 160px;
    display: inline-block;
}
div.alerta-ferias-vencida .detalhe .vlr {
    color: #1a1a1a;
    font-weight: 700;
}
div.alerta-ferias-vencida .icone-pulso {
    display: inline-block;
    animation: pulso_vermelho 1.5s ease-in-out infinite;
}
@keyframes pulso_vermelho {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.55; transform: scale(1.18); }
}

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

/* ----- tabela (Styler wrapper) ----- */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
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
             "neutro": "tag-cinza"}
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
    """Cartao de evento (contrato de experiencia ou ferias).

    campos = lista de tuplas (rotulo, valor)
    situacao_tipo = 'ok' | 'alerta' | 'info' | 'perigo'
    progresso_pct = 0.0-1.0 ou None (sem barra)
    """
    campos_html = "".join(
        f"<div class='campo'><span class='lbl'>{escape(str(r))}</span>"
        f"<span class='vlr'>{escape(str(v))}</span></div>"
        for r, v in campos)

    sit_cls = {
        "ok": "ok", "alerta": "alerta", "info": "info",
        "perigo": "perigo"
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


def alerta_ferias_vencida(funcionario, campos):
    """Cartao vermelho pulsante para ferias vencidas.

    funcionario = str com nome/matricula
    campos = lista de tuplas (rotulo, valor)
    """
    linhas = "".join(
        f"<div class='detalhe'><span class='lbl'>{escape(str(r))}</span>"
        f"<span class='vlr'>{escape(str(v))}</span></div>"
        for r, v in campos)
    st.markdown(
        f"<div class='alerta-ferias-vencida'>"
        f"<h3><span class='icone-pulso'>\U0001F6A8</span> "
        f"Ferias VENCIDA</h3>"
        f"<div class='detalhe'><span class='lbl'>Funcionario</span>"
        f"<span class='vlr'>{escape(funcionario)}</span></div>"
        f"{linhas}</div>",
        unsafe_allow_html=True)


def alerta_ferias_gozo_proximo(funcionario, campos):
    """Cartao amarelo para ferias com prazo de gozo vencendo em ate 30 dias.

    funcionario = str com nome/matricula
    campos = lista de tuplas (rotulo, valor)
    """
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


def estilo_tabela(df, coluna_ferias="Ferias", coluna_exp="Status experiencia",
                   coluna_vencida="Vencida"):
    """Pinta as linhas conforme os eventos trabalhistas."""
    def pintar(linha):
        cor = ""
        venc = str(linha.get(coluna_vencida, ""))
        exp = str(linha.get(coluna_exp, ""))
        fer = str(linha.get(coluna_ferias, ""))
        if venc == "Sim":
            cor = "background-color: #FDECEA"
        elif "atencao" in exp.lower() or "vence" in exp.lower() or "Encerrado" in exp:
            cor = "background-color: #FDF1DC"
        elif "LIBERADA" in fer:
            cor = "background-color: #E9F7EE"
        return [cor] * len(linha)

    return df.style.apply(pintar, axis=1)
