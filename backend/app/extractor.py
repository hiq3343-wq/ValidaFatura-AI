from pathlib import Path
import os
import tempfile

import easyocr
import pdfplumber
import pypdfium2 as pdfium


reader = easyocr.Reader(["pt"])


def extrair_texto_pdf_normal(caminho: str) -> str:
    """Extrai texto de PDFs que possuem texto selecionável."""

    paginas = []

    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            texto_pagina = pagina.extract_text() or ""

            if texto_pagina.strip():
                paginas.append(texto_pagina)

    return "\n".join(paginas)


def extrair_texto_pdf_com_ocr(caminho: str) -> str:
    """Converte cada página do PDF em imagem e executa OCR."""

    documento = pdfium.PdfDocument(caminho)
    textos = []

    with tempfile.TemporaryDirectory() as pasta_temporaria:
        for numero_pagina in range(len(documento)):
            pagina = documento[numero_pagina]

            imagem = pagina.render(
                scale=2.5
            ).to_pil()

            caminho_imagem = os.path.join(
                pasta_temporaria,
                f"pagina_{numero_pagina + 1}.png"
            )

            imagem.save(caminho_imagem)

            resultado = reader.readtext(
                caminho_imagem,
                detail=0,
                paragraph=True
            )

            textos.append("\n".join(resultado))

    return "\n".join(textos)


def extrair_texto_pdf(caminho: str) -> str:
    """
    Primeiro tenta extrair o texto normalmente.
    Se não encontrar conteúdo suficiente, utiliza OCR.
    """

    texto = extrair_texto_pdf_normal(caminho)

    if len(texto.strip()) >= 30:
        return texto

    print("PDF sem texto selecionável. Iniciando OCR das páginas...")

    return extrair_texto_pdf_com_ocr(caminho)


def extrair_texto_imagem(caminho: str) -> str:
    """Extrai texto de uma imagem usando OCR."""

    resultado = reader.readtext(
        caminho,
        detail=0,
        paragraph=True
    )

    return "\n".join(resultado)


def extrair_texto(caminho: str) -> str:
    """Identifica o tipo do arquivo e escolhe o extrator adequado."""

    extensao = Path(caminho).suffix.lower()

    if extensao == ".pdf":
        return extrair_texto_pdf(caminho)

    if extensao in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
        return extrair_texto_imagem(caminho)

    raise ValueError(
        f"Formato de arquivo não suportado: {extensao}"
    )