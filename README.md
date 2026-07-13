# ValidaFatura AI

Sistema web para comparar os lançamentos de uma fatura de cartão
com recibos e comprovantes enviados pelo usuário.

🔗 Demonstração: https://valida-fatura-ai.vercel.app

## Objetivo

Automatizar a conferência de comprovantes contra uma fatura,
identificando compras confirmadas, parceladas, divergentes
ou sem comprovante.

## Como funciona

1. A fatura em PDF é processada.
2. O texto é enviado à IA para extrair as compras.
3. Os comprovantes passam por OCR.
4. Um parser extrai empresa, valor, data e parcelas.
5. O comparador cruza os dados.
6. O frontend apresenta os resultados.

## Decisões técnicas

- IA na fatura, pois o layout varia entre bancos.
- OCR e parser nos comprovantes para reduzir tokens e custo.
- RapidFuzz para comparar nomes com diferenças de formatação.
- Docker para instalar e executar o Tesseract no Render.

## Status retornados

- Confirmado
- Confirmado parcelado
- Data divergente
- Não encontrado
- Sem comprovante

## Tecnologias

...

## Execução local

...

## Limitações

- OCR depende da qualidade da imagem.
- O desempenho varia conforme os recursos do servidor.
- O parser pode precisar de novos rótulos para layouts muito diferentes.

## Melhorias futuras

- testes automatizados;
- limpeza automática de uploads;
- processamento assíncrono;
- suporte a armazenamento externo.
