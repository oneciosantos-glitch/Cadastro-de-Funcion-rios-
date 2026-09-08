"""Sistema de Cadastro de Funcionarios - versao web (Streamlit).

Use de qualquer lugar/dispositivo e compartilhe o link com sua equipe.
Execute local:  streamlit run streamlit_app.py

Sistema aberto: qualquer pessoa com o link pode acessar e alterar cadastros.
"""

import os
from datetime import date, timedelta

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

    # --- Acoes por funcionario (editar / excluir) ---
    registros_all = banco.pesquisar(*filtros)
    if registros_all:
        st.divider()
        st.subheader("\U0001F4DD Acoes por funcionario")
        opcoes_acao = {f"{r['matricula']} - {r['nome']}": r for r in registros_all}
        escolha_acao = st.selectbox("Selecionar funcionario",
                                   list(opcoes_acao.keys()),
                                   key="consulta_acao_sel")
        reg_acao = opcoes_acao[escolha_acao]
        ca1, ca2 = st.columns(2)
        editar = ca1.button("\U0001F4DD Editar cadastro",
                            key="consulta_btn_editar",
                            type="primary")
        excluir = ca2.button("\U0001F5D1 Excluir cadastro",
                            key="consulta_btn_excluir")

        if editar:
            st.session_state["_navegar_para"] = "\U0001F4DD Cadastrar"
            st.session_state["_editar_id"] = reg_acao["id"]
            st.rerun()

        if excluir:
            confirma_exc = st.checkbox(
                f"Confirmo a exclusao de {reg_acao['nome']}",
                key="consulta_confirma_exc")
            if confirma_exc:
                banco.excluir(reg_acao["id"])
                st.success("Registro excluido com sucesso.")
                st.rerun()
            else:
                st.warning("Marque a confirmacao para excluir.")


def pagina_cadastro(banco):
    estilo.cabecalho("Cadastrar / Editar",
                    "Preencha os campos e anexe a foto")
    registros = banco.pesquisar()
    opcoes = _opcoes(banco, registros)

    # Se veio da pagina Consultar (editar por ID), pre-selecionar
    _editar_id = st.session_state.pop("_editar_id", None)
    _navegar = st.session_state.pop("_navegar_para", None)
    _pre_sel = None
    if _editar_id:
        for k, v in opcoes.items():
            if v == _editar_id:
                _pre_sel = k
                break
        # Forcar o widget sel_registro a mostrar o registro correto
        if _pre_sel:
            st.session_state["sel_registro"] = _pre_sel
            # Marcar que este registro e o atual (nao disparar limpeza)
            st.session_state["_cad_sel_reg"] = _pre_sel

    escolha = st.selectbox("Selecionar registro",
                          ["\U0001F195 Novo cadastro"] + list(opcoes),
                          index=(list(opcoes).index(_pre_sel) + 1
                                 if _pre_sel and _pre_sel in list(opcoes) else 0),
                          key="sel_registro")
    reg = banco.obter(opcoes[escolha]) if escolha in opcoes else None

    # Limpar widget keys do form SOMENTE quando o usuario mudar
    # intencionalmente o registro selecionado (via sel_registro changes)
    _sel_key = "_cad_sel_reg"
    _widget_key = "sel_registro"
    _prev_sel = st.session_state.get(_sel_key)
    # So limpa se o valor do selectbox sel_registro mudou (deteccao via callback ou comparacao)
    _current_sel = st.session_state.get(_widget_key, escolha)
    if _prev_sel != _current_sel:
        st.session_state[_sel_key] = _current_sel
        for _k in ["f_matricula", "f_nome", "f_rg", "f_cpf", "f_telefone",
                   "f_admissao", "f_obs", "f_demissao", "f_experiencia",
                   "f_foto", "f_remove_foto",
                   "sel_loja", "sel_situacao", "sel_cargo",
                   "f_loja_nova", "f_sit_nova", "f_cargo_novo"]:
            st.session_state.pop(_k, None)

    combos = {t: banco.listar_combo(t) for t in ("loja", "situacao", "cargo")}

    # --- Cadastro automatico via OCR ---
    with st.expander("\U0001F4F7 Cadastro automatico via documento",
                     expanded=False):
        st.markdown(
            "**Carregue a Ficha de Registro e/ou o Contrato de Experiencia** "
            "para preencher os campos automaticamente."
        )
        co1, co2 = st.columns(2)
        ficha_upload = co1.file_uploader(
            "\U0001F4C4 Ficha de Registro de Empregado",
            type=["pdf", "png", "jpg", "jpeg"],
            key="ocr_ficha",
            help="Upload do PDF ou imagem da Ficha de Registro"
        )
        contrato_upload = co2.file_uploader(
            "\U0001F4C3 Contrato de Experiencia",
            type=["pdf", "png", "jpg", "jpeg"],
            key="ocr_contrato",
            help="Upload do PDF ou imagem do Contrato de Experiencia"
        )

        if ficha_upload or contrato_upload:
            with st.spinner("\U0001F50D Lendo documentos..."):
                try:
                    import ocr_cadastro as ocr
                    campos_extraidos = {}
                    if ficha_upload:
                        texto_ficha = ocr.ler_documento(ficha_upload)
                        campos_ficha = ocr._extrair_com_regex(texto_ficha, "registro")
                        campos_extraidos.update(campos_ficha)
                    if contrato_upload:
                        texto_contrato = ocr.ler_documento(contrato_upload)
                        campos_contrato = ocr._extrair_com_regex(texto_contrato, "contrato")
                        if ficha_upload:
                            campos_extraidos = ocr.mesclar_campos(campos_extraidos, campos_contrato)
                        else:
                            campos_extraidos.update(campos_contrato)
                    sistema_ocr = ocr.campos_para_sistema(campos_extraidos)

                    # Armazenar no session_state para preencher os campos
                    st.session_state["_ocr_campos"] = sistema_ocr

                    # Mostrar resumo dos campos extraidos
                    st.success("\u2705 Documentos lidos com sucesso!")
                    with st.expander("\U0001F4CB Campos extraidos", expanded=True):
                        for k, v in sistema_ocr.items():
                            if k != "observacao":
                                st.write(f"**{k}:** {v}")
                        if sistema_ocr.get("observacao"):
                            st.write(f"**observacao:** {sistema_ocr['observacao'][:200]}...")

                    # Botao para aplicar os campos extraidos
                    if st.button("\U0001F4CC Aplicar campos extraidos ao formulario",
                                key="btn_ocr_aplicar"):
                        st.session_state["_ocr_aplicar"] = True
                        st.rerun()

                except Exception as e:
                    st.error(f"Erro ao ler documentos: {e}")

    # --- Pre-fill de campos via OCR ---
    ocr_campos = st.session_state.pop("_ocr_campos", None) if st.session_state.get("_ocr_aplicar") else None
    st.session_state.pop("_ocr_aplicar", None)

    # Quando OCR extrai dados, escrever diretamente nos widget keys
    # do session_state para que os campos fiquem preenchidos E editaveis
    if ocr_campos:
        _mapa_ocr = {
            "f_matricula": ocr_campos.get("matricula", ""),
            "f_nome": ocr_campos.get("nome", ""),
            "f_rg": ocr_campos.get("rg", ""),
            "f_cpf": ocr_campos.get("cpf", ""),
            "f_telefone": ocr_campos.get("telefone", ""),
            "f_admissao": None,
            "f_obs": ocr_campos.get("observacao", ""),
            "sel_loja": ocr_campos.get("loja", ""),
            "sel_situacao": ocr_campos.get("situacao", "Ativo"),
            "sel_cargo": ocr_campos.get("cargo", ""),
        }
        if ocr_campos.get("admissao"):
            try:
                _mapa_ocr["f_admissao"] = date.fromisoformat(ocr_campos["admissao"])
            except (ValueError, TypeError):
                _mapa_ocr["f_admissao"] = None
        for _key, _val in _mapa_ocr.items():
            if _val is not None:
                st.session_state[_key] = _val
        # Experiencia via OCR
        _exp_ocr = ocr_campos.get("experiencia_dias")
        if _exp_ocr:
            _prazos = ["Sem contrato"] + [f"{d} dias" for d in cal.PRAZOS_EXPERIENCIA]
            _exp_str = f"{_exp_ocr} dias"
            if _exp_str in _prazos:
                st.session_state["f_experiencia"] = _exp_str

    # Determinar valores defaults (OCR > registro existente > vazio)
    def _default(campo, reg_val=None):
        """Retorna valor default: OCR tem prioridade, senao registro existente."""
        # OCR ja foi aplicado ao session_state acima, entao os widgets
        # vao ler automaticamente do session_state
        if reg_val is not None:
            return reg_val
        return ""

    _def_loja = reg["loja"] if reg and reg.get("loja") else ""
    _def_cargo = reg["cargo"] if reg and reg.get("cargo") else ""
    _def_sit = reg["situacao"] if reg and reg.get("situacao") else "Ativo"
    _def_matricula = reg["matricula"] if reg else banco.proxima_matricula()
    _def_nome = reg["nome"] if reg else ""
    _def_rg = (reg["rg"] or "") if reg else ""
    _def_cpf = (reg["cpf"] or "") if reg else ""
    _def_telefone = (reg["telefone"] or "") if reg else ""
    _def_admissao = cal.parse_data(reg["admissao"]) if reg else date.today()
    _def_obs = (reg["observacao"] or "") if reg else ""
    _def_exp = ""
    if reg and reg["experiencia_dias"]:
        _def_exp = f"{reg['experiencia_dias']} dias"
    else:
        _def_exp = "Sem contrato"

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

    # --- campos editaveis (fora do form para funcionar imediatamente) ---
    st.markdown("#### \U0001F4DD Dados cadastrais")
    c1, c2, c3, c4 = st.columns(4)

    # Loja
    opcoes_loja = combos["loja"] + ["\u270F\uFE0F Digitar nova loja..."]
    val_loja = _def_loja
    if val_loja and val_loja not in combos["loja"]:
        opcoes_loja = [val_loja] + combos["loja"] + ["\u270F\uFE0F Digitar nova loja..."]
    idx_loja = opcoes_loja.index(val_loja) if val_loja in opcoes_loja else 0
    sel_loja = c1.selectbox("\U0001F3EA Loja", opcoes_loja, index=idx_loja,
                           key="sel_loja")
    if sel_loja == "\u270F\uFE0F Digitar nova loja...":
        loja = c1.text_input("Nome da Loja", value=val_loja, key="f_loja_nova",
                             placeholder="Digite o nome da loja")
    else:
        loja = sel_loja
    if loja.strip() and loja.strip() not in combos["loja"]:
        banco.add_combo("loja", loja.strip())

    # Situacao
    opcoes_sit = combos["situacao"] + ["\u270F\uFE0F Digitar nova situacao..."]
    val_sit = _def_sit
    if val_sit and val_sit not in combos["situacao"]:
        opcoes_sit = [val_sit] + combos["situacao"] + ["\u270F\uFE0F Digitar nova situacao..."]
    idx_sit = opcoes_sit.index(val_sit) if val_sit in opcoes_sit else 0
    sel_sit = c2.selectbox("\U0001F4CB Situacao", opcoes_sit, index=idx_sit,
                          key="sel_situacao")
    if sel_sit == "\u270F\uFE0F Digitar nova situacao...":
        situacao = c2.text_input("Nome da Situacao", value=val_sit, key="f_sit_nova",
                                placeholder="Digite a situacao")
    else:
        situacao = sel_sit
    if situacao.strip() and situacao.strip() not in combos["situacao"]:
        banco.add_combo("situacao", situacao.strip())

    # Cargo
    opcoes_cargo = combos["cargo"] + ["\u270F\uFE0F Digitar novo cargo..."]
    val_cargo = _def_cargo
    if val_cargo and val_cargo not in combos["cargo"]:
        opcoes_cargo = [val_cargo] + combos["cargo"] + ["\u270F\uFE0F Digitar novo cargo..."]
    idx_cargo = opcoes_cargo.index(val_cargo) if val_cargo in opcoes_cargo else 0
    sel_cargo = c3.selectbox("\U0001F4BC Cargo", opcoes_cargo, index=idx_cargo,
                            key="sel_cargo")
    if sel_cargo == "\u270F\uFE0F Digitar novo cargo...":
        cargo = c3.text_input("Nome do Cargo", value=val_cargo, key="f_cargo_novo",
                              placeholder="Digite o cargo")
    else:
        cargo = sel_cargo
    if cargo.strip() and cargo.strip() not in combos["cargo"]:
        banco.add_combo("cargo", cargo.strip())

    # --- Definir defaults no session_state ANTES do formulario ---
    # Isso garante que os widgets leem do session_state e nao resetam
    # com value= ao rerodar apos o submit.
    for _wk, _wv in [
        ("f_matricula", _def_matricula),
        ("f_nome", _def_nome),
        ("f_rg", _def_rg),
        ("f_cpf", _def_cpf),
        ("f_telefone", _def_telefone),
        ("f_admissao", _def_admissao),
        ("f_obs", _def_obs),
        ("f_demissao", cal.parse_data(reg["demissao"]) if reg and reg["demissao"] else None),
    ]:
        if _wk not in st.session_state:
            st.session_state[_wk] = _wv

    # --- formulario ---
    with st.form("cadastro", clear_on_submit=False):
        c1, c2, c3, c4 = st.columns(4)
        matricula = c1.text_input(
            "Matricula *", key="f_matricula")
        nome = c2.text_input("Funcionario *", key="f_nome")
        rg = c3.text_input("RG", key="f_rg")
        cpf = c4.text_input("CPF", key="f_cpf")
        telefone = c1.text_input("Telefone", key="f_telefone")
        admissao = c2.date_input(
            "Admissao *", format="DD/MM/YYYY", key="f_admissao",
            min_value=date(1970, 1, 1), max_value=date(2100, 12, 31))

        # Loja, Situacao e Cargo ja definidos acima (fora do form)
        c1.markdown(f"**Loja:** {loja or '-'}")
        c2.markdown(f"**Situacao:** {situacao or '-'}")
        c3.markdown(f"**Cargo:** {cargo or '-'}")

        prazos = ["Sem contrato"] + [f"{d} dias" for d in cal.PRAZOS_EXPERIENCIA]
        atual = _def_exp
        # Se OCR aplicou experiencia ao session_state, usar aquele valor
        _ss_exp = st.session_state.get("f_experiencia", None)
        if _ss_exp and _ss_exp in prazos:
            atual = _ss_exp
        if atual not in prazos:
            atual = "Sem contrato"
        experiencia = c1.selectbox("\U0001F4DD Contrato de experiencia",
                                   prazos, index=prazos.index(atual),
                                   key="f_experiencia")
        observacao = st.text_area(
            "\U0001F4AC Observacao",
            key="f_obs")
        demissao = c4.date_input(
            "\U0001F4C5 Desligamento (vazio = ativo)", format="DD/MM/YYYY",
            key="f_demissao",
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

    # --- Cartoes de prazo de experiencia ---
    _hoje = date.today()
    _exp_dias = None
    if experiencia and experiencia[:1].isdigit():
        _exp_dias = int(experiencia.split()[0])
    elif reg and reg.get("experiencia_dias"):
        _exp_dias = reg["experiencia_dias"]

    if _exp_dias and admissao:
        _ct = cal.contrato_experiencia(admissao, _exp_dias)
        _prazos = _ct.get("prazos_intermediarios", [])
        if _prazos:
            st.divider()
            st.subheader("\U0001F4C5 Prazos do contrato selecionado")
            for _prazo_dias, _data_fim in _prazos:
                _dias_rest = max((_data_fim - _hoje).days, 0)
                if _hoje > _data_fim:
                    _status = "vencido"
                elif _dias_rest <= 7:
                    _status = "alerta"
                else:
                    _status = "ativo"
                estilo.cartao_prazo_experiencia(
                    prazo_dias=_prazo_dias,
                    data_fim=cal.fmt(_data_fim),
                    dias_restantes=_dias_rest,
                    status_tipo=_status)

        # --- Todos os prazos legais (45, 60, 90) ---
        _todos = _ct.get("todos_os_prazos", [])
        if _todos:
            st.divider()
            estilo.secao_todos_prazos()
            for _tp in _todos:
                _tp_dias = _tp["prazo_dias"]
                _tp_fim = _tp["fim"]
                _tp_rest = _tp["dias_restantes"]
                if _tp["encerrado"]:
                    _tp_status = "vencido"
                elif _tp["alerta"]:
                    _tp_status = "alerta"
                else:
                    _tp_status = "ativo"
                # Mostrar sub-prazos intermediarios dentro de cada prazo
                _sub_html = ""
                for _sp_d, _sp_f in _tp.get("prazos_intermediarios", []):
                    _sp_rest = max((_sp_f - _hoje).days, 0)
                    _sp_venc = _hoje > _sp_f
                    _sp_tag = "vencido" if _sp_venc else ("alerta" if _sp_rest <= 7 else "ativo")
                    _sp_cls = {"ativo": "tag-azul", "alerta": "tag-amarelo", "vencido": "tag-vermelho"}
                    _sp_txt = {"ativo": f"{_sp_rest}d restantes", "alerta": f"Vencendo ({_sp_rest}d)", "vencido": "Encerrado"}
                    _sub_html += (f"<span style='margin-left:12px;font-size:12px;color:#7f8c8d'>"
                                  f"\u2192 {_sp_d}d: {cal.fmt(_sp_f)} "
                                  f"<span class='tag {_sp_cls[_sp_tag]}'>"
                                  f"{_sp_txt[_sp_tag]}</span></span><br>")
                estilo.cartao_prazo_experiencia(
                    prazo_dias=_tp_dias,
                    data_fim=cal.fmt(_tp_fim),
                    dias_restantes=_tp_rest,
                    status_tipo=_tp_status)
                if _sub_html:
                    st.markdown(_sub_html, unsafe_allow_html=True)

    if reg:
        st.divider()
        st.subheader("\U0001F5D1 Excluir cadastro")
        confirma = st.checkbox(f"Confirmo a exclusao de {reg['nome']}")
        if st.button("\U0001F5D1 Excluir definitivamente",
                     disabled=not confirma):
            banco.excluir(reg["id"])
            st.success("Registro excluido.")
            st.rerun()


def _registrar_evento_form(banco, reg, tipo_evento, chave):
    """Formulario para registrar um evento trabalhista.

    tipo_evento: 'ferias', 'licenca_maternidade', 'afastamento_inss', 'afastamento_doenca'
    Retorna dict com dados do evento ou None se cancelado.
    """
    hoje = date.today()

    # Labels e icones por tipo
    config = {
        "ferias": {
            "titulo": "Registrar Férias",
            "icone": "\U0001F3D6\uFE0F",
            "label_inicio": "Data de início das férias",
            "label_dias": "Quantidade de dias de férias",
            "dias_default": 30,
            "campo_inicio": "ferias_inicio",
            "campo_dias": "ferias_dias",
            "campo_retorno": "ferias_retorno",
        },
        "licenca_maternidade": {
            "titulo": "Registrar Licença Maternidade",
            "icone": "\U0001F9EC",
            "label_inicio": "Data de início da licença",
            "label_dias": "Quantidade de dias de licença",
            "dias_default": 120,
            "campo_inicio": "licenca_maternidade_inicio",
            "campo_dias": "licenca_maternidade_dias",
            "campo_retorno": "licenca_maternidade_retorno",
        },
        "afastamento_inss": {
            "titulo": "Registrar Afastamento INSS",
            "icone": "\U0001F3E5",
            "label_inicio": "Data de início do afastamento",
            "label_dias": "Quantidade de dias de afastamento",
            "dias_default": 15,
            "campo_inicio": "afastamento_inicio",
            "campo_dias": "afastamento_dias",
            "campo_retorno": "afastamento_retorno",
        },

    }

    cfg = config[tipo_evento]

    # Verificar se ja existe evento ativo
    inicio_atual = reg.get(cfg["campo_inicio"])
    dias_atual = reg.get(cfg["campo_dias"])
    retorno_atual = reg.get(cfg["campo_retorno"])

    c1, c2, c3 = st.columns(3)
    data_inicio = c1.date_input(
        cfg["label_inicio"], format="DD/MM/YYYY",
        key=f"{chave}_inicio",
        value=cal.parse_data(inicio_atual) if inicio_atual else hoje,
        min_value=date(1970, 1, 1), max_value=date(2100, 12, 31))
    qtd_dias = c2.number_input(
        cfg["label_dias"], min_value=1, max_value=9999,
        key=f"{chave}_dias",
        value=dias_atual if dias_atual else cfg["dias_default"])

    # Calcular retorno automaticamente
    data_retorno = cal.calcular_retorno(data_inicio, qtd_dias)
    c3.info(f"\U0001F4C5 **Retorno:** {cal.fmt(data_retorno)}")

    col_btn1, col_btn2 = st.columns([1, 3])
    registrar = col_btn1.button(
        f"{cfg['icone']} {cfg['titulo']}",
        key=f"{chave}_btn_reg", type="primary")
    encerrar = col_btn2.button(
        f"\u2705 Encerrar {cfg['titulo'].replace('Registrar ', '')}",
        key=f"{chave}_btn_enc",
        disabled=not inicio_atual)

    return {
        "registrar": registrar,
        "encerrar": encerrar,
        "data_inicio": data_inicio.isoformat(),
        "qtd_dias": qtd_dias,
        "data_retorno": data_retorno.isoformat() if data_retorno else None,
        "campo_inicio": cfg["campo_inicio"],
        "campo_dias": cfg["campo_dias"],
        "campo_retorno": cfg["campo_retorno"],
        "tipo_evento": tipo_evento,
    }


def _cartao_evento_ativo(reg, tipo_evento):
    """Exibe cartao com informacoes do evento ativo (se houver)."""
    config = {
        "ferias": {
            "icone": "\U0001F3D6\uFE0F", "titulo": "Férias em Andamento",
            "campo_inicio": "ferias_inicio", "campo_dias": "ferias_dias",
            "campo_retorno": "ferias_retorno", "cor": "#4CAF50",
            "cor_clara": "#82E0AA",
        },
        "licenca_maternidade": {
            "icone": "\U0001F9EC", "titulo": "Licença Maternidade em Andamento",
            "campo_inicio": "licenca_maternidade_inicio",
            "campo_dias": "licenca_maternidade_dias",
            "campo_retorno": "licenca_maternidade_retorno",
            "cor": "#8E44AD", "cor_clara": "#C39BD3",
        },
        "afastamento_inss": {
            "icone": "\U0001F3E5", "titulo": "Afastamento INSS em Andamento",
            "campo_inicio": "afastamento_inicio", "campo_dias": "afastamento_dias",
            "campo_retorno": "afastamento_retorno", "cor": "#E67E22",
            "cor_clara": "#F0B27A",
        },

    }

    cfg = config.get(tipo_evento)
    if not cfg:
        return

    inicio = reg.get(cfg["campo_inicio"])
    if not inicio:
        return

    dias = reg.get(cfg["campo_dias"]) or 0
    retorno = reg.get(cfg["campo_retorno"])
    data_inicio = cal.parse_data(inicio)
    data_retorno = cal.parse_data(retorno)
    hoje = date.today()

    # Calcular progresso
    total_dias = dias
    dias_passados = (hoje - data_inicio).days if data_inicio else 0
    dias_restantes = max((data_retorno - hoje).days, 0) if data_retorno else 0
    progresso = min(dias_passados / total_dias, 1.0) if total_dias > 0 else 0

    # Situacao
    if data_retorno and hoje > data_retorno:
        sit_texto = f"Vencido em {cal.fmt(data_retorno)}"
        sit_tipo = "alerta"
    elif data_retorno and (data_retorno - hoje).days <= 7:
        sit_texto = f"Retorno em {dias_restantes} dia(s)"
        sit_tipo = "alerta"
    else:
        sit_texto = f"Retorno em {dias_restantes} dia(s)"
        sit_tipo = "info"

    estilo.cartao_evento(
        titulo=cfg["titulo"],
        icon=cfg["icone"],
        campos=[
            ("Início", cal.fmt(data_inicio)),
            ("Dias", str(dias)),
            ("Retorno previsto", cal.fmt(data_retorno)),
            ("Dias restantes", f"{dias_restantes} dia(s)"),
        ],
        situacao_texto=sit_texto,
        situacao_tipo=sit_tipo,
        cor_barra=cfg["cor"],
        cor_clara=cfg["cor_clara"],
        progresso_pct=progresso,
    )


def pagina_eventos(banco):
    """Pagina de Eventos Trabalhistas com registro interativo."""
    estilo.cabecalho("Eventos trabalhistas",
                    "Contratos de experiência, férias, licenças e afastamentos")
    filtros = _filtros(banco, "eventos")
    registros = banco.pesquisar(*filtros)
    if not registros:
        st.info("\U0001F50D Nenhum funcionario encontrado.")
        return
    hoje = date.today()

    # --- metricas resumo ---
    ativos = [r for r in registros if r["situacao"] == "Ativo"]
    ferias_ativas = [r for r in registros if r["situacao"] == "Está de Férias"]
    licenca_ativas = [r for r in registros if r["situacao"] == "Licença Maternidade"]
    afast_inss = [r for r in registros if r["situacao"] == "Afastado INSS"]
    alerta_exp = [r for r in registros if r["experiencia_dias"] and
                  cal.contrato_experiencia(
                      cal.parse_data(r["admissao"]), r["experiencia_dias"],
                      hoje)["alerta"]]
    liberadas = [r for r in registros if cal.calcular_ferias(
        cal.parse_data(r["admissao"]), hoje)["liberada"]]
    alerta_4m = [r for r in registros if cal.calcular_ferias(
        cal.parse_data(r["admissao"]), hoje)["alerta_4_meses"]]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("\U0001F465 Ativos", len(ativos))
    c2.metric("\U0001F3D6\uFE0F De Férias", len(ferias_ativas))
    c3.metric("\U0001F9EC Lic. Matern.", len(licenca_ativas))
    c4.metric("\U0001F3E5 Afast. INSS", len(afast_inss))
    c5.metric("\U0001F4DD Exp. vencendo", len(alerta_exp))
    c6.metric("\U0001F7E1 Ferias 4m", len(alerta_4m))

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

    # ============================================================
    # CONTRATO DE EXPERIENCIA (com prazos e datas)
    # ============================================================
    st.subheader("\U0001F4DD Contrato de Experiencia")
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

        # Prazos intermediarios com datas (contrato selecionado)
        st.markdown("**Prazos com datas de vencimento:**")
        for prazo_dias, data_fim in e.get("prazos_intermediarios", []):
            dias_restantes_prazo = max((data_fim - hoje).days, 0)
            if hoje > data_fim:
                status_tipo = "vencido"
            elif dias_restantes_prazo <= 7:
                status_tipo = "alerta"
            else:
                status_tipo = "ativo"
            estilo.cartao_prazo_experiencia(
                prazo_dias=prazo_dias,
                data_fim=cal.fmt(data_fim),
                dias_restantes=dias_restantes_prazo,
                status_tipo=status_tipo,
            )

        # Todos os prazos legais (45, 60, 90)
        _todos = e.get("todos_os_prazos", [])
        if _todos:
            st.divider()
            estilo.secao_todos_prazos()
            for _tp in _todos:
                _tp_dias = _tp["prazo_dias"]
                _tp_fim = _tp["fim"]
                _tp_rest = _tp["dias_restantes"]
                if _tp["encerrado"]:
                    _tp_status = "vencido"
                elif _tp["alerta"]:
                    _tp_status = "alerta"
                else:
                    _tp_status = "ativo"
                _sub_html = ""
                for _sp_d, _sp_f in _tp.get("prazos_intermediarios", []):
                    _sp_rest = max((_sp_f - hoje).days, 0)
                    _sp_venc = hoje > _sp_f
                    _sp_tag = "vencido" if _sp_venc else ("alerta" if _sp_rest <= 7 else "ativo")
                    _sp_cls = {"ativo": "tag-azul", "alerta": "tag-amarelo", "vencido": "tag-vermelho"}
                    _sp_txt = {"ativo": f"{_sp_rest}d restantes", "alerta": f"Vencendo ({_sp_rest}d)", "vencido": "Encerrado"}
                    _sub_html += (f"<span style='margin-left:12px;font-size:12px;color:#7f8c8d'>"
                                  f"\u2192 {_sp_d}d: {cal.fmt(_sp_f)} "
                                  f"<span class='tag {_sp_cls[_sp_tag]}'>"
                                  f"{_sp_txt[_sp_tag]}</span></span><br>")
                estilo.cartao_prazo_experiencia(
                    prazo_dias=_tp_dias,
                    data_fim=cal.fmt(_tp_fim),
                    dias_restantes=_tp_rest,
                    status_tipo=_tp_status)
                if _sub_html:
                    st.markdown(_sub_html, unsafe_allow_html=True)
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

    st.divider()

    # ============================================================
    # FERIAS (calculo + registro)
    # ============================================================
    st.subheader("\U0001F3D6\uFE0F Férias")

    # Cartao de calculo de ferias
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
        titulo="Cálculo de Férias",
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

    # Alertas de ferias
    if f["vencida"]:
        dias_vencida = (hoje - f["inicio_periodo"]).days
        prazo_expirado = cal.fmt(f["inicio_periodo"])
        estilo.alerta_ferias_vencida(
            f"{reg['matricula']} \u00B7 {reg['nome']}",
            [("Liberada em", cal.fmt(f["data_liberacao"])),
             ("Prazo de gozo expirou em", prazo_expirado),
             ("Dias em atraso", f"{dias_vencida} dia(s)"),
             ("Dias proporcionais", f"{f['dias_proporcionais']}")])
    elif f["alerta_4_meses"]:
        dias_lib = (f["data_liberacao"] - hoje).days
        estilo.alerta_ferias_4_meses(
            f"{reg['matricula']} \u00B7 {reg['nome']}",
            [("Liberacao em", cal.fmt(f["data_liberacao"])),
             ("Dias para liberacao", f"{dias_lib} dia(s)"),
             ("Regra", f["regra"]),
             ("Dias proporcionais", f"{f['dias_proporcionais']}")])
    elif f["proxima_vencer_gozo"]:
        dias_restantes = (f["limite_gozo"] - hoje).days
        estilo.alerta_ferias_gozo_proximo(
            f"{reg['matricula']} \u00B7 {reg['nome']}",
            [("Liberada em", cal.fmt(f["data_liberacao"])),
             ("Prazo de gozo expira em", cal.fmt(f["limite_gozo"])),
             ("Dias restantes", f"{dias_restantes} dia(s)"),
             ("Dias proporcionais", f"{f['dias_proporcionais']}")])

    # Registro de ferias
    with st.expander("\U0001F4DD Registrar / Editar Férias", expanded=False):
        evento = _registrar_evento_form(banco, reg, "ferias", "evt_ferias")
        if evento["registrar"]:
            banco.atualizar(reg["id"], {
                evento["campo_inicio"]: evento["data_inicio"],
                evento["campo_dias"]: evento["qtd_dias"],
                evento["campo_retorno"]: evento["data_retorno"],
                "situacao": "Está de Férias",
            })
            st.success("\u2705 Férias registradas! Situação atualizada para 'Está de Férias'.")
            st.rerun()
        if evento["encerrar"]:
            banco.atualizar(reg["id"], {
                evento["campo_inicio"]: None,
                evento["campo_dias"]: None,
                evento["campo_retorno"]: None,
                "situacao": "Ativo",
            })
            st.success("\u2705 Férias encerradas! Situação atualizada para 'Ativo'.")
            st.rerun()

    # Cartao de ferias em andamento
    _cartao_evento_ativo(reg, "ferias")

    st.divider()

    # ============================================================
    # LICENCA MATERNIDADE
    # ============================================================
    st.subheader("\U0001F9EC Licença Maternidade")

    _cartao_evento_ativo(reg, "licenca_maternidade")

    with st.expander("\U0001F4DD Registrar / Editar Licença Maternidade", expanded=False):
        evento = _registrar_evento_form(banco, reg, "licenca_maternidade", "evt_lic_mat")
        if evento["registrar"]:
            banco.atualizar(reg["id"], {
                evento["campo_inicio"]: evento["data_inicio"],
                evento["campo_dias"]: evento["qtd_dias"],
                evento["campo_retorno"]: evento["data_retorno"],
                "situacao": "Licença Maternidade",
            })
            st.success("\u2705 Licença Maternidade registrada! Situação atualizada.")
            st.rerun()
        if evento["encerrar"]:
            banco.atualizar(reg["id"], {
                evento["campo_inicio"]: None,
                evento["campo_dias"]: None,
                evento["campo_retorno"]: None,
                "situacao": "Ativo",
            })
            st.success("\u2705 Licença Maternidade encerrada! Situação atualizada para 'Ativo'.")
            st.rerun()

    st.divider()

    # ============================================================
    # AFASTAMENTOS (INSS)
    # ============================================================
    st.subheader("\U0001F3E5 Afastamentos")

    # Afastamento INSS
    st.markdown("**Afastamento INSS**")
    _cartao_evento_ativo(reg, "afastamento_inss")

    with st.expander("\U0001F4DD Registrar / Editar Afastamento INSS", expanded=False):
        evento = _registrar_evento_form(banco, reg, "afastamento_inss", "evt_afast_inss")
        if evento["registrar"]:
            banco.atualizar(reg["id"], {
                evento["campo_inicio"]: evento["data_inicio"],
                evento["campo_dias"]: evento["qtd_dias"],
                evento["campo_retorno"]: evento["data_retorno"],
                "afastamento_tipo": "INSS",
                "situacao": "Afastado INSS",
            })
            st.success("\u2705 Afastamento INSS registrado! Situação atualizada.")
            st.rerun()
        if evento["encerrar"]:
            banco.atualizar(reg["id"], {
                evento["campo_inicio"]: None,
                evento["campo_dias"]: None,
                evento["campo_retorno"]: None,
                "afastamento_tipo": None,
                "situacao": "Ativo",
            })
            st.success("\u2705 Afastamento INSS encerrado! Situação atualizada para 'Ativo'.")
            st.rerun()

    st.divider()

    # ============================================================
    # DESLIGAMENTO
    # ============================================================
    st.subheader("\U0001F4CB Desligamento")

    tipos_deslig = [""] + cal.TIPOS_DESLIGAMENTO
    # Verificar tipo de desligamento atual
    sit_atual = reg.get("situacao", "")
    tipo_deslig_atual = sit_atual if sit_atual in cal.TIPOS_DESLIGAMENTO else ""
    idx_deslig = tipos_deslig.index(tipo_deslig_atual) if tipo_deslig_atual in tipos_deslig else 0

    c1, c2 = st.columns([2, 3])
    tipo_deslig_selecionado = c1.selectbox(
        "Tipo de desligamento", tipos_deslig, index=idx_deslig,
        key="evt_deslig_tipo")
    data_deslig = c2.date_input(
        "Data do desligamento", format="DD/MM/YYYY",
        key="evt_deslig_data",
        value=cal.parse_data(reg["demissao"]) if reg.get("demissao") else hoje,
        min_value=date(1970, 1, 1), max_value=date(2100, 12, 31))

    col_d1, col_d2 = st.columns([1, 3])
    if col_d1.button("\U0001F4CB Aplicar Desligamento", type="primary",
                     key="btn_deslig", disabled=not tipo_deslig_selecionado):
        banco.atualizar(reg["id"], {
            "situacao": tipo_deslig_selecionado,
            "demissao": data_deslig.isoformat(),
        })
        st.success(f"\u2705 Desligamento '{tipo_deslig_selecionado}' aplicado!")
        st.rerun()
    if col_d2.button("\u2705 Reverter para Ativo", key="btn_reverter_deslig",
                     disabled=tipo_deslig_atual == ""):
        banco.atualizar(reg["id"], {
            "situacao": "Ativo",
            "demissao": None,
        })
        st.success("\u2705 Situação revertida para 'Ativo'.")
        st.rerun()


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

    # --- Botoes de excluir combos com callback on_click ---
    # Inicializar estado de exclusao pendente
    if "_exc_tipo" not in st.session_state:
        st.session_state["_exc_tipo"] = None
        st.session_state["_exc_valor"] = None
        st.session_state["_exc_msg_ok"] = None
        st.session_state["_exc_msg_erro"] = None

    # Callback que marca qual item excluir
    def _marcar_excluir(t, v):
        st.session_state["_exc_tipo"] = t
        st.session_state["_exc_valor"] = v

    # Processar exclusao pendente (acontece no rerun apos o clique)
    _et = st.session_state.get("_exc_tipo")
    _ev = st.session_state.get("_exc_valor")
    if _et and _ev:
        ok = banco.remover_combo(_et, _ev)
        if ok:
            st.session_state["_exc_msg_ok"] = (
                f"\u2705 '{_ev}' removido de {_et}.")
            st.session_state["_exc_msg_erro"] = None
        else:
            st.session_state["_exc_msg_ok"] = None
            st.session_state["_exc_msg_erro"] = (
                f"\u274C '{_ev}' nao pode ser removido: "
                "esta em uso por um ou mais funcionarios.")
        st.session_state["_exc_tipo"] = None
        st.session_state["_exc_valor"] = None
        st.rerun()

    # Exibir mensagens de feedback
    if st.session_state.get("_exc_msg_ok"):
        st.success(st.session_state["_exc_msg_ok"])
        st.session_state["_exc_msg_ok"] = None
    if st.session_state.get("_exc_msg_erro"):
        st.error(st.session_state["_exc_msg_erro"])
        st.session_state["_exc_msg_erro"] = None

    # Renderizar lista com botoes de exclusao
    valores = banco.listar_combo(tipo)
    if valores:
        st.markdown("**Opcoes existentes:**")
        for idx, v in enumerate(valores):
            cv1, cv2 = st.columns([3, 1])
            cv1.markdown(f"\U0001F4CB {v}")
            cv2.button(
                "\U0001F5D1 Excluir",
                key=f"exc_combo_{tipo}_{idx}",
                on_click=_marcar_excluir,
                args=(tipo, v),
            )
    else:
        st.info(f"Nenhuma opcao cadastrada em {tipo}.")

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

    st.divider()
    st.subheader("\U0001F4CB Tipos de Desligamento")
    for t in cal.TIPOS_DESLIGAMENTO:
        estilo.tag(t, tipo="vermelho")
    st.markdown("")  # spacer

    st.subheader("\U0001F3E5 Tipos de Afastamento")
    for t in cal.TIPOS_AFASTAMENTO:
        estilo.tag(t, tipo="amarelo")


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
    k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
    k1.metric("Quadro ativo", tot["quadro_atual"])
    k2.metric("Turnover medio", f"{tot['turnover_medio']}%",
              help="((admissoes + desligamentos) / 2) / quadro medio")
    k3.metric("Admissoes", tot["admissoes"])
    k4.metric("Desligamentos", tot["desligamentos"])
    k5.metric("Ferias liberadas", ev.get("ferias_liberadas", 0))
    k6.metric("\U0001F6A8 Ferias VENCIDAS", ev.get("ferias_vencidas", 0))
    k7.metric("\u26A0\uFE0F Gozo vence 30d", ev.get("ferias_gozo_30", 0))
    k8.metric("\U0001F7E1 Alerta 4 meses", ev.get("ferias_alerta_4m", 0))

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
              ev.get("experiencia_30", 0))
    k2.metric("\u26A0 Experiencia vencendo em 7d",
              ev.get("experiencia_7", 0))
    k3.metric("\U0001F3D6 Ferias liberando em 60d",
              ev.get("ferias_proximas", 0))
    k4.metric("\U0001F6A8 Ferias VENCIDAS",
              ev.get("ferias_vencidas", 0))

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

    # --- alerta visual: ferias com alerta de 4 meses ---
    alerta_4m = [r for r in dash.ativos(registros, hoje)
                if cal.calcular_ferias(
                    cal.parse_data(r["admissao"]), hoje)["alerta_4_meses"]]
    if alerta_4m:
        for r in alerta_4m:
            f = cal.calcular_ferias(cal.parse_data(r["admissao"]), hoje)
            dias_lib = (f["data_liberacao"] - hoje).days
            estilo.alerta_ferias_4_meses(
                f"{r['matricula']} \u00B7 {r['nome']} \u00B7 "
                f"{r.get('cargo', '') or '-'} \u00B7 {r.get('loja', '') or '-'}",
                [("Liberacao em", cal.fmt(f["data_liberacao"])),
                 ("Dias para liberacao", f"{dias_lib} dia(s)"),
                 ("Regra", f["regra"]),
                 ("Dias proporcionais", f"{f['dias_proporcionais']}")])

    if not vencidas and not gozo_30 and not alerta_4m:
        st.success("\u2705 Nenhuma ferias vencida, com prazo de gozo "
                   "vencendo em 30 dias ou com alerta de 4 meses.")

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

    # Se veio de outra pagina (ex: Editar cadastro), navegar automaticamente
    _nav_dest = st.session_state.pop("_navegar_para", None)
    if _nav_dest and _nav_dest not in st.session_state.get("_nav_atual", ""):
        st.session_state["nav_radio"] = _nav_dest
        st.rerun()
    _nav_atual = st.session_state.get("nav_radio", "\U0001F4CA Dashboard")

    pagina = st.sidebar.radio(
        "Navegacao", ["\U0001F4CA Dashboard", "\U0001F50D Consultar",
                     "\U0001F4DD Cadastrar", "\U0001F4CB Eventos",
                     "\U0001F4E5 Exportar", "\U0001F527 Ajustes"],
        key="nav_radio")
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