import json

from openai import APIStatusError, APITimeoutError, OpenAI

from app.config import GROQ_API_KEY

print(
    "\n======================================"
)
print("Modelo: openai/gpt-oss-20b")
print(
    f"API carregada: {GROQ_API_KEY[:10]}...{GROQ_API_KEY[-6:]}"
)
print(
    "======================================\n"
)

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def interpretar_documento(texto: str) -> list[dict]:
    prompt = f"""
Você é especialista em analisar faturas de cartão.

Extraia todas as compras.

Retorne SOMENTE um JSON válido.

Formato:

{{
  "transacoes": [
    {{
      "empresa": "",
      "valor": 0,
      "data": "",
      "parcela_atual": null,
      "total_parcelas": null
    }}
  ]
}}

Texto:

{texto}
"""

    try:

        print("\n==============================")
        print("Enviando para a IA...")
        print(f"Caracteres enviados: {len(texto)}")
        print("==============================")

        resposta = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "Responda apenas JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_object"
            },
            temperature=0,
            timeout=60,
        )

        print("Resposta recebida!")

        texto_resposta = resposta.choices[0].message.content

        if not texto_resposta:
            raise ValueError("Resposta vazia.")

        dados = json.loads(texto_resposta)

        return dados["transacoes"]

    except APITimeoutError as erro:

        print("\n========== TIMEOUT ==========")
        print(repr(erro))
        print("=============================\n")

        raise RuntimeError(
            "Timeout ao consultar a IA."
        ) from erro

    except APIStatusError as erro:

        print("\n========== API ERROR ==========")
        print("Status:", erro.status_code)

        try:
            print("Body:")
            print(erro.response.text)
        except Exception:
            pass

        print("===============================\n")

        raise RuntimeError(
            f"Erro da Groq ({erro.status_code})"
        ) from erro

    except json.JSONDecodeError as erro:

        print("\n========== JSON ERROR ==========")
        print(repr(erro))
        print("===============================\n")

        raise RuntimeError(
            "JSON inválido retornado pela IA."
        ) from erro

    except Exception as erro:

        print("\n========== ERRO GERAL ==========")
        print(type(erro).__name__)
        print(repr(erro))
        print("================================\n")

        raise RuntimeError(str(erro)) from erro