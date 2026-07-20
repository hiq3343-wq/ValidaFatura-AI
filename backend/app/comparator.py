import re
import unicodedata
from datetime import date

from rapidfuzz import fuzz


MESES = {
    "JAN": 1,
    "FEV": 2,
    "MAR": 3,
    "ABR": 4,
    "MAI": 5,
    "JUN": 6,
    "JUL": 7,
    "AGO": 8,
    "SET": 9,
    "OUT": 10,
    "NOV": 11,
    "DEZ": 12,
}


def normalizar_empresa(nome: str) -> str:
    nome = nome.upper()

    nome = unicodedata.normalize("NFD", nome)

    nome = "".join(
        caractere
        for caractere in nome
        if unicodedata.category(caractere) != "Mn"
    )

    nome = re.sub(
        r"\b(LTDA|SA|S A|EIRELI|ME|EPP)\b",
        "",
        nome
    )

    nome = re.sub(
        r"\bPARCELA\s+\d+\s*/\s*\d+\b",
        "",
        nome
    )

    nome = re.sub(r"[^A-Z0-9 ]", " ", nome)
    nome = re.sub(r"\s+", " ", nome)

    return nome.strip()


def extrair_data(
    data_texto: str | None
) -> tuple[int, int, int | None] | None:
    if not data_texto:
        return None

    texto = data_texto.upper().strip()

    resultado_textual = re.search(
        r"\b(\d{1,2})\s+([A-ZÇ]{3})"
        r"(?:\s+(\d{4}))?\b",
        texto
    )

    if resultado_textual:
        dia = int(resultado_textual.group(1))
        mes = MESES.get(resultado_textual.group(2))
        ano_texto = resultado_textual.group(3)

        if not mes:
            return None

        return (
            dia,
            mes,
            int(ano_texto) if ano_texto else None,
        )

    resultado_numerico = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
        texto
    )

    if resultado_numerico:
        dia = int(resultado_numerico.group(1))
        mes = int(resultado_numerico.group(2))
        ano = int(resultado_numerico.group(3))

        try:
            date(ano, mes, dia)
        except ValueError:
            return None

        return dia, mes, ano

    return None


def diferenca_dias(
    data_recibo: str | None,
    data_fatura: str | None
) -> int | None:
    recibo = extrair_data(data_recibo)
    fatura = extrair_data(data_fatura)

    if not recibo or not fatura:
        return None

    dia_recibo, mes_recibo, ano_recibo = recibo
    dia_fatura, mes_fatura, ano_fatura = fatura

    ano_recibo_final = ano_recibo or ano_fatura or 2026
    ano_fatura_final = ano_fatura or ano_recibo or 2026

    try:
        primeira_data = date(
            ano_recibo_final,
            mes_recibo,
            dia_recibo
        )

        segunda_data = date(
            ano_fatura_final,
            mes_fatura,
            dia_fatura
        )

        return abs(
            (primeira_data - segunda_data).days
        )

    except ValueError:
        return None


def obter_valor_comparacao(
    recibo: dict
) -> tuple[float, bool]:
    """
    Retorna o valor em BRL usado na comparação e informa
    se houve tratamento cambial.
    """
    moeda = str(
        recibo.get("moeda", "BRL")
    ).upper()

    valor_convertido = recibo.get(
        "valor_convertido"
    )

    if valor_convertido not in {
        None,
        "",
    }:
        try:
            return float(valor_convertido), moeda != "BRL"
        except (TypeError, ValueError):
            pass

    valor_original = recibo.get(
        "valor_original"
    )

    cotacao = recibo.get("cotacao")

    if (
        moeda != "BRL"
        and valor_original not in {None, ""}
        and cotacao not in {None, ""}
    ):
        try:
            valor_calculado = (
                float(valor_original)
                * float(cotacao)
            )

            return round(valor_calculado, 2), True

        except (TypeError, ValueError):
            pass

    try:
        return float(recibo.get("valor", 0)), False

    except (TypeError, ValueError):
        return 0.0, False


def verificar_parcelamento(
    compra_fatura: dict,
    valor_recibo: float,
    valor_fatura: float
) -> bool:
    total_parcelas = compra_fatura.get(
        "total_parcelas"
    )

    if total_parcelas:
        try:
            quantidade = int(total_parcelas)

            if quantidade > 0:
                valor_estimado = (
                    valor_recibo / quantidade
                )

                return abs(
                    valor_estimado - valor_fatura
                ) <= 0.05

        except (TypeError, ValueError):
            pass

    empresa_fatura = str(
        compra_fatura.get("empresa", "")
    )

    parcela_no_nome = re.search(
        r"PARCELA\s+\d+\s*/\s*(\d+)",
        empresa_fatura.upper()
    )

    if not parcela_no_nome:
        return False

    quantidade = int(
        parcela_no_nome.group(1)
    )

    if quantidade <= 0:
        return False

    valor_estimado = (
        valor_recibo / quantidade
    )

    return abs(
        valor_estimado - valor_fatura
    ) <= 0.05


def definir_status(
    parcelada: bool,
    diferenca: int | None,
    conversao_cambial: bool,
    tipo_documento: str | None
) -> tuple[str, str]:
    if parcelada:
        return (
            "confirmado",
            "CONFIRMADO - PARCELADO"
        )

    if (
        diferenca is not None
        and diferenca > 2
    ):
        return (
            "divergencia_data",
            "DATA DIFERENTE"
        )

    if conversao_cambial:
        return (
            "confirmado",
            "CONFIRMADO - CONVERSÃO CAMBIAL"
        )

    if tipo_documento == "nota_fiscal":
        return (
            "confirmado",
            "CONFIRMADO - ITEM DA NF"
        )

    return (
        "confirmado",
        "CONFIRMADO"
    )


def dados_extras_recibo(
    recibo: dict
) -> dict:
    return {
        "tipo_documento": recibo.get(
            "tipo_documento"
        ),
        "descricao_item": recibo.get(
            "descricao_item"
        ),
        "moeda": recibo.get(
            "moeda",
            "BRL"
        ),
        "valor_original": recibo.get(
            "valor_original"
        ),
        "valor_convertido": recibo.get(
            "valor_convertido"
        ),
        "cotacao": recibo.get(
            "cotacao"
        ),
    }


def comparar_transacoes(
    fatura: list[dict],
    recibos: list[dict]
) -> list[dict]:
    resultados = []
    indices_utilizados: set[int] = set()

    for recibo in recibos:
        empresa_recibo = normalizar_empresa(
            str(recibo.get("empresa", ""))
        )

        valor_recibo, conversao_cambial = (
            obter_valor_comparacao(recibo)
        )

        tolerancia_valor = (
            0.15
            if conversao_cambial
            else 0.02
        )

        candidatos = []

        for indice, compra in enumerate(fatura):
            if indice in indices_utilizados:
                continue

            empresa_fatura_original = str(
                compra.get("empresa", "")
            )

            empresa_fatura = normalizar_empresa(
                empresa_fatura_original
            )

            valor_fatura = float(
                compra.get("valor", 0)
            )

            valores_iguais = (
                abs(
                    valor_recibo - valor_fatura
                ) <= tolerancia_valor
            )

            compra_parcelada = (
                verificar_parcelamento(
                    compra,
                    valor_recibo,
                    valor_fatura
                )
            )

            if (
                not valores_iguais
                and not compra_parcelada
            ):
                continue

            similaridade = fuzz.token_set_ratio(
                empresa_recibo,
                empresa_fatura
            )

            if similaridade < 55:
                continue

            diferenca = diferenca_dias(
                recibo.get("data"),
                compra.get("data")
            )

            candidatos.append({
                "indice": indice,
                "compra": compra,
                "similaridade": round(
                    float(similaridade),
                    2
                ),
                "parcelada": compra_parcelada,
                "diferenca": diferenca,
            })

        if not candidatos:
            moeda = str(
                recibo.get("moeda", "BRL")
            ).upper()

            resultado = (
                "revisao_cambial"
                if moeda != "BRL"
                else "nao_encontrado"
            )

            status = (
                "REVISÃO CAMBIAL"
                if moeda != "BRL"
                else "NÃO ENCONTRADO"
            )

            resultados.append({
                "resultado": resultado,
                "status": status,
                "empresa": recibo.get("empresa"),
                "empresa_fatura": None,
                "recibo": valor_recibo,
                "fatura": None,
                "data_recibo": recibo.get("data"),
                "data_fatura": None,
                "diferenca_dias": None,
                "similaridade": None,
                "parcela_atual": recibo.get(
                    "parcela_atual"
                ),
                "total_parcelas": recibo.get(
                    "total_parcelas"
                ),
                "arquivo_origem": recibo.get(
                    "arquivo_origem"
                ),
                **dados_extras_recibo(recibo),
            })

            continue

        melhor_candidato = max(
            candidatos,
            key=lambda candidato: (
                candidato["similaridade"],
                -(
                    candidato["diferenca"]
                    if candidato["diferenca"]
                    is not None
                    else 9999
                ),
            )
        )

        indice = melhor_candidato["indice"]
        compra = melhor_candidato["compra"]
        parcelada = melhor_candidato["parcelada"]
        similaridade = melhor_candidato[
            "similaridade"
        ]
        diferenca = melhor_candidato[
            "diferenca"
        ]

        indices_utilizados.add(indice)

        resultado, status = definir_status(
            parcelada=parcelada,
            diferenca=diferenca,
            conversao_cambial=conversao_cambial,
            tipo_documento=recibo.get(
                "tipo_documento"
            ),
        )

        parcela_atual = (
            compra.get("parcela_atual")
            or recibo.get("parcela_atual")
        )

        total_parcelas = (
            compra.get("total_parcelas")
            or recibo.get("total_parcelas")
        )

        resultados.append({
            "resultado": resultado,
            "status": status,
            "empresa": recibo.get("empresa"),
            "empresa_fatura": compra.get(
                "empresa"
            ),
            "recibo": valor_recibo,
            "fatura": float(
                compra.get("valor", 0)
            ),
            "data_recibo": recibo.get("data"),
            "data_fatura": compra.get("data"),
            "diferenca_dias": diferenca,
            "similaridade": similaridade,
            "parcela_atual": parcela_atual,
            "total_parcelas": total_parcelas,
            "arquivo_origem": recibo.get(
                "arquivo_origem"
            ),
            **dados_extras_recibo(recibo),
        })

    for indice, compra in enumerate(fatura):
        if indice in indices_utilizados:
            continue

        resultados.append({
            "resultado": "sem_comprovante",
            "status": "SEM COMPROVANTE",
            "empresa": compra.get("empresa"),
            "empresa_fatura": compra.get(
                "empresa"
            ),
            "recibo": None,
            "fatura": float(
                compra.get("valor", 0)
            ),
            "data_recibo": None,
            "data_fatura": compra.get("data"),
            "diferenca_dias": None,
            "similaridade": None,
            "parcela_atual": compra.get(
                "parcela_atual"
            ),
            "total_parcelas": compra.get(
                "total_parcelas"
            ),
            "arquivo_origem": None,
            "tipo_documento": None,
            "descricao_item": None,
            "moeda": "BRL",
            "valor_original": None,
            "valor_convertido": None,
            "cotacao": None,
        })

    return resultados
