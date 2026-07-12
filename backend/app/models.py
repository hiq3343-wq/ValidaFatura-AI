from pydantic import BaseModel


class Transacao(BaseModel):
    empresa: str
    valor: float
    data: str | None = None


class ResultadoComparacao(BaseModel):
    empresa: str
    valor: float
    encontrado: bool
    observacao: str