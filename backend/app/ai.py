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

        print("\nEnviando para a IA...")
        print(f"Caracteres enviados: {len(texto)}")

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

    except APITimeoutError:
        raise RuntimeError("Timeout da IA.")

    except APIStatusError as erro:

        print("Status:", erro.status_code)

        raise

    except Exception:
        raise