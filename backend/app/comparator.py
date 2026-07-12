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

    padrao = re.search(
        r"(\d{1,2})\s+([A-ZÇ]{3})"
        r"(?:\s+(\d{4}))?",
        texto
    )

    if not padrao:
        return None

    dia = int(padrao.group(1))
    mes_texto = padrao.group(2)
    ano_texto = padrao.group(3)

    mes = MESES.get(mes_texto)

    if not mes:
        return None

    ano = int(ano_texto) if ano_texto else None

    return dia, mes, ano


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

    ano = ano_recibo or ano_fatura or 2026

    try:
        primeira_data = date(
            ano,
            mes_recibo,
            dia_recibo
        )

        segunda_data = date(
            ano,
            mes_fatura,
            dia_fatura
        )

        return abs(
            (primeira_data - segunda_data).days
        )

    except ValueError:
        return None


def verificar_parcelamento(
    compra_fatura: dict,
    valor_recibo: float,
    valor_fatura: float
) -> bool:
    total_parcelas = compra_fatura.get("total_parcelas")

    if total_parcelas:
        try:
            quantidade = int(total_parcelas)

            if quantidade > 0:
                valor_estimado = valor_recibo / quantidade

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

    quantidade = int(parcela_no_nome.group(1))

    if quantidade <= 0:
        return False

    valor_estimado = valor_recibo / quantidade

    return abs(
        valor_estimado - valor_fatura
    ) <= 0.05


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

        valor_recibo = float(
            recibo.get("valor", 0)
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
                abs(valor_recibo - valor_fatura) <= 0.02
            )

            compra_parcelada = verificar_parcelamento(
                compra,
                valor_recibo,
                valor_fatura
            )

            if not valores_iguais and not compra_parcelada:
                continue

            similaridade = fuzz.token_set_ratio(
                empresa_recibo,
                empresa_fatura
            )

            if similaridade < 55:
                continue

            candidatos.append({
                "indice": indice,
                "compra": compra,
                "similaridade": similaridade,
                "parcelada": compra_parcelada,
            })

        if not candidatos:
            resultados.append({
                "empresa": recibo.get("empresa"),
                "recibo": valor_recibo,
                "fatura": None,
                "status": "NÃO ENCONTRADO"
            })

            continue

        melhor_candidato = max(
            candidatos,
            key=lambda candidato: candidato["similaridade"]
        )

        indice = melhor_candidato["indice"]
        compra = melhor_candidato["compra"]
        parcelada = melhor_candidato["parcelada"]

        indices_utilizados.add(indice)

        diferenca = diferenca_dias(
            recibo.get("data"),
            compra.get("data")
        )

        if parcelada:
            status = "CONFIRMADO - PARCELADO"

        elif diferenca is not None and diferenca > 2:
            status = "DATA DIFERENTE"

        else:
            status = "CONFIRMADO"

        resultados.append({
            "empresa": recibo.get("empresa"),
            "empresa_fatura": compra.get("empresa"),
            "recibo": valor_recibo,
            "fatura": float(compra.get("valor", 0)),
            "data_recibo": recibo.get("data"),
            "data_fatura": compra.get("data"),
            "status": status
        })
    # Adiciona compras da fatura que não receberam comprovante
    for indice, compra in enumerate(fatura):
        if indice in indices_utilizados:
            continue

        resultados.append({
            "empresa": compra.get("empresa"),
            "empresa_fatura": compra.get("empresa"),
            "recibo": None,
            "fatura": float(compra.get("valor", 0)),
            "data_recibo": None,
            "data_fatura": compra.get("data"),
            "status": "SEM COMPROVANTE"
        })

    
    return resultados