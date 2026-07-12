import os
import shutil
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.ai import interpretar_documento
from app.comparator import comparar_transacoes
from app.services import (
    processar_documento,
    processar_documentos_em_lote,
)


router = APIRouter()


class TextoRequest(BaseModel):
    texto: str


UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.get("/")
def home():
    return {
        "mensagem": "API funcionando!",
        "status": "online",
    }


@router.get("/health")
def health():
    return {
        "status": "online",
        "servico": "Validador de Faturas",
    }


@router.post("/validar")
async def validar(
    fatura: Annotated[UploadFile, File(...)],
    recibos: Annotated[list[UploadFile], File(...)],
):
    try:
        nome_fatura = os.path.basename(
            fatura.filename or "fatura.pdf"
        )

        caminho_fatura = os.path.join(
            UPLOAD_FOLDER,
            nome_fatura,
        )

        with open(caminho_fatura, "wb") as buffer:
            shutil.copyfileobj(
                fatura.file,
                buffer,
            )

        transacoes_fatura = processar_documento(
            caminho_fatura
        )

        documentos_recibos = []

        for indice, recibo in enumerate(recibos):
            nome_recibo = os.path.basename(
                recibo.filename
                or f"comprovante_{indice + 1}"
            )

            caminho_recibo = os.path.join(
                UPLOAD_FOLDER,
                nome_recibo,
            )

            with open(caminho_recibo, "wb") as buffer:
                shutil.copyfileobj(
                    recibo.file,
                    buffer,
                )

            documentos_recibos.append(
                (
                    nome_recibo,
                    caminho_recibo,
                )
            )

        resultado_recibos = processar_documentos_em_lote(
            documentos_recibos
        )

        comparacao = comparar_transacoes(
            transacoes_fatura,
            resultado_recibos,
        )

        confirmados = sum(
            item.get("resultado") == "confirmado"
            for item in comparacao
        )

        divergencias = sum(
            item.get("resultado")
            in {
                "divergencia_data",
                "nao_encontrado",
            }
            for item in comparacao
        )

        sem_comprovante = sum(
            item.get("resultado") == "sem_comprovante"
            for item in comparacao
        )

        pendencias = (
            divergencias
            + sem_comprovante
        )

        return {
            "resumo": {
                "compras_fatura": len(
                    transacoes_fatura
                ),
                "comprovantes": len(
                    resultado_recibos
                ),
                "confirmados": confirmados,
                "divergencias": divergencias,
                "sem_comprovante": sem_comprovante,
                "pendencias": pendencias,
            },
            "transacoes_fatura": transacoes_fatura,
            "transacoes_recibos": resultado_recibos,
            "comparacao": comparacao,
        }

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=str(erro),
        ) from erro


@router.post("/teste-ia")
def teste_ia(request: TextoRequest):
    try:
        return interpretar_documento(
            request.texto
        )

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=str(erro),
        ) from erro