import time

from app.ai import interpretar_documento
from app.extractor import extrair_texto
from app.receipt_parser import interpretar_comprovante


def processar_documento(
    caminho_arquivo: str
) -> list[dict]:
    inicio = time.perf_counter()

    print(">>> Extraindo texto da fatura...")

    texto = extrair_texto(caminho_arquivo)

    print(
        f">>> OCR da fatura concluído em "
        f"{time.perf_counter() - inicio:.2f}s"
    )

    if not texto.strip():
        raise ValueError(
            "Não foi possível extrair texto da fatura: "
            f"{caminho_arquivo}"
        )

    print(
        f">>> Caracteres extraídos: {len(texto)}"
    )

    texto = texto[:15000]

    print(
        f">>> Caracteres enviados para IA: {len(texto)}"
    )

    inicio_ia = time.perf_counter()

    transacoes = interpretar_documento(texto)

    print(
        f">>> IA respondeu em "
        f"{time.perf_counter() - inicio_ia:.2f}s"
    )

    if isinstance(transacoes, dict) and "erro" in transacoes:
        raise RuntimeError(
            "Erro ao interpretar a fatura com IA: "
            f"{transacoes['erro']}"
        )

    if not isinstance(transacoes, list):
        raise ValueError(
            "A IA retornou um formato inesperado."
        )

    return transacoes


def processar_documentos_em_lote(
    documentos: list[tuple[str, str]]
) -> list[dict]:
    transacoes = []

    for indice, (nome_arquivo, caminho_arquivo) in enumerate(
        documentos,
        start=1
    ):
        inicio = time.perf_counter()

        print(
            f">>> [{indice}/{len(documentos)}] "
            f"Processando {nome_arquivo}"
        )

        texto = extrair_texto(caminho_arquivo)

        print(
            f">>> OCR concluído em "
            f"{time.perf_counter() - inicio:.2f}s"
        )

        if not texto.strip():
            continue

        texto = texto[:4000]

        transacoes.append(
            interpretar_comprovante(
                texto=texto,
                nome_arquivo=nome_arquivo
            )
        )

    if not transacoes:
        raise ValueError(
            "Nenhum comprovante pôde ser processado."
        )

    return transacoes