import os
import shutil
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.ai import interpretar_documento
from app.comparator import comparar_transacoes
from app.services import processar_documento


router = APIRouter()


class TextoRequest(BaseModel):
    texto: str


UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.get("/")
def home():
    return {
        "mensagem": "API funcionando!",
        "status": "online"
    }


@router.get("/health")
def health():
    return {
        "status": "online",
        "servico": "Validador de Faturas"
    }


@router.post("/validar")
async def validar(
    fatura: Annotated[UploadFile, File(...)],
    recibos: Annotated[list[UploadFile], File(...)]
):
    try:
        caminho_fatura = os.path.join(
            UPLOAD_FOLDER,
            fatura.filename
        )

        with open(caminho_fatura, "wb") as buffer:
            shutil.copyfileobj(
                fatura.file,
                buffer
            )

        transacoes_fatura = processar_documento(
            caminho_fatura
        )

        resultado_recibos = []

        for recibo in recibos:
            caminho = os.path.join(
                UPLOAD_FOLDER,
                recibo.filename
            )

            with open(caminho, "wb") as buffer:
                shutil.copyfileobj(
                    recibo.file,
                    buffer
                )

            transacoes = processar_documento(
                caminho
            )

            resultado_recibos.extend(
                transacoes
            )

        comparacao = comparar_transacoes(
            transacoes_fatura,
            resultado_recibos
        )

        return {
            "transacoes_fatura": transacoes_fatura,
            "transacoes_recibos": resultado_recibos,
            "comparacao": comparacao
        }

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=str(erro)
        )


@router.post("/teste-ia")
def teste_ia(request: TextoRequest):
    try:
        return interpretar_documento(request.texto)

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=str(erro)
        )