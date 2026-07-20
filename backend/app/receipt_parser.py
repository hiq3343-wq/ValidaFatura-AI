import re
import unicodedata


MESES = (
    "JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|"
    "SET|OUT|NOV|DEZ"
)


ROTULOS_EMPRESA = (
    "ESTABELECIMENTO",
    "FAVORECIDO",
    "DESTINATARIO",
    "DESTINATÁRIO",
    "RECEBEDOR",
    "BENEFICIARIO",
    "BENEFICIÁRIO",
    "COMERCIO",
    "COMÉRCIO",
    "LOJA",
)


TERMOS_IGNORADOS_EMPRESA = {
    "COMPROVANTE",
    "COMPROVANTE DE PAGAMENTO",
    "PAGAMENTO",
    "TRANSFERENCIA",
    "TRANSFERÊNCIA",
    "TRANSACAO",
    "TRANSAÇÃO",
    "APROVADA",
    "APROVADO",
    "DATA",
    "HORA",
    "VALOR",
    "TOTAL",
    "CNPJ",
    "CPF",
    "PIX",
    "BANCO",
    "AGENCIA",
    "AGÊNCIA",
    "CONTA",
    "AUTENTICACAO",
    "AUTENTICAÇÃO",
    "CODIGO",
    "CÓDIGO",
    "CODIGO DE AUTORIZACAO",
    "CÓDIGO DE AUTORIZAÇÃO",
    "NSU",
    "CARTAO",
    "CARTÃO",
    "DEBITO",
    "DÉBITO",
    "CREDITO",
    "CRÉDITO",
    "ORIGEM",
    "DESTINO",
    "NOME",
    "INSTITUICAO",
    "INSTITUIÇÃO",
    "TIPO DE TRANSFERENCIA",
    "TIPO DE TRANSFERÊNCIA",
    "A VISTA",
    "À VISTA",
    "ID DA TRANSACAO",
    "ID DA TRANSAÇÃO",
    "ME AJUDA",
    "OUVIDORIA",
    "NU PAGAMENTOS",
}


FRASES_IGNORADAS_EMPRESA = (
    "ESTAMOS AQUI PARA AJUDAR",
    "SE VOCE TIVER ALGUMA DUVIDA",
    "SE VOCÊ TIVER ALGUMA DÚVIDA",
    "ATENDIMENTO EM DIAS UTEIS",
    "ATENDIMENTO EM DIAS ÚTEIS",
    "DEMAIS CANAIS",
    "OUVIDORIA",
    "NUBANK.COM.BR",
    "COMPROVANTE DE PAGAMENTO",
    "TIPO DE TRANSFERENCIA",
    "TIPO DE TRANSFERÊNCIA",
    "CODIGO DE AUTORIZACAO",
    "CÓDIGO DE AUTORIZAÇÃO",
    "ID DA TRANSACAO",
    "ID DA TRANSAÇÃO",
)


def limpar_texto(texto: str) -> str:
    texto = texto.replace("\r", "\n")

    linhas = [
        re.sub(r"\s+", " ", linha).strip()
        for linha in texto.splitlines()
    ]

    return "\n".join(
        linha
        for linha in linhas
        if linha
    )


def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    return texto.upper()


def converter_valor(
    valor_texto: str
) -> float:
    valor_texto = valor_texto.strip()
    valor_texto = valor_texto.replace("R$", "")
    valor_texto = valor_texto.replace(" ", "")

    if "," in valor_texto:
        valor_texto = valor_texto.replace(".", "")
        valor_texto = valor_texto.replace(",", ".")

    return float(valor_texto)


def extrair_valor(
    texto: str
) -> float | None:
    texto_normalizado = normalizar_texto(texto)

    padroes = [
        r"R\$\s*(\d{1,6}(?:\.\d{3})*,\d{2})",

        r"(?:VALOR|TOTAL|PAGO|PAGAMENTO)"
        r"[^0-9]{0,30}"
        r"R?\$?\s*"
        r"(\d{1,6}(?:\.\d{3})*,\d{2})",

        r"R\$\s*(\d{1,6}\.\d{2})",
    ]

    for padrao in padroes:
        resultado = re.search(
            padrao,
            texto_normalizado,
            flags=re.IGNORECASE
        )

        if not resultado:
            continue

        try:
            return converter_valor(
                resultado.group(1)
            )

        except ValueError:
            continue

    candidatos = re.findall(
        r"(?<!\d)"
        r"(\d{1,6}[,.]\d{2})"
        r"(?!\d)",
        texto_normalizado
    )

    valores = []

    for candidato in candidatos:
        try:
            valor = converter_valor(candidato)

            if valor > 0:
                valores.append(valor)

        except ValueError:
            continue

    if not valores:
        return None

    return max(valores)


def extrair_data(
    texto: str
) -> str | None:
    texto_normalizado = normalizar_texto(texto)

    padroes = [
        rf"\b(\d{{1,2}}\s+(?:{MESES})\s+\d{{4}}"
        r"(?:\s*[-–]\s*\d{1,2}:\d{2})?)\b",

        rf"\b(\d{{1,2}}\s+(?:{MESES})\s+\d{{4}})\b",

        r"\b(\d{1,2}/\d{1,2}/\d{4}"
        r"(?:\s*[-–]?\s*\d{1,2}:\d{2})?)\b",

        r"\b(\d{1,2}-\d{1,2}-\d{4}"
        r"(?:\s+\d{1,2}:\d{2})?)\b",
    ]

    for padrao in padroes:
        resultado = re.search(
            padrao,
            texto_normalizado
        )

        if resultado:
            return resultado.group(1)

    return None


def linha_parece_empresa(
    linha: str
) -> bool:
    linha_limpa = linha.strip()
    linha_normalizada = normalizar_texto(
        linha_limpa
    )

    if len(linha_normalizada) < 3:
        return False

    if linha_normalizada in {
        normalizar_texto(termo)
        for termo in TERMOS_IGNORADOS_EMPRESA
    }:
        return False

    if any(
        normalizar_texto(frase) in linha_normalizada
        for frase in FRASES_IGNORADAS_EMPRESA
    ):
        return False

    if re.fullmatch(
        r"[\d\s./:,*-]+",
        linha_normalizada
    ):
        return False

    if re.search(
        r"\b\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}\b",
        linha_normalizada
    ):
        return False

    if re.search(
        r"\b\d{2}\.?\d{3}\.?\d{3}/\d{4}-?\d{2}\b",
        linha_normalizada
    ):
        return False

    if re.search(
        r"\bR\$\s*\d",
        linha_normalizada
    ):
        return False

    if re.search(
        r"\b\d{1,2}\s+(?:"
        + MESES
        + r")\b",
        linha_normalizada
    ):
        return False

    if len(linha_normalizada) > 60:
        return False

    quantidade_letras = sum(
        caractere.isalpha()
        for caractere in linha_normalizada
    )

    return quantidade_letras >= 3


def extrair_valor_rotulo_mesma_linha(
    linha: str,
    rotulo: str
) -> str | None:
    linha_normalizada = normalizar_texto(linha)
    rotulo_normalizado = normalizar_texto(rotulo)

    posicao = linha_normalizada.find(
        rotulo_normalizado
    )

    if posicao == -1:
        return None

    valor = linha[
        posicao + len(rotulo):
    ].strip(" :-–")

    if (
        valor
        and linha_parece_empresa(valor)
    ):
        return valor

    return None


def extrair_empresa_por_rotulo(
    linhas: list[str]
) -> str | None:
    for indice, linha in enumerate(linhas):
        linha_normalizada = normalizar_texto(
            linha
        )

        for rotulo in ROTULOS_EMPRESA:
            rotulo_normalizado = normalizar_texto(
                rotulo
            )

            if rotulo_normalizado not in linha_normalizada:
                continue

            valor_mesma_linha = (
                extrair_valor_rotulo_mesma_linha(
                    linha,
                    rotulo
                )
            )

            if valor_mesma_linha:
                return valor_mesma_linha

            for deslocamento in range(1, 4):
                proximo_indice = indice + deslocamento

                if proximo_indice >= len(linhas):
                    break

                candidato = linhas[proximo_indice]

                if linha_parece_empresa(candidato):
                    return candidato

    return None


def pontuar_candidato_empresa(
    linha: str,
    indice: int,
    total_linhas: int
) -> float:
    linha_normalizada = normalizar_texto(linha)

    pontuacao = 0.0

    quantidade_letras = sum(
        caractere.isalpha()
        for caractere in linha_normalizada
    )

    pontuacao += min(
        quantidade_letras,
        25
    )

    quantidade_palavras = len(
        linha_normalizada.split()
    )

    if 1 <= quantidade_palavras <= 4:
        pontuacao += 12

    if len(linha_normalizada) <= 30:
        pontuacao += 8

    if indice < total_linhas * 0.75:
        pontuacao += 4

    if any(
        termo in linha_normalizada
        for termo in (
            "PAGAMENTOS",
            "BANCO",
            "INSTITUICAO",
            "INSTITUIÇÃO",
        )
    ):
        pontuacao -= 15

    if quantidade_palavras > 7:
        pontuacao -= 20

    if len(linha_normalizada) > 45:
        pontuacao -= 20

    return pontuacao


def extrair_empresa_por_heuristica(
    linhas: list[str]
) -> str | None:
    candidatos = []

    total_linhas = len(linhas)

    for indice, linha in enumerate(linhas):
        if not linha_parece_empresa(linha):
            continue

        candidatos.append({
            "linha": linha,
            "pontuacao": pontuar_candidato_empresa(
                linha,
                indice,
                total_linhas
            ),
        })

    if not candidatos:
        return None

    melhor = max(
        candidatos,
        key=lambda candidato: candidato["pontuacao"]
    )

    return melhor["linha"]


def extrair_empresa(
    texto: str
) -> str | None:
    linhas = limpar_texto(texto).splitlines()

    empresa_rotulada = extrair_empresa_por_rotulo(
        linhas
    )

    if empresa_rotulada:
        return empresa_rotulada

    return extrair_empresa_por_heuristica(
        linhas
    )


def extrair_parcelamento(
    texto: str
) -> tuple[int | None, int | None]:
    texto_normalizado = normalizar_texto(texto)

    resultado_fracao = re.search(
        r"(?:PARCELA\s*)?"
        r"(\d{1,2})\s*/\s*(\d{1,2})",
        texto_normalizado
    )

    if resultado_fracao:
        parcela_atual = int(
            resultado_fracao.group(1)
        )

        total_parcelas = int(
            resultado_fracao.group(2)
        )

        if (
            parcela_atual > 0
            and total_parcelas > 0
            and parcela_atual <= total_parcelas
        ):
            return (
                parcela_atual,
                total_parcelas
            )

    resultado_x = re.search(
        r"\b(\d{1,2})\s*[Xx]\b",
        texto_normalizado
    )

    if resultado_x:
        total_parcelas = int(
            resultado_x.group(1)
        )

        if total_parcelas > 0:
            return (
                1,
                total_parcelas
            )

    resultado_textual = re.search(
        r"\b(?:PARCELADO\s+EM|EM)"
        r"\s+(\d{1,2})\s+PARCELAS?\b",
        texto_normalizado
    )

    if resultado_textual:
        total_parcelas = int(
            resultado_textual.group(1)
        )

        if total_parcelas > 0:
            return (
                1,
                total_parcelas
            )

    if re.search(
        r"\bA\s+VISTA\b",
        texto_normalizado
    ):
        return None, None

    return None, None


def eh_nota_fiscal(texto: str) -> bool:
    texto_normalizado = normalizar_texto(texto)

    indicadores = (
        "NOTA FISCAL",
        "NF-E",
        "NFE",
        "DANFE",
        "DOCUMENTO AUXILIAR DA NOTA FISCAL",
    )

    return any(
        indicador in texto_normalizado
        for indicador in indicadores
    )


def extrair_empresa_nota_fiscal(
    texto: str
) -> str | None:
    linhas = limpar_texto(texto).splitlines()

    rotulos = (
        "EMITENTE",
        "RAZAO SOCIAL",
        "RAZÃO SOCIAL",
        "FORNECEDOR",
    )

    for indice, linha in enumerate(linhas):
        linha_normalizada = normalizar_texto(linha)

        for rotulo in rotulos:
            rotulo_normalizado = normalizar_texto(rotulo)

            if rotulo_normalizado not in linha_normalizada:
                continue

            valor_mesma_linha = (
                extrair_valor_rotulo_mesma_linha(
                    linha,
                    rotulo
                )
            )

            if valor_mesma_linha:
                return valor_mesma_linha

            if indice + 1 < len(linhas):
                candidato = linhas[indice + 1]

                if linha_parece_empresa(candidato):
                    return candidato

    return extrair_empresa(texto)


def extrair_dados_cambiais(
    texto: str
) -> dict:
    texto_normalizado = normalizar_texto(texto)

    valor_original = None
    valor_convertido = None
    cotacao = None
    moeda = "BRL"

    padroes_valor_original = (
        r"\b(?:US\$|USD)\s*"
        r"(\d{1,6}(?:\.\d{3})*[,.]\d{2})\b",

        r"(?:VALOR ORIGINAL|ORIGINAL)"
        r"[^0-9]{0,25}"
        r"(\d{1,6}(?:\.\d{3})*[,.]\d{2})"
        r"\s*(?:USD|DOLARES?|DOLARS?)",
    )

    for padrao in padroes_valor_original:
        resultado = re.search(
            padrao,
            texto_normalizado
        )

        if resultado:
            try:
                valor_original = converter_valor(
                    resultado.group(1)
                )
                moeda = "USD"
                break
            except ValueError:
                pass

    padroes_valor_convertido = (
        r"(?:VALOR CONVERTIDO|CONVERTIDO EM REAIS|"
        r"VALOR EM BRL|VALOR EM REAIS)"
        r"[^0-9]{0,30}"
        r"R?\$?\s*"
        r"(\d{1,6}(?:\.\d{3})*[,.]\d{2})",

        r"(?:TOTAL CONVERTIDO)"
        r"[^0-9]{0,30}"
        r"R?\$?\s*"
        r"(\d{1,6}(?:\.\d{3})*[,.]\d{2})",
    )

    for padrao in padroes_valor_convertido:
        resultado = re.search(
            padrao,
            texto_normalizado
        )

        if resultado:
            try:
                valor_convertido = converter_valor(
                    resultado.group(1)
                )
                break
            except ValueError:
                pass

    padroes_cotacao = (
        r"(?:COTACAO|CÂMBIO|CAMBIO)"
        r"[^0-9]{0,30}"
        r"R?\$?\s*"
        r"(\d{1,3}[,.]\d{2,6})",

        r"R\$\s*(\d{1,3}[,.]\d{2,6})"
        r"\s*(?:POR|/)\s*(?:US\$|USD)",

        r"(?:1\s*(?:US\$|USD))"
        r"[^0-9]{0,20}"
        r"R\$\s*(\d{1,3}[,.]\d{2,6})",
    )

    for padrao in padroes_cotacao:
        resultado = re.search(
            padrao,
            texto_normalizado
        )

        if resultado:
            try:
                cotacao = converter_valor(
                    resultado.group(1)
                )
                break
            except ValueError:
                pass

    if (
        valor_convertido is None
        and valor_original is not None
        and cotacao is not None
    ):
        valor_convertido = round(
            valor_original * cotacao,
            2
        )

    return {
        "moeda": moeda,
        "valor_original": valor_original,
        "valor_convertido": valor_convertido,
        "cotacao": cotacao,
    }


def extrair_itens_nota_fiscal(
    texto: str,
    nome_arquivo: str | None = None
) -> list[dict]:
    linhas = limpar_texto(texto).splitlines()

    empresa = (
        extrair_empresa_nota_fiscal(texto)
        or "NÃO IDENTIFICADO"
    )

    data = extrair_data(texto)

    termos_ignorados = (
        "TOTAL",
        "SUBTOTAL",
        "DESCONTO",
        "FRETE",
        "IMPOSTO",
        "TRIBUTO",
        "VALOR DA NOTA",
        "VALOR TOTAL",
        "CNPJ",
        "CPF",
        "CHAVE DE ACESSO",
        "FORMA DE PAGAMENTO",
        "OBSERVACAO",
        "OBSERVAÇÃO",
    )

    padrao_valor_final = re.compile(
        r"(?:R\$\s*)?"
        r"(\d{1,6}(?:\.\d{3})*,\d{2}"
        r"|\d{1,6}\.\d{2})"
        r"\s*$",
        flags=re.IGNORECASE,
    )

    itens = []
    vistos = set()

    for linha in linhas:
        linha_normalizada = normalizar_texto(linha)

        if any(
            termo in linha_normalizada
            for termo in termos_ignorados
        ):
            continue

        resultado_valor = padrao_valor_final.search(
            linha
        )

        if not resultado_valor:
            continue

        try:
            valor = converter_valor(
                resultado_valor.group(1)
            )
        except ValueError:
            continue

        if valor <= 0:
            continue

        descricao = linha[
            :resultado_valor.start()
        ].strip(" :-–|")

        descricao = re.sub(
            r"\s+\d+(?:[,.]\d+)?\s*$",
            "",
            descricao
        ).strip(" :-–|")

        if not descricao:
            continue

        quantidade_letras = sum(
            caractere.isalpha()
            for caractere in descricao
        )

        if quantidade_letras < 3:
            continue

        chave = (
            normalizar_texto(descricao),
            round(valor, 2),
        )

        if chave in vistos:
            continue

        vistos.add(chave)

        itens.append({
            "empresa": empresa,
            "descricao_item": descricao,
            "valor": valor,
            "data": data,
            "parcela_atual": None,
            "total_parcelas": None,
            "arquivo_origem": nome_arquivo,
            "tipo_documento": "nota_fiscal",
            "moeda": "BRL",
            "valor_original": valor,
            "valor_convertido": valor,
            "cotacao": None,
        })

    return itens


def interpretar_comprovante(
    texto: str,
    nome_arquivo: str | None = None
) -> dict:
    empresa = extrair_empresa(texto)
    valor = extrair_valor(texto)
    data = extrair_data(texto)

    parcela_atual, total_parcelas = (
        extrair_parcelamento(texto)
    )

    dados_cambiais = extrair_dados_cambiais(
        texto
    )

    valor_convertido = dados_cambiais[
        "valor_convertido"
    ]

    valor_comparacao = (
        valor_convertido
        if valor_convertido is not None
        else valor
    )

    return {
        "empresa": empresa or "NÃO IDENTIFICADO",
        "valor": (
            valor_comparacao
            if valor_comparacao is not None
            else 0
        ),
        "data": data,
        "parcela_atual": parcela_atual,
        "total_parcelas": total_parcelas,
        "arquivo_origem": nome_arquivo,
        "tipo_documento": "comprovante",
        "moeda": dados_cambiais["moeda"],
        "valor_original": dados_cambiais[
            "valor_original"
        ],
        "valor_convertido": valor_convertido,
        "cotacao": dados_cambiais["cotacao"],
        "descricao_item": None,
    }


def interpretar_comprovantes(
    texto: str,
    nome_arquivo: str | None = None
) -> list[dict]:
    """
    Retorna uma lista porque um único documento pode
    representar uma ou várias transações.

    Comprovante comum:
        retorna uma lista com um elemento.

    Nota fiscal com vários itens:
        retorna uma transação para cada item identificado.
    """
    if eh_nota_fiscal(texto):
        itens = extrair_itens_nota_fiscal(
            texto,
            nome_arquivo
        )

        if itens:
            return itens

    return [
        interpretar_comprovante(
            texto,
            nome_arquivo
        )
    ]
