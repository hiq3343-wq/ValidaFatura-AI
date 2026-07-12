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

        except Exception as erro:
            print(
                "\n========== ERRO INESPERADO ==========",
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
                "=====================================\n",
                flush=True,
            )

            raise RuntimeError(
                "Erro inesperado ao preparar a conexão "
                f"com a Groq: {erro}"
            ) from erro

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

Retorne somente um objeto JSON válido neste formato:

{{
  "transacoes": [
    {{
      "empresa": "UBER",
      "valor": 32.50,
      "data": "08 JUL",
      "parcela_atual": null,
      "total_parcelas": null
    }}
  ]
}}

Regras:
- valor deve ser numérico;
- preserve a data como aparece;
- informe parcela_atual e total_parcelas quando houver;
- use null quando não houver parcelamento;
- se não houver compras, retorne "transacoes" como lista vazia.

Texto da fatura:

{texto}
"""

    payload = {
        "model": MODELO_IA,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um extrator de dados. "
                    "Responda somente com JSON válido."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "response_format": {
            "type": "json_object",
        },
        "temperature": 0,
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