"""Calculos de turnover, movimentacao e eventos para o dashboard."""

from datetime import date

import pandas as pd

import calculos as cal


def turnover_periodo(registros, meses, ref=None):
    """Resumo de turnover em N meses."""
    ref = ref or date.today()
    inicio = cal.add_meses(ref, -meses)

    admissoes = 0
    desligamentos = 0
    for r in registros:
        a = cal.parse_data(r["admissao"])
        d = cal.parse_data(r.get("demissao")) if r.get("demissao") else None
        if a and inicio <= a <= ref:
            admissoes += 1
        if d and inicio <= d <= ref:
            desligamentos += 1

    ativos = ativos_em_data(registros, ref)
    quadro_atual = len(ativos)
    quadro_medio = quadro_atual + (admissoes + desligamentos) // 2
    quadro_medio = max(quadro_medio, 1)

    turno = ((admissoes + desligamentos) / 2) / quadro_medio * 100

    return {
        "quadro_atual": quadro_atual,
        "admissoes": admissoes,
        "desligamentos": desligamentos,
        "turnover_medio": round(turno, 1),
        "quadro_medio": quadro_medio,
    }


def ativos_em_data(registros, ref):
    """Retorna registros ativos na data ref."""
    resultado = []
    for r in registros:
        a = cal.parse_data(r["admissao"])
        if a and a <= ref:
            d = cal.parse_data(r.get("demissao")) if r.get("demissao") else None
            if d is None or d > ref:
                resultado.append(r)
    return resultado


def ativos(registros, ref=None):
    ref = ref or date.today()
    return ativos_em_data(registros, ref)


def movimentacao_mensal(registros, meses, ref=None):
    """DataFrame com admissoes, desligamentos, quadro e turnover por mes."""
    ref = ref or date.today()
    rows = []
    for i in range(meses - 1, -1, -1):
        m = cal.add_meses(ref, -i)
        mes_str = m.strftime("%Y-%m")
        mes_label = m.strftime("%b/%y")

        adm = 0
        desl = 0
        for r in registros:
            a = cal.parse_data(r["admissao"])
            d = cal.parse_data(r.get("demissao")) if r.get("demissao") else None
            if a and a.strftime("%Y-%m") == mes_str:
                adm += 1
            if d and d.strftime("%Y-%m") == mes_str:
                desl += 1

        quadro_fim = len(ativos_em_data(registros, m))
        quadro_med = max(quadro_fim + (adm + desl) // 2, 1)
        turno = ((adm + desl) / 2) / quadro_med * 100

        rows.append({
            "Mes": mes_label, "Admissoes": adm,
            "Desligamentos": desl, "Quadro no fim do mes": quadro_fim,
            "Turnover %": round(turno, 1),
            "Desligamentos %": round(desl / quadro_med * 100, 1),
        })
    return pd.DataFrame(rows).set_index("Mes")


def turnover_por_loja(registros, meses, ref=None):
    """DataFrame com turnover por loja."""
    ref = ref or date.today()
    lojas = sorted(set(r.get("loja", "") or "Sem loja" for r in registros))
    rows = []
    for loja in lojas:
        regs = [r for r in registros if (r.get("loja", "") or "Sem loja") == loja]
        t = turnover_periodo(regs, meses, ref)
        rows.append({
            "Loja": loja, "Quadro": t["quadro_atual"],
            "Admissoes": t["admissoes"], "Desligamentos": t["desligamentos"],
            "Turnover %": t["turnover_medio"],
        })
    if not rows:
        return pd.DataFrame(columns=["Loja", "Quadro", "Admissoes",
                                     "Desligamentos", "Turnover %"]).set_index("Loja")
    return pd.DataFrame(rows).set_index("Loja")


def por_categoria(registros, campo, label=None):
    """Contagem por categoria (cargo, situacao etc.)."""
    label = label or campo.capitalize()
    cats = sorted(set(r.get(campo, "") or "Nenhum(a)" for r in registros))
    rows = [{label: c, "Quantidade": sum(1 for r in registros
                                        if (r.get(campo, "") or "Nenhum(a)") == c)}
            for c in cats]
    if not rows:
        return pd.DataFrame(columns=[label, "Quantidade"]).set_index(label)
    return pd.DataFrame(rows).set_index(label)


def faixas_tempo_casa(registros, ref=None):
    """Contagem por faixa de tempo de casa."""
    ref = ref or date.today()
    faixas = ["0-6m", "6-12m", "1-2a", "2-5a", "5-10a", "+10a"]
    contagem = {f: 0 for f in faixas}
    for r in registros:
        a = cal.parse_data(r["admissao"])
        if not a:
            continue
        meses = cal.meses_completos(a, ref)
        if meses < 6:
            contagem["0-6m"] += 1
        elif meses < 12:
            contagem["6-12m"] += 1
        elif meses < 24:
            contagem["1-2a"] += 1
        elif meses < 60:
            contagem["2-5a"] += 1
        elif meses < 120:
            contagem["5-10a"] += 1
        else:
            contagem["+10a"] += 1
    return pd.DataFrame([{"Faixa": f, "Quantidade": v}
                          for f, v in contagem.items()]).set_index("Faixa")


def resumo_eventos(registros, ref=None):
    ref = ref or date.today()
    exp_30 = 0
    exp_7 = 0
    ferias_prox = 0
    ferias_lib = 0
    ferias_venc = 0
    ferias_gozo_30 = 0
    ferias_alerta_4m = 0
    for r in registros:
        if r.get("experiencia_dias"):
            e = cal.contrato_experiencia(
                cal.parse_data(r["admissao"]), r["experiencia_dias"], ref)
            if e["dias_restantes"] <= 30:
                exp_30 += 1
            if e["alerta"]:
                exp_7 += 1
        f = cal.calcular_ferias(cal.parse_data(r["admissao"]), ref)
        if f["liberada"]:
            ferias_lib += 1
        if f["vencida"]:
            ferias_venc += 1
        if f["proxima_vencer_gozo"]:
            ferias_gozo_30 += 1
        if f["alerta_4_meses"]:
            ferias_alerta_4m += 1
        if not f["liberada"]:
            dias_lib = (f["data_liberacao"] - ref).days
            if 0 < dias_lib <= 60:
                ferias_prox += 1
    return {
        "experiencia_30": exp_30,
        "experiencia_7": exp_7,
        "ferias_liberadas": ferias_lib,
        "ferias_proximas": ferias_prox,
        "ferias_vencidas": ferias_venc,
        "ferias_gozo_30": ferias_gozo_30,
        "ferias_alerta_4m": ferias_alerta_4m,
    }


def eventos_experiencia(registros, ref=None):
    ref = ref or date.today()
    rows = []
    for r in registros:
        if not r.get("experiencia_dias"):
            continue
        e = cal.contrato_experiencia(
            cal.parse_data(r["admissao"]), r["experiencia_dias"], ref)
        if e["dias_restantes"] <= 30:
            rows.append({
                "Matricula": r["matricula"],
                "Funcionario": r["nome"],
                "Loja": r.get("loja", ""),
                "Cargo": r.get("cargo", ""),
                "Prazo": f"{e['prazo_dias']}d ({e['etapas']})",
                "Fim": cal.fmt(e["fim"]),
                "Dias restantes": e["dias_restantes"],
                "Situacao": e["situacao"],
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def eventos_ferias(registros, ref=None):
    ref = ref or date.today()
    rows = []
    for r in ativos(registros, ref):
        f = cal.calcular_ferias(cal.parse_data(r["admissao"]), ref)
        # Filtrar: mostrar apenas colaboradores com alerta_4_meses,
        # ferias liberada ou vencida
        if not (f["alerta_4_meses"] or f["liberada"] or f["vencida"]):
            continue
        vencida_txt = "Sim" if f["vencida"] else "Nao"
        gozo_30_txt = "Sim" if f["proxima_vencer_gozo"] else "Nao"
        alerta_4m_txt = "Sim" if f["alerta_4_meses"] else "Nao"
        rows.append({
            "Matricula": r["matricula"],
            "Funcionario": r["nome"],
            "Loja": r.get("loja", ""),
            "Cargo": r.get("cargo", ""),
            "Regra": f["regra"],
            "Periodo": f"{cal.fmt(f['inicio_periodo'])} a {cal.fmt(f['fim_periodo'])}",
            "Liberacao": cal.fmt(f["data_liberacao"]),
            "Limite gozo": cal.fmt(f["limite_gozo"]),
            "Progresso": f["progresso"],
            "Dias prop.": f["dias_proporcionais"],
            "Liberada": "Sim" if f["liberada"] else "Nao",
            "Vencida": vencida_txt,
            "Gozo vence 30d": gozo_30_txt,
            "Alerta 4 meses": alerta_4m_txt,
            "Situacao": f["situacao"],
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()
