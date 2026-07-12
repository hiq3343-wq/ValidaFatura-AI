# 💳 ValidaFatura AI

Sistema inteligente para validação automática de faturas de cartão de crédito através de Inteligência Artificial e OCR.

## 🚀 Funcionalidades

- 📄 Leitura de faturas em PDF
- 📷 Leitura de comprovantes em JPG, JPEG, PNG e WebP
- 🤖 Extração inteligente utilizando IA (Groq)
- 🔍 OCR utilizando Tesseract
- 💳 Reconhecimento de compras parceladas
- 📊 Comparação automática entre fatura e comprovantes
- ✅ Identificação de compras confirmadas
- ⚠️ Identificação de compras sem comprovante
- 🌐 Interface Web moderna

---

## Tecnologias

### Backend

- FastAPI
- Python
- Groq API
- Tesseract OCR
- pdfplumber
- pypdfium2
- RapidFuzz

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

---

## Como executar

### Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## Variáveis de ambiente

Backend (.env)

```
GROQ_API_KEY=sua_api_key
```

Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Demonstração

O sistema realiza:

- Upload da fatura
- Upload dos comprovantes
- OCR dos documentos
- Extração inteligente via IA
- Comparação automática
- Exibição do resultado

---

## Autor

Henrique Batista
