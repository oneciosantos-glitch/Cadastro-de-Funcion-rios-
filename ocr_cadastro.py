"""Modulo de OCR para cadastro automatico a partir de documentos.

Le a Ficha de Registro de Empregado e/ou o Contrato de Experiencia,
extrai os campos via IA ou regex e retorna um dict pronto para o formulario.
"""

import json
import re

try:
    import streamlit as st
except ImportError:
    st = None


def _prompt_extracao(texto_documento: str, tipo_doc: str) -> str:
    """Gera o prompt para a IA extrair campos do documento."""
    tipo_label = {
        "registro": "Ficha de Registro de Empregado",
        "contrato": "Contrato de Experiencia",
    }.get(tipo_doc, "Documento")

    return (
        f"Analise o texto abaixo de uma {tipo_label} e extraia os campos "
        f"para cadastro de funcionario. "
        f"Retorne SOMENTE um JSON valido (sem markdown, sem ```), com as chaves abaixo. "
        f"Se um campo nao for encontrado, use null.\n\n"
        f"Campos a extrair:\n"
        f"- matricula: numero de matricula/eSocial (string)\n"
        f"- nome: nome completo do empregado (string)\n"
        f"- rg: numero da carteira de identidade (string)\n"
        f"- cpf: CPF (string, formato XXX.XXX.XXX-XX)\n"
        f"- telefone: telefone celular (string)\n"
        f"- admissao: data de admissao (string, formato YYYY-MM-DD)\n"
        f"- cargo: cargo/funcao (string)\n"
        f"- experiencia_dias: prazo do contrato em dias (inteiro: 30, 45, 60 ou 90)\n"
        f"- loja: nome/local de trabalho (string)\n"
        f"- salario: valor do salario (string)\n"
        f"- cbo: codigo CBO (string)\n"
        f"- sexo: Masculino ou Feminino (string)\n"
        f"- cor_raca: cor/raca declarada (string)\n"
        f"- estado_civil: estado civil (string)\n"
        f"- grau_instrucao: grau de instrucao (string)\n"
        f"- data_nascimento: data de nascimento (string YYYY-MM-DD)\n"
        f"- endereco: endereco residencial (string)\n"
        f"- nome_pai: nome do pai (string)\n"
        f"- nome_mae: nome da mae (string)\n"
        f"- ctps_numero: numero da CTPS (string)\n"
        f"- ctps_serie: serie da CTPS (string)\n"
        f"- titulo_eleitoral: numero do titulo eleitoral (string)\n"
        f"- pis: numero do PIS (string)\n"
        f"- cnpj_empregador: CNPJ da empresa (string)\n"
        f"- horario_trabalho: horario de trabalho (string)\n"
        f"- contrato_inicio: data inicio contrato (string YYYY-MM-DD)\n"
        f"- contrato_fim: data fim contrato (string YYYY-MM-DD)\n\n"
        f"Texto do documento:\n{texto_documento}\n\nJSON:"
    )


def extrair_campos_ia(texto_documento: str, tipo_doc: str) -> dict:
    """Extrai campos do documento usando IA (OpenAI) ou regex fallback."""
    try:
        return _extrair_com_ia(texto_documento, tipo_doc)
    except Exception:
        return _extrair_com_regex(texto_documento, tipo_doc)


def _extrair_com_ia(texto_documento: str, tipo_doc: str) -> dict:
    """Extrai campos usando a API OpenAI (se configurada)."""
    api_key = ""
    if st is not None:
        api_key = (
            st.secrets.get("openai_api_key", "")
            or st.secrets.get("OPENAI_API_KEY", "")
        )
    if not api_key:
        return _extrair_com_regex(texto_documento, tipo_doc)

    prompt = _prompt_extracao(texto_documento, tipo_doc)

    import openai
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=2000,
    )
    texto_resposta = response.choices[0].message.content.strip()
    texto_resposta = re.sub(r'^```(?:json)?\s*', '', texto_resposta)
    texto_resposta = re.sub(r'\s*```$', '', texto_resposta)
    return json.loads(texto_resposta)


def _converte_data(data_str: str) -> str:
    """Converte DD/MM/YYYY ou DD.MM.YYYY para YYYY-MM-DD."""
    data_str = data_str.replace('/', '-').replace('.', '-')
    partes = data_str.split('-')
    if len(partes) == 3 and len(partes[2]) == 4:
        return f"{partes[2]}-{partes[1]}-{partes[0]}"
    return data_str


def _extrair_com_regex(texto: str, tipo_doc: str) -> dict:
    """Extrai campos via regex adaptados ao layout real dos documentos."""
    resultado = {}

    if tipo_doc == "registro":
        resultado.update(_extrair_registro(texto))
    elif tipo_doc == "contrato":
        resultado.update(_extrair_contrato(texto))
    else:
        # Tenta ambos
        resultado.update(_extrair_registro(texto))
        resultado.update(_extrair_contrato(texto))

    return resultado


def _extrair_registro(texto: str) -> dict:
    """Extrai campos da Ficha de Registro de Empregado."""
    resultado = {}

    # Nome do empregado - aparece apos "Empregado" e antes de "Residencia"
    nome_match = re.search(
        r'Empregado\s+.*?\n([\w\s]+?)\nResid',
        texto, re.DOTALL
    )
    if nome_match:
        resultado["nome"] = nome_match.group(1).strip()

    # Matricula/eSocial - aparece apos "Matricula eSocial No"
    mat_match = re.search(r'Matr[i\xed]cula\s+eSocial\s+N[\xba\u00ba0]??\s*\n(\d+)', texto)
    if not mat_match:
        mat_match = re.search(r'eSocial\s+N[\xba\u00ba0]??\s*\n(\d+)', texto)
    if mat_match:
        resultado["matricula"] = mat_match.group(1)

    # CPF
    cpf_match = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', texto)
    if cpf_match:
        resultado["cpf"] = cpf_match.group(1)

    # RG / Cedula de Identidade
    rg_match = re.search(
        r'C[eé]dula\s+de\s+Identidade.*?\n(\d+)',
        texto, re.DOTALL
    )
    if not rg_match:
        rg_match = re.search(
            r'Identidade.*?\n(\d{4,})',
            texto, re.DOTALL
        )
    if rg_match:
        resultado["rg"] = rg_match.group(1).strip()

    # Data de nascimento
    nasc_match = re.search(
        r'Data\s+de\s+nascimento.*?(\d{2}/\d{2}/\d{4})',
        texto, re.DOTALL
    )
    if nasc_match:
        resultado["data_nascimento"] = _converte_data(nasc_match.group(1))

    # Estado civil
    civil_match = re.search(
        r'Estado\s+civil.*?\n.*?(Solteiro|Casado|Divorciado|Vi[uú]vo|Separado)',
        texto, re.DOTALL | re.IGNORECASE
    )
    if not civil_match:
        civil_match = re.search(
            r'nacionalidade\s+(Solteiro|Casado|Divorciado|Vi[uú]vo|Separado)',
            texto, re.IGNORECASE
        )
    if civil_match:
        resultado["estado_civil"] = civil_match.group(1).strip().capitalize()

    # Filiacao - Pai e Mae
    pai_match = re.search(r'Pai\s*\n([\w\s]+?)\s*FILIA', texto)
    if pai_match:
        resultado["nome_pai"] = pai_match.group(1).strip()

    mae_match = re.search(
        r'M[eã]e\s*\n([\w\s]+?)(?:\s*\n|\s*C[eé]dula)',
        texto
    )
    if mae_match:
        resultado["nome_mae"] = mae_match.group(1).strip()

    # CTPS numero e serie
    ctps_match = re.search(
        r'CTPS.*?\n(\d+)\s+(\d+)\s+(\d{2}/\d{2}/\d{4})',
        texto, re.DOTALL
    )
    if ctps_match:
        resultado["ctps_numero"] = ctps_match.group(1)
        resultado["ctps_serie"] = ctps_match.group(2)

    # Titulo eleitoral
    tit_match = re.search(
        r'T[ií]tulo\s+Eleitoral.*?(\d{10,})',
        texto, re.DOTALL
    )
    if tit_match:
        resultado["titulo_eleitoral"] = tit_match.group(1)

    # Sexo - pode estar na mesma linha de Cor/Raca
    sexo_match = re.search(
        r'Sexo\s+(Masculino|Feminino)',
        texto, re.IGNORECASE
    )
    if not sexo_match:
        sexo_match = re.search(
            r'(Masculino|Feminino)\s+(?:Ensino|Grau)',
            texto, re.IGNORECASE
        )
    if sexo_match:
        resultado["sexo"] = sexo_match.group(1).strip().capitalize()

    # Cor/Raca - pode estar na linha "280154720658 RA Parda Masculino Ensino Medio Completo"
    cor_opcoes = r'(Branca|Preta|Parda|Amarela|Ind[ií]gena)'
    cor_match = re.search(
        r'Cor\s+' + cor_opcoes,
        texto, re.IGNORECASE
    )
    if not cor_match:
        # Na linha de doc militar/cor/sexo/grau: "RA Parda Masculino"
        cor_match = re.search(
            r'(?:RA\s+)?(' + cor_opcoes + r')\s+(?:Masculino|Feminino)',
            texto, re.IGNORECASE
        )
    if cor_match:
        resultado["cor_raca"] = cor_match.group(1).strip().capitalize()

    # Grau de instrucao - pode estar na mesma linha com sexo/cor
    grau_match = re.search(
        r'(Ensino\s+(?:Fundamental|M[eé]dio|Superior)\s+(?:Completo|Incompleto))',
        texto, re.IGNORECASE
    )
    if grau_match:
        resultado["grau_instrucao"] = grau_match.group(1).strip()

    # Telefone celular
    tel_match = re.search(
        r'Telefone\s+Celular.*?(\d{2}[\s-]?\d{8,9})',
        texto, re.DOTALL
    )
    if not tel_match:
        tel_match = re.search(
            r'Celular.*?(\d{2}[\s-]?9?\d{8})',
            texto, re.DOTALL
        )
    if tel_match:
        resultado["telefone"] = re.sub(r'[^0-9]', '', tel_match.group(1))

    # Cargo e Funcao - na mesma linha aparece CARGO FUNCAO CBO
    # Ex: "AUXILIAR DE SERVIÇOS GERAIS AUXILIAR DE SERVIÇOS GERAIS 514320"
    # Cargo e Funcao costumam ser iguais; capturar ate o CBO
    cargo_match = re.search(
        r'Cargo\s+Fun[cç][aã]o.*?C\.?B\.?O\.?\s*\n(.+?)\s+(\d{5,})\s*$',
        texto, re.MULTILINE | re.IGNORECASE
    )
    if cargo_match:
        linha_valores = cargo_match.group(1).strip()
        # Remover o CBO do final
        resultado["cbo"] = cargo_match.group(2)
        # Separar cargo e funcao - podem ser iguais sem espaco duplo entre eles
        partes = re.split(r'\s{2,}', linha_valores)
        if len(partes) >= 2:
            resultado["cargo"] = partes[0].strip()
        else:
            # Cargo e Funcao iguais colados — pegar primeira metade
            # Verificar se a string se repete
            metade = len(linha_valores) // 2
            primeira_metade = linha_valores[:metade].strip()
            segunda_metade = linha_valores[metade:].strip()
            if primeira_metade.upper() == segunda_metade.upper():
                resultado["cargo"] = primeira_metade
            else:
                resultado["cargo"] = linha_valores
    if "cargo" not in resultado:
        # Fallback: capturar linha inteira apos "Cargo Funcao"
        cargo_match = re.search(
            r'Cargo\s+Fun[cç][aã]o.*?\n(.+)',
            texto
        )
        if cargo_match:
            linha = cargo_match.group(1).strip()
            # Remover numero CBO do final
            linha_sem_cbo = re.sub(r'\s+\d{5,}\s*$', '', linha)
            # Verificar repeticao cargo=funcao
            metade = len(linha_sem_cbo) // 2
            primeira_metade = linha_sem_cbo[:metade].strip()
            segunda_metade = linha_sem_cbo[metade:].strip()
            if primeira_metade.upper() == segunda_metade.upper():
                resultado["cargo"] = primeira_metade
            else:
                partes = re.split(r'\s{2,}', linha_sem_cbo)
                resultado["cargo"] = partes[0].strip() if partes else linha_sem_cbo

    # CBO - se nao foi capturado junto com cargo
    if "cbo" not in resultado:
        cbo_match = re.search(r'C\.?B\.?O\.?\s*\n.*?(\d{5,})', texto, re.DOTALL)
        if not cbo_match:
            cbo_match = re.search(r'(\d{5,})\s*\n.*?Data\s+de\s+Admiss', texto, re.DOTALL)
        if cbo_match:
            resultado["cbo"] = cbo_match.group(1)

    # Data de Admissao
    adm_match = re.search(
        r'Data\s+de\s+Admiss[aã]o.*?(\d{2}/\d{2}/\d{4})',
        texto, re.DOTALL
    )
    if adm_match:
        resultado["admissao"] = _converte_data(adm_match.group(1))

    # Salario
    sal_match = re.search(r'R\$\s*([\d.,]+)', texto)
    if sal_match:
        resultado["salario"] = sal_match.group(1)

    # Horario de trabalho
    hor_match = re.search(
        r'das\s+(\d{1,2}:\d{2})\s+as\s+(\d{1,2}:\d{2})',
        texto, re.IGNORECASE
    )
    if not hor_match:
        hor_match = re.search(
            r'(\d{1,2}:\d{2}).*?(\d{1,2}:\d{2})',
            texto
        )
    if hor_match:
        resultado["horario_trabalho"] = f"{hor_match.group(1)} as {hor_match.group(2)}"

    # CNPJ empregador
    cnpj_match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
    if cnpj_match:
        resultado["cnpj_empregador"] = cnpj_match.group(1)

    # PIS
    pis_match = re.search(r'PIS.*?([\d.]+-\d)', texto, re.DOTALL)
    if pis_match:
        resultado["pis"] = pis_match.group(1)

    # Deficiencia
    def_match = re.search(
        r'Defici[eê]ncia.*?(Sim|N[aã]o|Nao)',
        texto, re.DOTALL | re.IGNORECASE
    )
    if def_match:
        resultado["deficiencia"] = def_match.group(1).strip()

    # Endereco residencial
    end_match = re.search(
        r'Resid[eê]ncia.*?\n(.*?CEP:\s*\d{5}-\d{3})',
        texto, re.DOTALL
    )
    if end_match:
        resultado["endereco"] = end_match.group(1).strip()

    return resultado


def _extrair_contrato(texto: str) -> dict:
    """Extrai campos do Contrato de Experiencia."""
    resultado = {}

    # Nome do empregado - "Sr.(a) NOME"
    nome_match = re.search(
        r'Sr\(a\)\.?\s+([A-Z\s]+?),\s+domiciliado',
        texto, re.IGNORECASE
    )
    if nome_match:
        resultado["nome"] = nome_match.group(1).strip()

    # CTPS
    ctps_match = re.search(
        r'CTPS\s*N?[\xba\u00ba0]?:?\s*(\d+)\s*s[eé]rie\s*(\d+)',
        texto, re.IGNORECASE
    )
    if ctps_match:
        resultado["ctps_numero"] = ctps_match.group(1)
        resultado["ctps_serie"] = ctps_match.group(2)

    # Cargo/Funcao
    cargo_match = re.search(
        r'fun[cç][aã]o\s+de\s+([A-Z\s]+?)\s+e\s+mais\s+as',
        texto, re.IGNORECASE
    )
    if cargo_match:
        resultado["cargo"] = cargo_match.group(1).strip()

    # Local de trabalho / Loja
    loja_match = re.search(
        r'local\s+de\s+trabalho\s+situa-se\s+na\s+(.*?),\s+podendo',
        texto, re.IGNORECASE
    )
    if loja_match:
        resultado["loja"] = loja_match.group(1).strip()

    # Salario
    sal_match = re.search(
        r'remunera[cç][aã]o\s+de:\s*R\$\s*([\d.,]+)',
        texto, re.IGNORECASE
    )
    if sal_match:
        resultado["salario"] = sal_match.group(1)

    # Prazo experiencia + datas
    prazo_match = re.search(
        r'prazo\s+deste\s+contrato\s+[eé]\s+de\s+(\d+).*?'
        r'in[ií]cio\s+em:\s*(\d{2}/\d{2}/\d{4})\s+e\s+'
        r't[eé]rmino\s+em:\s*(\d{2}/\d{2}/\d{4})',
        texto, re.IGNORECASE
    )
    if prazo_match:
        resultado["experiencia_dias"] = int(prazo_match.group(1))
        resultado["contrato_inicio"] = _converte_data(prazo_match.group(2))
        resultado["contrato_fim"] = _converte_data(prazo_match.group(3))
        resultado["admissao"] = _converte_data(prazo_match.group(2))

    # CNPJ
    cnpj_match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
    if cnpj_match:
        resultado["cnpj_empregador"] = cnpj_match.group(1)

    # Horario
    hor_match = re.search(
        r'(\d{1,2}:\d{2}).*?(\d{1,2}:\d{2})',
        texto
    )
    if hor_match:
        resultado["horario_trabalho"] = f"{hor_match.group(1)} as {hor_match.group(2)}"

    return resultado


def mesclar_campos(campos_registro: dict, campos_contrato: dict) -> dict:
    """Mescla campos extraidos do Registro e do Contrato.

    O Contrato tem prioridade para campos de experiencia.
    O Registro tem prioridade para dados pessoais.
    """
    mesclado = {}
    mesclado.update(campos_registro)
    mesclado.update(campos_contrato)

    # Garantir dados pessoais do Registro
    for campo in ["nome", "cpf", "rg", "data_nascimento", "sexo",
                  "cor_raca", "estado_civil", "grau_instrucao",
                  "nome_pai", "nome_mae", "endereco", "telefone",
                  "ctps_numero", "ctps_serie", "titulo_eleitoral", "pis",
                  "matricula"]:
        if campo in campos_registro and campos_registro[campo]:
            mesclado[campo] = campos_registro[campo]

    # Garantir campos do Contrato para experiencia (somente se existirem no contrato)
    for campo in ["experiencia_dias", "contrato_inicio", "contrato_fim",
                  "salario", "cargo", "loja"]:
        if campo in campos_contrato and campos_contrato[campo]:
            mesclado[campo] = campos_contrato[campo]

    # CBO: prioridade Registro (contrato geralmente nao tem)
    if "cbo" in campos_registro and campos_registro["cbo"]:
        mesclado["cbo"] = campos_registro["cbo"]

    return mesclado


def campos_para_sistema(campos: dict) -> dict:
    """Converte campos extraidos para formato do sistema de cadastro."""
    import calculos as cal

    sistema = {}

    mapa_direto = {
        "matricula": "matricula",
        "nome": "nome",
        "rg": "rg",
        "cpf": "cpf",
        "telefone": "telefone",
        "cargo": "cargo",
        "loja": "loja",
    }
    for origem, destino in mapa_direto.items():
        if origem in campos and campos[origem]:
            sistema[destino] = str(campos[origem])

    # Admissao
    if "admissao" in campos and campos["admissao"]:
        sistema["admissao"] = campos["admissao"]

    # Experiencia dias
    if "experiencia_dias" in campos and campos["experiencia_dias"]:
        try:
            sistema["experiencia_dias"] = int(campos["experiencia_dias"])
        except (ValueError, TypeError):
            pass

    # Formata telefone
    if "telefone" in sistema:
        sistema["telefone"] = cal.formatar_telefone(sistema["telefone"])

    # Formata CPF
    if "cpf" in sistema:
        digitos = ''.join(filter(str.isdigit, sistema["cpf"]))
        sistema["cpf"] = cal.formatar_cpf(digitos)

    # Situacao padrao
    sistema.setdefault("situacao", "Ativo")

    # Observacao com campos extras
    extras = []
    if campos.get("salario"):
        extras.append(f"Salario: R$ {campos['salario']}")
    if campos.get("cbo"):
        extras.append(f"CBO: {campos['cbo']}")
    if campos.get("sexo"):
        extras.append(f"Sexo: {campos['sexo']}")
    if campos.get("cor_raca"):
        extras.append(f"Cor/Raca: {campos['cor_raca']}")
    if campos.get("estado_civil"):
        extras.append(f"Estado Civil: {campos['estado_civil']}")
    if campos.get("grau_instrucao"):
        extras.append(f"Grau Instrucao: {campos['grau_instrucao']}")
    if campos.get("data_nascimento"):
        extras.append(f"Nascimento: {campos['data_nascimento']}")
    if campos.get("endereco"):
        extras.append(f"Endereco: {campos['endereco']}")
    if campos.get("nome_pai"):
        extras.append(f"Pai: {campos['nome_pai']}")
    if campos.get("nome_mae"):
        extras.append(f"Mae: {campos['nome_mae']}")
    if campos.get("ctps_numero"):
        ctps_info = f"CTPS: {campos['ctps_numero']}"
        if campos.get("ctps_serie"):
            ctps_info += f" Serie {campos['ctps_serie']}"
        extras.append(ctps_info)
    if campos.get("titulo_eleitoral"):
        extras.append(f"Titulo Eleitoral: {campos['titulo_eleitoral']}")
    if campos.get("pis"):
        extras.append(f"PIS: {campos['pis']}")
    if campos.get("cnpj_empregador"):
        extras.append(f"CNPJ Empregador: {campos['cnpj_empregador']}")
    if campos.get("horario_trabalho"):
        extras.append(f"Horario: {campos['horario_trabalho']}")
    if campos.get("contrato_inicio"):
        extras.append(f"Contrato Inicio: {campos['contrato_inicio']}")
    if campos.get("contrato_fim"):
        extras.append(f"Contrato Fim: {campos['contrato_fim']}")

    if extras:
        sistema["observacao"] = " | ".join(extras)

    return sistema


def ler_documento_pdf(arquivo_upload) -> str:
    """Le texto de um PDF usando pdfplumber ou PyPDF2."""
    # Salvar em temp se for stream do Streamlit
    import io as _io
    dados = arquivo_upload.read()
    arquivo_upload.seek(0)

    try:
        import pdfplumber
        buf = _io.BytesIO(dados)
        with pdfplumber.open(buf) as pdf:
            paginas = []
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    paginas.append(texto)
            return "\n".join(paginas)
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader
        buf = _io.BytesIO(dados)
        reader = PdfReader(buf)
        paginas = []
        for pagina in reader.pages:
            texto = pagina.extract_text()
            if texto:
                paginas.append(texto)
        return "\n".join(paginas)
    except ImportError:
        pass

    return ""


def ler_documento_imagem(arquivo_upload) -> str:
    """Le texto de uma imagem via OCR (tesseract)."""
    try:
        import pytesseract
        from PIL import Image
        import io as _io
        dados = arquivo_upload.read()
        arquivo_upload.seek(0)
        img = Image.open(_io.BytesIO(dados))
        return pytesseract.image_to_string(img, lang='por')
    except ImportError:
        return ""


def ler_documento(arquivo_upload) -> str:
    """Le texto de um documento (PDF ou imagem)."""
    nome = getattr(arquivo_upload, 'name', '') or ''
    if nome.lower().endswith('.pdf'):
        return ler_documento_pdf(arquivo_upload)
    return ler_documento_imagem(arquivo_upload)