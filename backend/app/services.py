from app.ai import interpretar_documento
from app.extractor import extrair_texto


def processar_documento(caminho_arquivo: str) -> list[dict]:
    texto = extrair_texto(caminho_arquivo)

    if not texto.strip():
        raise ValueError(
            f"Não foi possível extrair texto do arquivo: {caminho_arquivo}"
        )

    transacoes = interpretar_documento(texto)

    if isinstance(transacoes, dict) and "erro" in transacoes:
        raise RuntimeError(
            f"Erro ao interpretar o documento com IA: {transacoes['erro']}"
        )

    if not isinstance(transacoes, list):
        raise ValueError(
            "A IA retornou um formato inesperado. Era esperada uma lista."
        )

    return transacoes