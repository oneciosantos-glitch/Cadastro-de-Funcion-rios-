"""Calculos de experiencia, ferias, CPF e datas."""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

PRAZOS_EXPERIENCIA = [30, 45, 60, 90]


def parse_data(valor):
    """Converte string 'YYYY-MM-DD' ou Date para date."""
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str) and valor.strip():
        return date.fromisoformat(valor.strip())
    return None


def fmt(d):
    """Formata date como dd/mm/aaaa."""
    return d.strftime("%d/%m/%Y") if d else "-"


def add_meses(d, n):
    """Soma n meses a uma data."""
    return d + relativedelta(months=n)


def meses_completos(inicio, ref=None):
    """Quantos meses completos entre inicio e ref (hoje se None)."""
    ref = ref or date.today()
    delta = relativedelta(ref, inicio)
    return delta.years * 12 + delta.months


def contrato_experiencia(admissao, prazo_dias, ref=None):
    """Retorna dict com dados do contrato de experiencia.

    prazo_dias = 30 | 45 | 60 | 90
    Etapas: 30 = unico | 45 = 45 | 60 = 30+30 | 90 = 45+45
    """
    ref = ref or date.today()
    fim = admissao + timedelta(days=prazo_dias)
    alerta = (fim - ref).days <= 7 and (fim - ref).days >= 0
    encerrado = ref >= fim

    etapas = {30: "30", 45: "45", 60: "30 + 30", 90: "45 + 45"}

    dias_restantes = max((fim - ref).days, 0)
    if encerrado:
        situacao = "Encerrado"
    elif alerta:
        situacao = f"Atencao - vence em {dias_restantes} dia(s)"
    else:
        situacao = f"Dentro do prazo ({dias_restantes} dias restantes)"

    return {
        "prazo_dias": prazo_dias,
        "etapas": etapas.get(prazo_dias, str(prazo_dias)),
        "inicio": admissao,
        "fim": fim,
        "alerta": alerta,
        "encerrado": encerrado,
        "situacao": situacao,
        "dias_restantes": dias_restantes,
    }


def calcular_ferias(admissao, ref=None):
    """Calcula ferias com as regras customizadas.

    Regras:
    - 1o periodo (< 24 meses de casa): periodo 24 meses, liberacao aos 20 meses
    - Periodos seguintes (>= 24 meses de casa): periodo 12 meses, liberacao aos 8 meses

    Ferias vencidas: quando o periodo anterior encerrou sem que as ferias
    fossem gozadas. O limite de gozo e o fim do periodo aquisitivo.
    Se ref > fim do periodo anterior e ferias estavam liberadas,
    elas estao vencidas.
    """
    ref = ref or date.today()
    meses_casa = meses_completos(admissao, ref)
    anos_casa = meses_casa // 12

    # --- Periodo atual ---
    if meses_casa < 24:
        # Primeiro periodo: 24 meses a partir da admissao
        regra = "Menos de 1 ano (20 de 24)"
        inicio_periodo = admissao
        meses_periodo = 24
        meses_liberacao = 20
    else:
        # Periodos subsequentes: 12 meses a partir do ultimo aniversario
        regra = "Mais de 1 ano (8 de 12)"
        aniversario = add_meses(admissao, anos_casa * 12)
        inicio_periodo = aniversario
        meses_periodo = 12
        meses_liberacao = 8

    fim_periodo = add_meses(inicio_periodo, meses_periodo)
    data_liberacao = add_meses(inicio_periodo, meses_liberacao)
    limite_gozo = fim_periodo  # prazo para gozo = fim do periodo aquisitivo
    meses_cumpridos = meses_completos(inicio_periodo, ref)

    liberada = ref >= data_liberacao and ref <= fim_periodo

    # --- Verificar periodo anterior (ferias vencidas) ---
    vencida = False
    periodo_vencido_fim = None

    if meses_casa >= 24:
        # 2+ anos de casa: periodo anterior era de 12 meses.
        # Ferias vencidas: periodo anterior encerrou sem gozo.
        # Assumimos que se o periodo atual ja liberou ferias (liberada),
        # o funcionario tirou as do periodo anterior.
        # Entao vencida so na janela: inicio_periodo < ref < data_liberacao
        if inicio_periodo < ref < data_liberacao:
            vencida = True
            periodo_vencido_fim = inicio_periodo  # = fim do periodo anterior

    # < 24 meses: se ref > fim_periodo do 1o periodo, vencida
    if meses_casa < 24 and ref > fim_periodo:
        vencida = True
        periodo_vencido_fim = fim_periodo

    proxima_vencer = (liberada and not vencida
                     and (limite_gozo - ref).days <= 30)
    progresso = f"{meses_cumpridos}/{meses_liberacao}"
    dias_proporcionais = round(meses_cumpridos * 2.5, 1)

    if vencida and periodo_vencido_fim:
        dias_vencida = (ref - periodo_vencido_fim).days
        situacao = f"VENCIDA ha {dias_vencida} dia(s)"
    elif liberada and proxima_vencer:
        dias_restantes_gozo = (limite_gozo - ref).days
        situacao = f"LIBERADA - gozo vence em {dias_restantes_gozo}d"
    elif liberada:
        situacao = "LIBERADA"
    elif meses_cumpridos >= meses_liberacao - 2:
        situacao = "Proxima de liberar"
    else:
        situacao = "Em curso"

    return {
        "regra": regra,
        "tempo_servico_meses": meses_casa,
        "anos_casa": anos_casa,
        "inicio_periodo": inicio_periodo,
        "fim_periodo": fim_periodo,
        "meses_periodo": meses_periodo,
        "meses_liberacao": meses_liberacao,
        "data_liberacao": data_liberacao,
        "limite_gozo": limite_gozo,
        "meses_cumpridos": meses_cumpridos,
        "progresso": progresso,
        "dias_proporcionais": dias_proporcionais,
        "liberada": liberada,
        "vencida": vencida,
        "proxima_vencer_gozo": proxima_vencer,
        "situacao": situacao,
    }


def cpf_valido(cpf):
    """Valida CPF pelos digitos verificadores."""
    cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))
    if len(cpf_limpo) != 11 or cpf_limpo == cpf_limpo[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf_limpo[j]) * (i + 1 - j) for j in range(i))
        dig = 11 - soma % 11
        if dig >= 10:
            dig = 0
        if int(cpf_limpo[i]) != dig:
            return False
    return True


def formatar_cpf(cpf):
    """Formata CPF como XXX.XXX.XXX-XX."""
    d = ''.join(filter(str.isdigit, str(cpf)))
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}" if len(d) == 11 else cpf


def formatar_telefone(tel):
    """Formata telefone como (XX) XXXXX-XXXX se possivel."""
    d = ''.join(filter(str.isdigit, str(tel)))
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:11]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:10]}"
    return tel
