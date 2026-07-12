import json

import groq
from groq import Groq

from app.config import GROQ_API_KEY


MODELO_IA = "openai/gpt-oss-20b"


if not GROQ_API_KEY:
    raise RuntimeError(
        "A variável de ambiente GROQ_API_KEY não foi configurada."
    )


print(
    "\n======================================"
)
print(f"Modelo: {MODELO_IA}")
print("SDK: Groq oficial")
print(
    "======================================\n"
)


client = Groq(
    api_key=GROQ_API_KEY,
    timeout=60.0,
    max_retries=2,
)


def interpretar_documento(
    texto: str
) -> list[dict]:
    prompt = f"""
Você é especialista em analisar faturas de cartão.

Extraia todas as compras reais presentes no texto da fatura.

Para cada compra, retorne:
- empresa
- valor
- data
- parcela_atual
- total_parcelas

Regras:
- Ignore total da fatura, limite, vencimento, pagamento,
  pagamento mínimo e demais informações que não sejam compras.
- O valor deve ser numérico e sem o símbolo R$.
- Preserve a data como aparece no documento.
- Em compras parceladas, informe a parcela atual e o total.
- Em compras não parceladas, use null nos campos de parcela.
- Se não houver compras, retorne uma lista vazia.
- Retorne somente um objeto JSON válido.

Formato obrigatório:

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

Texto da fatura:

{texto}
"""

    try:
        print(
            "\n=============================="
        )
        print("Enviando fatura para a IA...")
        print(
            f"Caracteres enviados: {len(texto)}"
        )
        print(
            "=============================="
        )

        resposta = client.chat.completions.create(
            model=MODELO_IA,
            messages=[
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
            response_format={
                "type": "json_object",
            },
            temperature=0,
        )

        print("Resposta recebida da IA.")

        texto_resposta = (
            resposta.choices[0].message.content
        )

        if not texto_resposta:
            raise ValueError(
                "A IA retornou uma resposta vazia."
            )

        dados = json.loads(texto_resposta)
        transacoes = dados.get("transacoes")

        if not isinstance(transacoes, list):
            raise ValueError(
                "A resposta da IA não contém uma "
                "lista chamada 'transacoes'."
            )

        return transacoes

    except groq.RateLimitError as erro:
        print(
            "\n========== LIMITE DA IA =========="
        )
        print(repr(erro))
        print(
            "==================================\n"
        )

        raise RuntimeError(
            "O limite de uso da IA foi atingido. "
            "Aguarde o período indicado pela Groq "
            "e tente novamente."
        ) from erro

    except groq.APITimeoutError as erro:
        print(
            "\n========== TIMEOUT DA IA =========="
        )
        print(repr(erro))
        print(
            "===================================\n"
        )

        raise RuntimeError(
            "A IA demorou mais de 60 segundos para responder."
        ) from erro

    except groq.APIConnectionError as erro:
        print(
            "\n========== CONEXÃO COM A IA =========="
        )
        print(repr(erro))
        print(
            "======================================\n"
        )

        raise RuntimeError(
            "Não foi possível conectar à Groq. "
            "A conexão foi tentada novamente automaticamente, "
            "mas continuou indisponível."
        ) from erro

    except groq.APIStatusError as erro:
        print(
            "\n========== ERRO DA GROQ =========="
        )
        print(f"Status: {erro.status_code}")
        print(repr(erro))
        print(
            "===================================\n"
        )

        raise RuntimeError(
            f"A Groq retornou o erro HTTP "
            f"{erro.status_code}."
        ) from erro

    except json.JSONDecodeError as erro:
        print(
            "\n========== JSON INVÁLIDO =========="
        )
        print(repr(erro))
        print(
            "===================================\n"
        )

        raise RuntimeError(
            "A IA respondeu, mas retornou um JSON inválido."
        ) from erro

    except (KeyError, IndexError, TypeError, ValueError) as erro:
        print(
            "\n========== RESPOSTA INESPERADA =========="
        )
        print(repr(erro))
        print(
            "=========================================\n"
        )

        raise RuntimeError(
            f"Resposta inesperada da IA: {erro}"
        ) from erro

    except Exception as erro:
        print(
            "\n========== ERRO GERAL =========="
        )
        print(type(erro).__name__)
        print(repr(erro))
        print(
            "================================\n"
        )

        raise RuntimeError(
            f"Erro inesperado ao consultar a IA: {erro}"
        ) from erro