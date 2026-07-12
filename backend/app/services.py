from app.ai import interpretar_documento
from app.extractor import extrair_texto


def processar_documento(caminho_arquivo: str) -> list[dict]:
    texto = extrair_texto(caminho_arquivo)

    if not texto.strip():
        raise ValueError(
            f"Não foi possível extrair texto do arquivo: {caminho_arquivo}"
        )

    # Evita enviar textos enormes para a IA.
    texto = texto[:15000]

    transacoes = interpretar_documento(texto)

    if isinstance(transacoes, dict) and "erro" in transacoes:
        raise RuntimeError(
            f"Erro ao interpretar o documento com IA: "
            f"{transacoes['erro']}"
        )

    if not isinstance(transacoes, list):
        raise ValueError(
            "A IA retornou um formato inesperado. "
            "Era esperada uma lista."
        )

    return transacoes


def processar_documentos_em_lote(
    documentos: list[tuple[str, str]]
) -> list[dict]:
    textos = []

    for nome_arquivo, caminho_arquivo in documentos:
        texto = extrair_texto(caminho_arquivo)

        if not texto.strip():
            continue

        # Comprovantes normalmente são pequenos.
        texto = texto[:4000]

        textos.append(
            f"""
===== ARQUIVO: {nome_arquivo} =====
{texto}
===== FIM DO ARQUIVO =====
"""
        )

    if not textos:
        raise ValueError(
            "Não foi possível extrair texto dos comprovantes."
        )

    texto_completo = "\n".join(textos)

    transacoes = interpretar_documento(texto_completo)

    if not isinstance(transacoes, list):
        raise ValueError(
            "A IA retornou um formato inesperado ao analisar "
            "os comprovantes."
        )

    return transacoes