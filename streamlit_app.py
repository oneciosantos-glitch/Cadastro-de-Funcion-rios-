"""Sistema de Cadastro de Funcionarios - versao web (Streamlit).

Use de qualquer lugar/dispositivo e compartilhe o link com sua equipe.
Execute local:  streamlit run streamlit_app.py

Sistema aberto: qualquer pessoa com o link pode acessar e alterar cadastros.
"""

import os
from datetime import date

import pandas as pd
import streamlit as st

import calculos as cal
import dashboard as dash
import exportador
import estilo
from database import Banco, DB_PATH

st.set_page_config(page_title="Cadastro de Funcionarios",
                   page_icon="\U0001F465", layout="wide")
estilo.aplicar()


@st.cache_resource
def get_banco():
    return Banco(multiusuario=True)




def linha_tabela(reg, hoje):
    adm = cal.parse_data(reg["admissao"])
    f = cal.calcular_ferias(adm, hoje)
    if reg["experiencia_dias"]:
        e = cal.contrato_experiencia(adm, reg["experiencia_dias"], hoje)
        exp = f"{e['prazo_dias']}d ate {cal.fmt(e['fim'])}"
        exp_sit = e["situacao"]
    else:
        exp, exp_sit = "-", "Sem contrato"
    return {
        "Matricula": reg["matricula"], "Funcionario": reg["nome"],
        "CPF": reg["cpf"] or "", "Telefone": reg["telefone"] or "",
        "Loja": reg["loja"] or "", "Cargo": reg["cargo"] or "",
        "Situacao": reg["situacao"] or "", "Admissao": cal.fmt(adm),
        "Experiencia": exp, "Status experiencia": exp_sit,
        "Ferias": f"{f['progresso']} - {f['situacao']}",
        "Foto": "Sim" if reg["foto"] else "Nao",
    }


def _opcoes(banco, registros):
    return {f"{r['matricula']} - {r['nome']}": r["id"] for r in registros}


def _filtros(banco, chave):
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    termo = c1.text_input("\U0001F50D Pesquisar", key=f"termo_{chave}",
                          placeholder="Matricula, nome, CPF, RG, telefone")
    loja = c2.selectbox("\U0001F3EA Loja", [""] + banco.listar_combo("loja"),
                        key=f"loja_{chave}")
    situacao = c3.selectbox("\U0001F4CB Situacao",
                           [""] + banco.listar_combo("situacao"),
                           key=f"sit_{chave}")
    cargo = c4.selectbox("\U0001F4BC Cargo",
                         [""] + banco.listar_combo("cargo"),
                         key=f"cargo_{chave}")
    return termo, loja, situacao, cargo


# ============================================================
# PAGINAS
# ============================================================


def pagina_consultar(banco):
    estilo.cabecalho("Consulta de funcionarios",
                    "Pesquise e filtre os cadastros")
    filtros = _filtros(banco, "consulta")
    tempo_real = st.toggle("\U0001F504 Atualizacao em tempo real (10s)",
                           value=True, help="Recarrega a lista a cada "
                           "10 segundos para mostrar o que outras pessoas "
                           "cadastraram.")

    def desenhar():
        hoje = date.today()
        registros = banco.pesquisar(*filtros)
        if not registros:
            st.info("\U0001F50D Nenhum funcionario encontrado.")
            return
        df = pd.DataFrame([linha_tabela(r, hoje) for r in registros])
        st.caption(f"{len(df)} registro(s) \u00B7 atualizado "
                   f"{pd.Timestamp.now():%H:%M:%S}")
        st.dataframe(estilo.estilo_tabela(df),
                     width="stretch", hide_index=True)

    if tempo_real:
        st.fragment(desenhar, run_every=10)()
    else:
        if st.button("\U0001F504 Atualizar agora"):
            pass
        desenhar()


def pagina_cadastro(banco):
    estilo.cabecalho("Cadastrar / Editar",
                    "Preencha os campos e anexe a foto")
    registros = banco.pesquisar()
    opcoes = _opcoes(banco, registros)
    escolha = st.selectbox("Selecionar registro",
                          ["\U0001F195 Novo cadastro"] + list(opcoes))
    reg = banco.obter(opcoes[escolha]) if escolha in opcoes else None

    combos = {t: banco.listar_combo(t) for t in ("loja", "situacao", "cargo")}

    def indice(lista, valor):
        return lista.index(valor) + 1 if valor in lista else 0

    # --- foto com visualizacao imediata (fora do formulario) ---
    st.subheader("\U0001F4F8 Foto")
    foto_atual = banco.caminho_foto(reg["foto"]) if reg else None
    cf1, cf2, cf3 = st.columns([2, 3, 1])
    nova_foto = cf2.file_uploader(
        "Anexar ou trocar a foto", key="f_foto",
        type=["png", "jpg", "jpeg", "gif", "bmp", "webp"],
        help="No celular voce pode tirar a foto pela camera.")
    excluir_foto = cf3.checkbox("Remover", key="f_remove_foto",
                                disabled=not foto_atual)
    if nova_foto is not None:
        cf1.image(nova_foto, width=220, caption="Nova foto")
        with st.expander("\U0001F50D Ver ampliada"):
            st.image(nova_foto, width="stretch")
    elif foto_atual:
        cf1.image(foto_atual, width=220, caption="Foto atual")
        with st.expander("\U0001F50D Ver ampliada"):
            st.image(foto_atual, width="stretch")
    else:
        cf1.info("\U0001F4F7 Sem foto")

    # --- formulario ---
    with st.form("cadastro", clear_on_submit=False):
        st.markdown("#### \U0001F4DD Dados cadastrais")
        c1, c2, c3, c4 = st.columns(4)
        matricula = c1.text_input(
            "Matricula *", key="f_matricula",
            value=reg["matricula"] if reg else banco.proxima_matricula())
        nome = c2.text_input("Funcionario *", key="f_nome",
                             value=reg["nome"] if reg else "")
        rg = c3.text_input("RG", key="f_rg",
                           value=(reg["rg"] or "") if reg else "")
        cpf = c4.text_input("CPF", key="f_cpf",
                            value=(reg["cpf"] or "") if reg else "")
        telefone = c1.text_input("Telefone", key="f_telefone",
                                 value=(reg["telefone"] or "") if reg else "")
        admissao = c2.date_input(
            "Admissao *", format="DD/MM/YYYY", key="f_admissao",
            value=cal.parse_data(reg["admissao"]) if reg else date.today(),
            min_value=date(1970, 1, 1), max_value=date(2100, 12, 31))

        opcoes_loja = [""] + combos["loja"] + ["Outra..."]
        idx_loja = indice(combos["loja"], reg["loja"] if reg else None)
        if idx_loja is None and reg and reg["loja"]:
            idx_loja = len(opcoes_loja) - 1  # "Outra..."
        sel_loja = c1.selectbox("\U0001F3EA Loja", opcoes_loja,
                               index=idx_loja if idx_loja is not None else 0)
        if sel_loja == "Outra...":
            loja = c1.text_input("Nome da Loja", key="f_loja_nova",
                                 value=reg["loja"] if reg and reg.get("loja") else "")
            if loja.strip() and loja.strip() not in combos["loja"]:
                banco.add_combo("loja", loja.strip())
        else:
            loja = sel_loja
        situacao = c2.selectbox(
            "\U0001F4CB Situacao", [""] + combos["situacao"],
            index=indice(combos["situacao"],
                         reg["situacao"] if reg else "Ativo"))
        opcoes_cargo = [""] + combos["cargo"] + ["Outro..."]
        idx_cargo = indice(combos["cargo"], reg["cargo"] if reg else None)
        if idx_cargo is None and reg and reg["cargo"]:
            idx_cargo = len(opcoes_cargo) - 1  # "Outro..."
        sel_cargo = c3.selectbox("\U0001F4BC Cargo", opcoes_cargo,
                                index=idx_cargo if idx_cargo is not None else 0)
        if sel_cargo == "Outro...":
            cargo = c3.text_input("Nome do Cargo", key="f_cargo_novo",
                                  value=reg["cargo"] if reg and reg.get("cargo") else "")
            if cargo.strip() and cargo.strip() not in combos["cargo"]:
                banco.add_combo("cargo", cargo.strip())
        else:
            cargo = sel_cargo

        prazos = ["Sem contrato"] + [f"{d} dias" for d in cal.PRAZOS_EXPERIENCIA]
        atual = (f"{reg['experiencia_dias']} dias"
                 if reg and reg["experiencia_dias"] else "Sem contrato")
        experiencia = c1.selectbox("\U0001F4DD Contrato de experiencia",
                                   prazos, index=prazos.index(atual))
        observacao = st.text_area(
            "\U0001F4AC Observacao",
            value=(reg["observacao"] or "") if reg else "")
        demissao = c4.date_input(
            "\U0001F4C5 Desligamento (vazio = ativo)", format="DD/MM/YYYY",
            key="f_demissao", value=cal.parse_data(reg["demissao"])
            if reg and reg["demissao"] else None,
            min_value=date(1970, 1, 1), max_value=date(2100, 12, 31),
            help="Preencha ao desligar o funcionario: e o que alimenta o "
                 "calculo de turnover no dashboard.")

        salvar = st.form_submit_button(
            ("\U0001F4BE Salvar alteracoes" if reg
             else "\U0001F195 Cadastrar"), type="primary")

    if salvar:
        erros = []
        if not matricula.strip() or not nome.strip():
            erros.append("Informe a matricula e o nome do funcionario.")
        if banco.matricula_existe(matricula.strip(),
                                  reg["id"] if reg else None):
            erros.append("Ja existe funcionario com esta matricula.")
        if cpf.strip() and not cal.cpf_valido(cpf):
            st.warning("CPF invalido - o registro foi salvo, confira o numero.")
        if erros:
            for e in erros:
                st.error(e)
            return

        foto = reg["foto"] if reg else None
        if excluir_foto and foto:
            banco.remover_foto(foto)
            foto = None
        if nova_foto is not None and st.session_state.get(
                "_foto_salva") != getattr(nova_foto, "file_id", None):
            novo = banco.salvar_foto_bytes(nova_foto.getvalue(), nova_foto.name)
            if novo:
                if foto:
                    banco.remover_foto(foto)
                foto = novo
                st.session_state["_foto_salva"] = getattr(
                    nova_foto, "file_id", None)

        dados = {
            "matricula": matricula.strip(), "nome": nome.strip(),
            "rg": rg.strip(),
            "cpf": cal.formatar_cpf(cpf) if cpf.strip() else "",
            "telefone": cal.formatar_telefone(telefone),
            "admissao": admissao.isoformat(),
            "demissao": demissao.isoformat() if demissao else None,
            "loja": loja, "situacao": situacao, "cargo": cargo,
            "experiencia_dias": (int(experiencia.split()[0])
                                 if experiencia[:1].isdigit() else None),
            "foto": foto, "observacao": observacao.strip(),
        }
        if reg:
            banco.atualizar(reg["id"], dados)
            st.success("Cadastro atualizado com sucesso.")
        else:
            banco.inserir(dados)
            st.success("Funcionario cadastrado com sucesso.")

    if reg:
        st.divider()
        st.subheader("\U0001F5D1 Excluir cadastro")
        confirma = st.checkbox(f"Confirmo a exclusao de {reg['nome']}")
        if st.button("\U0001F5D1 Excluir definitivamente",
                     disabled=not confirma):
            banco.excluir(reg["id"])
            st.success("Registro excluido.")
            st.rerun()


def pagina_eventos(banco):
    """Pagina de Eventos Trabalhistas com cartoes separados e organizados."""
    estilo.cabecalho("Eventos trabalhistas",
                    "Contratos de experiencia e ferias")
    filtros = _filtros(banco, "eventos")
    registros = banco.pesquisar(*filtros)
    if not registros:
        st.info("\U0001F50D Nenhum funcionario encontrado.")
        return
    hoje = date.today()

    alerta_exp = [r for r in registros if r["experiencia_dias"] and
                  cal.contrato_experiencia(
                      cal.parse_data(r["admissao"]), r["experiencia_dias"],
                      hoje)["alerta"]]
    liberadas = [r for r in registros if cal.calcular_ferias(
        cal.parse_data(r["admissao"]), hoje)["liberada"]]

    # --- metricas resumo ---
    c1, c2, c3 = st.columns(3)
    c1.metric("\U0001F465 Funcionarios listados", len(registros))
    c2.metric("\u26A0\uFE0F Experiencia vencendo (7d)", len(alerta_exp))
    c3.metric("\U0001F3D6\uFE0F Ferias liberadas", len(liberadas))

    # --- selecao do funcionario ---
    opcoes = _opcoes(banco, registros)
    escolha = st.selectbox("Funcionario", list(opcoes))
    reg = banco.obter(opcoes[escolha])

    # --- foto + resumo rapido ---
    ef1, ef2 = st.columns([1, 4])
    foto = banco.caminho_foto(reg["foto"])
    if foto:
        ef1.image(foto, width=180, caption=reg["nome"])
    else:
        ef1.info("\U0001F4F7 Sem foto")
    adm = cal.parse_data(reg["admissao"])
    ef2.markdown(
        f"**{reg['matricula']}** \u00B7 {reg['nome']} \u00B7 "
        f"{reg['cargo'] or '-'} \u00B7 {reg['loja'] or '-'}")
    ef2.caption(f"Admissao: {cal.fmt(adm)} | Situacao: {reg['situacao']}")

    st.divider()

    # --- cartao contrato de experiencia ---
    if reg["experiencia_dias"]:
        e = cal.contrato_experiencia(adm, reg["experiencia_dias"], hoje)
        sit_tipo = ("alerta" if e["alerta"]
                    else ("perigo" if e["encerrado"] else "info"))
        estilo.cartao_evento(
            titulo="Contrato de Experiencia",
            icon="\U0001F4DD",
            campos=[
                ("Prazo", f"{e['prazo_dias']} dias ({e['etapas']})"),
                ("Periodo", f"{cal.fmt(e['inicio'])} a {cal.fmt(e['fim'])}"),
                ("Dias restantes", f"{e['dias_restantes']} dia(s)"),
            ],
            situacao_texto=e["situacao"],
            situacao_tipo=sit_tipo,
            cor_barra="#E8C547",
            cor_barra_clara="#F9E79F",
        )
    else:
        estilo.cartao_evento(
            titulo="Contrato de Experiencia",
            icon="\U0001F4DD",
            campos=[("Status", "Sem contrato de experiencia registrado")],
            situacao_texto="Sem contrato",
            situacao_tipo="info",
            cor_barra="#95A5A6",
            cor_barra_clara="#BDC3C7",
        )

    # --- cartao ferias ---
    f = cal.calcular_ferias(adm, hoje)
    if f["vencida"]:
        sit_tipo_fer = "perigo"
    elif f["liberada"] and f["proxima_vencer_gozo"]:
        sit_tipo_fer = "alerta"
    elif f["liberada"]:
        sit_tipo_fer = "ok"
    elif f["situacao"] == "Proxima de liberar":
        sit_tipo_fer = "alerta"
    else:
        sit_tipo_fer = "info"
    estilo.cartao_evento(
        titulo="Ferias",
        icon="\U0001F3D6\uFE0F",
        campos=[
            ("Regra aplicada", f["regra"]),
            ("Tempo de casa", f"{f['tempo_servico_meses']} mes(es)"),
            ("Periodo aquisitivo", f"{cal.fmt(f['inicio_periodo'])} a "
             f"{cal.fmt(f['fim_periodo'])}"),
            ("Liberacao", f"{cal.fmt(f['data_liberacao'])} "
             f"({f['meses_liberacao']} de {f['meses_periodo']} meses)"),
            ("Progresso", f["progresso"]),
            ("Dias proporcionais", f"{f['dias_proporcionais']}"),
            ("Limite para gozo", cal.fmt(f["limite_gozo"])),
        ],
        situacao_texto=f["situacao"],
        situacao_tipo=sit_tipo_fer,
        cor_barra="#4CAF50",
        cor_barra_clara="#82E0AA",
        progresso_pct=min(f["meses_cumpridos"] / f["meses_liberacao"], 1.0),
    )

    # --- alerta visual de ferias vencida ---
    if f["vencida"]:
        # Dias em atraso desde o inicio do periodo atual (= fim do periodo vencido)
        dias_vencida = (hoje - f["inicio_periodo"]).days
        # Data do prazo expirado = inicio do periodo atual
        prazo_expirado = cal.fmt(f["inicio_periodo"])
        estilo.alerta_ferias_vencida(
            f"{reg['matricula']} \u00B7 {reg['nome']}",
            [("Liberada em", cal.fmt(f["data_liberacao"])),
             ("Prazo de gozo expirou em", prazo_expirado),
             ("Dias em atraso", f"{dias_vencida} dia(s)"),
             ("Dias proporcionais", f"{f['dias_proporcionais']}")])
    elif f["proxima_vencer_gozo"]:
        dias_restantes = (f["limite_gozo"] - hoje).days
        estilo.alerta_ferias_gozo_proximo(
            f"{reg['matricula']} \u00B7 {reg['nome']}",
            [("Liberada em", cal.fmt(f["data_liberacao"])),
             ("Prazo de gozo expira em", cal.fmt(f["limite_gozo"])),
             ("Dias restantes", f"{dias_restantes} dia(s)"),
             ("Dias proporcionais", f"{f['dias_proporcionais']}")])


def pagina_exportar(banco):
    estilo.cabecalho("Exportar e backup",
                    "Baixe planilhas e copia do banco")
    filtros = _filtros(banco, "export")
    registros = banco.pesquisar(*filtros)
    st.caption(f"{len(registros)} registro(s) serao exportados "
               "com os filtros atuais.")
    if registros:
        conteudo, nome = exportador.exportar_bytes(registros)
        tipo = ("application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet" if nome.endswith(".xlsx")
                else "text/csv")
        st.download_button("\U0001F4E5 Baixar planilha do Excel",
                           conteudo, nome, tipo, type="primary")
        if not nome.endswith(".xlsx"):
            st.info("openpyxl nao esta instalado, por isso a exportacao saiu "
                    "em CSV (abre no Excel).")
    else:
        st.info("\U0001F50D Nenhum registro para exportar.")

    st.divider()
    st.subheader("\U0001F4BE Backup do banco de dados")
    st.caption("Baixe periodicamente e guarde em local seguro.")
    if os.path.isfile(DB_PATH):
        with open(DB_PATH, "rb") as fp:
            st.download_button("\U0001F4E5 Baixar banco (.db)", fp.read(),
                               f"backup_funcionarios_{date.today():%Y-%m-%d}.db",
                               "application/octet-stream")
    else:
        st.warning("\u26A0\uFE0F Arquivo do banco nao encontrado.")


def pagina_config(banco):
    estilo.cabecalho("Configuracoes", "Ajuste combos e confira regras")

    st.subheader("\U0001F4CB Opcoes dos combos")
    c1, c2 = st.columns([1, 2])
    tipo = c1.selectbox("Tipo", ["loja", "situacao", "cargo"])
    novo = c2.text_input("Nova opcao")
    if st.button("\U0001F195 Adicionar", type="primary") and novo.strip():
        banco.add_combo(tipo, novo)
        st.success(f"\u2705 '{novo.strip()}' adicionado em {tipo}.")
    st.dataframe(
        estilo.estilo_tabela(
            pd.DataFrame({tipo.capitalize(): banco.listar_combo(tipo)})),
        width="stretch", hide_index=True)

    st.divider()
    st.subheader("\U0001F3D6\uFE0F Regras de ferias em uso")
    estilo.cartao(
        "\U0001F4C5 Menos de 1 ano",
        [("Periodo", "24 meses"), ("Liberacao", "20 meses")])
    estilo.cartao(
        "\U0001F4C5 Mais de 1 ano",
        [("Periodo", "12 meses"), ("Liberacao", "8 meses")])
    st.caption("Contratos de experiencia disponiveis: "
               + ", ".join(f"{d} dias" for d in cal.PRAZOS_EXPERIENCIA))


def pagina_dashboard(banco):
    estilo.cabecalho("Dashboard", "Turnover e eventos trabalhistas")
    registros = banco.pesquisar()
    if not registros:
        st.info("Cadastre funcionarios para ver os graficos.")
        return

    hoje = date.today()
    c1, c2 = st.columns([1, 3])
    meses = c1.selectbox("Periodo", [6, 12, 24], index=1,
                         format_func=lambda m: f"Ultimos {m} meses")
    lojas = c2.multiselect("Lojas", banco.listar_combo("loja"))
    if lojas:
        registros = [r for r in registros if r["loja"] in lojas]
    if not registros:
        st.info("Nenhum funcionario nas lojas selecionadas.")
        return

    tot = dash.turnover_periodo(registros, meses, hoje)
    ev = dash.resumo_eventos(registros, hoje)
    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    k1.metric("Quadro ativo", tot["quadro_atual"])
    k2.metric("Turnover medio", f"{tot['turnover_medio']}%",
              help="((admissoes + desligamentos) / 2) / quadro medio")
    k3.metric("Admissoes", tot["admissoes"])
    k4.metric("Desligamentos", tot["desligamentos"])
    k5.metric("Ferias liberadas", ev["ferias_liberadas"])
    k6.metric("\U0001F6A8 Ferias VENCIDAS", ev["ferias_vencidas"])
    k7.metric("\u26A0\uFE0F Gozo vence 30d", ev["ferias_gozo_30"])

    st.divider()

    col = estilo.CORES_GRAFICO
    mov = dash.movimentacao_mensal(registros, meses, hoje)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### \U0001F4C8 Turnover mensal (%)")
        st.line_chart(mov[["Turnover %", "Desligamentos %"]],
                      color=[col[0], col[3]], height=290)
    with c2:
        st.markdown("#### \U0001F4CA Admissoes x desligamentos")
        st.bar_chart(mov[["Admissoes", "Desligamentos"]],
                     color=[col[1], col[3]], height=290)

    st.markdown("#### \U0001F4C9 Evolucao do quadro")
    st.area_chart(mov[["Quadro no fim do mes"]],
                  color=col[2], height=250)

    st.divider()
    st.markdown("#### \U0001F3E2 Turnover por loja")
    por_loja = dash.turnover_por_loja(registros, meses, hoje)
    c1, c2 = st.columns([2, 3])
    c1.bar_chart(por_loja[["Turnover %"]], color=col[3], height=260)
    c2.dataframe(por_loja.style.format({"Turnover %": "{:.1f}%"}),
                 width="stretch")

    c1, c2, c3 = st.columns(3)
    ativos_lista = dash.ativos(registros, hoje)
    with c1:
        st.markdown("#### \U0001F4BC Por cargo")
        st.bar_chart(dash.por_categoria(ativos_lista, "cargo", "Cargo"),
                     color=col[0], height=260)
    with c2:
        st.markdown("#### \U0001F4CB Por situacao")
        st.bar_chart(dash.por_categoria(registros, "situacao", "Situacao"),
                     color=col[1], height=260)
    with c3:
        st.markdown("#### \u23F1 Tempo de casa")
        st.bar_chart(dash.faixas_tempo_casa(registros, hoje),
                     color=col[2], height=260)

    st.divider()
    st.markdown("#### \U0001F4C4 Eventos trabalhistas")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("\U0001F4CB Experiencia vencendo em 30d",
              ev["experiencia_30"])
    k2.metric("\u26A0 Experiencia vencendo em 7d",
              ev["experiencia_7"])
    k3.metric("\U0001F3D6 Ferias liberando em 60d",
              ev["ferias_proximas"])
    k4.metric("\U0001F6A8 Ferias VENCIDAS",
              ev["ferias_vencidas"])

    # --- alerta visual urgente: ferias vencidas ---
    vencidas = [r for r in dash.ativos(registros, hoje)
                if cal.calcular_ferias(
                    cal.parse_data(r["admissao"]), hoje)["vencida"]]
    if vencidas:
        for r in vencidas:
            f = cal.calcular_ferias(cal.parse_data(r["admissao"]), hoje)
            dias_vencida = (hoje - f["inicio_periodo"]).days
            prazo_expirado = cal.fmt(f["inicio_periodo"])
            estilo.alerta_ferias_vencida(
                f"{r['matricula']} \u00B7 {r['nome']} \u00B7 "
                f"{r.get('cargo', '') or '-'} \u00B7 {r.get('loja', '') or '-'}",
                [("Liberada em", cal.fmt(f["data_liberacao"])),
                 ("Prazo de gozo expirou em", prazo_expirado),
                 ("Dias em atraso", f"{dias_vencida} dia(s)"),
                 ("Dias proporcionais", f"{f['dias_proporcionais']}")])
    gozo_30 = [r for r in dash.ativos(registros, hoje)
               if cal.calcular_ferias(
                   cal.parse_data(r["admissao"]), hoje)["proxima_vencer_gozo"]]
    if gozo_30:
        for r in gozo_30:
            f = cal.calcular_ferias(cal.parse_data(r["admissao"]), hoje)
            dias_restantes = (f["limite_gozo"] - hoje).days
            estilo.alerta_ferias_gozo_proximo(
                f"{r['matricula']} \u00B7 {r['nome']} \u00B7 "
                f"{r.get('cargo', '') or '-'} \u00B7 {r.get('loja', '') or '-'}",
                [("Liberada em", cal.fmt(f["data_liberacao"])),
                 ("Prazo de gozo expira em", cal.fmt(f["limite_gozo"])),
                 ("Dias restantes", f"{dias_restantes} dia(s)"),
                 ("Dias proporcionais", f"{f['dias_proporcionais']}")])

    if not vencidas and not gozo_30:
        st.success("\u2705 Nenhuma ferias vencida ou com prazo de gozo "
                   "vencendo em 30 dias.")

    tab1, tab2 = st.tabs(
        ["\U0001F4DD Contratos de experiencia",
         "\U0001F3D6 Ferias"])
    with tab1:
        exp = dash.eventos_experiencia(registros, hoje)
        if exp.empty:
            st.success("\u2705 Nenhum contrato de experiencia vencendo "
                       "em 30 dias.")
        else:
            st.dataframe(estilo.estilo_tabela(exp,
                         coluna_exp="Situacao"),
                         width="stretch", hide_index=True)
    with tab2:
        fer = dash.eventos_ferias(registros, hoje)
        if fer.empty:
            st.info("Sem funcionarios ativos.")
        else:
            st.dataframe(
                estilo.estilo_tabela(fer, coluna_ferias="Liberada",
                                     coluna_vencida="Vencida"),
                width="stretch", hide_index=True)


# ============================================================
# MAIN
# ============================================================

def main():
    banco = get_banco()
    estilo.marca()
    pagina = st.sidebar.radio(
        "Navegacao", ["\U0001F4CA Dashboard", "\U0001F50D Consultar",
                     "\U0001F4DD Cadastrar", "\U0001F4CB Eventos",
                     "\U0001F4E5 Exportar", "\U0001F527 Ajustes"])
    st.sidebar.divider()
    st.sidebar.caption(
        f"\U0001F4C5 {cal.fmt(date.today())}  \u00B7  "
        f"{len(banco.pesquisar())} cadastro(s)")

    rotas = {"\U0001F4CA Dashboard": pagina_dashboard,
             "\U0001F50D Consultar": pagina_consultar,
             "\U0001F4DD Cadastrar": pagina_cadastro,
             "\U0001F4CB Eventos": pagina_eventos,
             "\U0001F4E5 Exportar": pagina_exportar,
             "\U0001F527 Ajustes": pagina_config}
    rotas[pagina](banco)


if __name__ == "__main__":
    main()
