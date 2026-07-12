from pathlib import Path
import tempfile

import pdfplumber
import pypdfium2 as pdfium
import pytesseract
from PIL import Image


CONFIGURACAO_OCR = "--oem 1 --psm 6"


def executar_ocr(imagem: Image.Image) -> str:
    """
    Executa OCR em português e inglês.

    A combinação por+eng ajuda quando o documento contém
    nomes de empresas, datas e termos em idiomas diferentes.
    """
    imagem = imagem.convert("RGB")

    return pytesseract.image_to_string(
        imagem,
        lang="por+eng",
        config=CONFIGURACAO_OCR
    ).strip()


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

    with tempfile.TemporaryDirectory():
        for numero_pagina in range(len(documento)):
            pagina = documento[numero_pagina]

            imagem = pagina.render(
                scale=2.5
            ).to_pil()

            texto_pagina = executar_ocr(imagem)

            if texto_pagina:
                textos.append(texto_pagina)

    return "\n".join(textos)


def extrair_texto_pdf(caminho: str) -> str:
    """
    Primeiro tenta extrair texto selecionável.
    Caso não encontre conteúdo suficiente, utiliza OCR.
    """

    texto = extrair_texto_pdf_normal(caminho)

    if len(texto.strip()) >= 30:
        return texto

    print(
        "PDF sem texto selecionável. "
        "Iniciando OCR das páginas..."
    )

    return extrair_texto_pdf_com_ocr(caminho)


def extrair_texto_imagem(caminho: str) -> str:
    """Extrai texto de uma imagem usando OCR."""

    with Image.open(caminho) as imagem:
        return executar_ocr(imagem)


def extrair_texto(caminho: str) -> str:
    """Identifica o formato e escolhe o extrator adequado."""

    extensao = Path(caminho).suffix.lower()

    if extensao == ".pdf":
        return extrair_texto_pdf(caminho)

    if extensao in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp"
    }:
        return extrair_texto_imagem(caminho)

    raise ValueError(
        f"Formato de arquivo não suportado: {extensao}"
    )