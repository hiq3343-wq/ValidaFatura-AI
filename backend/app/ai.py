import json

from openai import OpenAI

from app.config import GROQ_API_KEY


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def interpretar_documento(texto: str) -> list[dict]:
    prompt = f"""
Você é especialista em analisar faturas de cartão, recibos e comprovantes.

Extraia todas as transações reais encontradas no texto.

Para cada transação, retorne:
- empresa
- valor
- data
- parcela_atual
- total_parcelas

Regras:
- O valor deve ser um número decimal, sem o símbolo R$.
- A data deve ser mantida como aparece no documento.
- Não considere total da fatura, limite, vencimento ou pagamento da fatura
  como se fossem compras.
- Quando aparecer algo como "Parcela 2/3", retorne:
  "parcela_atual": 2
  "total_parcelas": 3
- Não remova a informação de parcelamento.
- Quando não for uma compra parcelada, use null em
  "parcela_atual" e "total_parcelas".
- Se não encontrar transações, retorne uma lista vazia.

Responda exatamente neste formato JSON:

{{
  "transacoes": [
    {{
      "empresa": "UBER",
      "valor": 32.50,
      "data": "08/07/2026",
      "parcela_atual": null,
      "total_parcelas": null
    }}
  ]
}}

Texto do documento:

{texto}
"""

    try:
        resposta = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um extrator de dados. "
                        "Responda sempre e somente com um objeto JSON válido."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_object"
            },
            temperature=0
        )

        texto_resposta = resposta.choices[0].message.content

        if not texto_resposta:
            raise ValueError("A IA retornou uma resposta vazia.")

        print("\n========== RESPOSTA DA IA ==========")
        print(texto_resposta)
        print("====================================\n")

        dados = json.loads(texto_resposta)
        transacoes = dados.get("transacoes")

        if not isinstance(transacoes, list):
            raise ValueError(
                "A resposta não contém uma lista chamada 'transacoes'."
            )

        return transacoes

    except json.JSONDecodeError as erro:
        raise ValueError(
            f"A IA retornou um JSON inválido: {erro}"
        ) from erro

    except Exception as erro:
        raise RuntimeError(str(erro)) from erro