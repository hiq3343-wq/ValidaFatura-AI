import json
import time

import requests

from app.config import GROQ_API_KEY


MODELO_IA = "openai/gpt-oss-20b"

URL_GROQ = (
    "https://api.groq.com/openai/v1/chat/completions"
)

TENTATIVAS_MAXIMAS = 3
TIMEOUT_CONEXAO = 15
TIMEOUT_RESPOSTA = 90


if not GROQ_API_KEY:
    raise RuntimeError(
        "A variável GROQ_API_KEY não foi configurada."
    )


print("\n======================================")
print(f"Modelo: {MODELO_IA}")
print("Integração: API REST da Groq")
print("======================================\n")


def realizar_requisicao(
    payload: dict
) -> requests.Response:
    ultimo_erro: Exception | None = None

    for tentativa in range(
        1,
        TENTATIVAS_MAXIMAS + 1
    ):
        try:
            print(
                f">>> Tentativa {tentativa}/"
                f"{TENTATIVAS_MAXIMAS} "
                "de conexão com a Groq",
                flush=True,
            )

            resposta = requests.post(
                URL_GROQ,
                headers={
                    "Authorization": (
                        f"Bearer {GROQ_API_KEY}"
                    ),
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=(
                    TIMEOUT_CONEXAO,
                    TIMEOUT_RESPOSTA,
                ),
            )

            print(
                f">>> Groq respondeu com HTTP "
                f"{resposta.status_code}",
                flush=True,
            )

            return resposta

        except requests.RequestException as erro:
            ultimo_erro = erro

            print(
                "\n========== ERRO DE REDE ==========",
                flush=True,
            )
            print(
                f"Tipo: {type(erro).__name__}",
                flush=True,
            )
            print(
                f"Detalhes: {erro!r}",
                flush=True,
            )
            print(
                "==================================\n",
                flush=True,
            )

            if tentativa < TENTATIVAS_MAXIMAS:
                espera = 2 * tentativa

                print(
                    f">>> Nova tentativa em "
                    f"{espera} segundos...",
                    flush=True,
                )

                time.sleep(espera)

    raise RuntimeError(
        "Não foi possível conectar à Groq após "
        f"{TENTATIVAS_MAXIMAS} tentativas. "
        f"Último erro: {type(ultimo_erro).__name__}: "
        f"{ultimo_erro}"
    )


def interpretar_documento(
    texto: str
) -> list[dict]:
    prompt = f"""
Analise o texto de uma fatura de cartão e extraia todas
as compras reais.

Ignore:
- total da fatura;
- limite;
- vencimento;
- pagamento da fatura;
- pagamento mínimo;
- informações que não sejam compras.

Para cada compra, identifique:
- empresa;
- valor;
- data;
- parcela atual;
- total de parcelas.

Texto da fatura:

{texto}
"""

    payload = {
        "model": MODELO_IA,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um extrator de dados de faturas. "
                    "Extraia somente compras reais."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "transacoes_fatura",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "transacoes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "empresa": {
                                        "type": "string",
                                    },
                                    "valor": {
                                        "type": "number",
                                    },
                                    "data": {
                                        "anyOf": [
                                            {
                                                "type": "string",
                                            },
                                            {
                                                "type": "null",
                                            },
                                        ],
                                    },
                                    "parcela_atual": {
                                        "anyOf": [
                                            {
                                                "type": "integer",
                                            },
                                            {
                                                "type": "null",
                                            },
                                        ],
                                    },
                                    "total_parcelas": {
                                        "anyOf": [
                                            {
                                                "type": "integer",
                                            },
                                            {
                                                "type": "null",
                                            },
                                        ],
                                    },
                                },
                                "required": [
                                    "empresa",
                                    "valor",
                                    "data",
                                    "parcela_atual",
                                    "total_parcelas",
                                ],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": [
                        "transacoes",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "temperature": 0,
        "reasoning_effort": "low",
        "max_completion_tokens": 4096,
    }

    print("\n==============================")
    print("Enviando fatura para a IA...")
    print(f"Caracteres enviados: {len(texto)}")
    print("==============================")

    resposta = realizar_requisicao(payload)

    if resposta.status_code == 429:
        try:
            detalhe = resposta.json()["error"]["message"]
        except (ValueError, KeyError, TypeError):
            detalhe = resposta.text

        raise RuntimeError(
            "Limite da Groq atingido. "
            f"Detalhes: {detalhe}"
        )

    if not resposta.ok:
        print(
            "\n========== RESPOSTA DE ERRO DA GROQ ==========",
            flush=True,
        )
        print(
            f"Status: {resposta.status_code}",
            flush=True,
        )
        print(
            f"Body: {resposta.text}",
            flush=True,
        )
        print(
            "==============================================\n",
            flush=True,
        )

        raise RuntimeError(
            f"Erro da Groq ({resposta.status_code}): "
            f"{resposta.text}"
        )

    try:
        dados_resposta = resposta.json()

        texto_resposta = (
            dados_resposta["choices"][0]
            ["message"]["content"]
        )

        if not texto_resposta:
            raise ValueError(
                "A IA retornou uma resposta vazia."
            )

        dados = json.loads(texto_resposta)
        transacoes = dados.get("transacoes")

        if not isinstance(transacoes, list):
            raise ValueError(
                "A resposta não contém uma lista "
                "chamada 'transacoes'."
            )

        print(
            f">>> IA retornou {len(transacoes)} "
            "transação(ões)."
        )

        return transacoes

    except (
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ) as erro:
        print(
            "Resposta bruta recebida da Groq:",
            resposta.text,
        )

        raise RuntimeError(
            f"Resposta inesperada da IA: {erro}"
        ) from erro