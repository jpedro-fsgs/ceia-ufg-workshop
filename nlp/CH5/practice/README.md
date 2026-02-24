# CH5 Prática — Pipeline RAG ponta a ponta

Esta prática implementa um fluxo RAG completo com etapas separadas:

1. Leitura de documentos em uma pasta.
2. Quebra dos documentos em chunks.
3. Geração de embeddings com `BAAI/bge-m3`.
4. Indexação no banco vetorial Qdrant.
5. API de chat com RAG usando `gpt-4.1-mini`.

## Arquitetura do fluxo

```text
data/documents/*.md|*.txt|*.pdf
    -> 01_chunk_documents.py
    -> data/artifacts/chunks.jsonl
    -> 02_generate_embeddings.py
    -> data/artifacts/embeddings.jsonl
    -> 03_index_qdrant.py
    -> Qdrant collection
    -> 04_api.py (/chat)
```

## Estrutura de pastas

```text
.
├── 01_chunk_documents.py
├── 02_generate_embeddings.py
├── 03_index_qdrant.py
├── 04_api.py
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── data/
│   ├── documents/
│   └── artifacts/
└── src/
    ├── document_pipeline.py
    ├── rag_pipeline.py
    └── settings.py
```

## Pré-requisitos

- Python 3.10+
- Docker + Docker Compose
- Chave da OpenAI para usar o `gpt-4.1-mini`

## Passo a passo de execução

### 1) Instalar dependências

```bash
cd nlp/CH5/practice
python3 -m venv .venv
source venv/bin/activate # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 2) Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` e preencha ao menos:

```env
OPENAI_API_KEY=...
```

### 3) Subir apenas o banco vetorial com Docker (Qdrant)

```bash
docker compose up -d
```

Qdrant ficará disponível em:

- API HTTP: `http://localhost:6333`
- gRPC: `localhost:6334`

### 4) Adicionar documentos na pasta de entrada

Coloque arquivos `.md`, `.txt` ou `.pdf` em:

```text
data/documents/
```

### 5) Rodar pipeline de ingestão

```bash
python3 01_chunk_documents.py
python3 02_generate_embeddings.py
python3 03_index_qdrant.py
```

### 6) Subir API de chat com RAG

```bash
uvicorn 04_api:app --host 0.0.0.0 --port 8000
```

### 7) Testar a API

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"pergunta":"Quais componentes usamos no CH5?","top_k":3}'
```

Resposta esperada (resumo):

- `resposta`: texto gerado pelo LLM com base no contexto recuperado.
- `fontes`: lista de chunks usados na resposta.

## Observações didáticas

- O chunking é por caracteres com overlap configurável (`CHUNK_SIZE` e `CHUNK_OVERLAP` no `.env`).
- PDFs são lidos com `pypdf` (extração de texto página a página).
- A coleção do Qdrant é recriada no script `03_index_qdrant.py` para simplificar experimentos em sala.
- O primeiro run do `bge-m3` pode demorar por download do modelo.

## Limpar ambiente

```bash
docker compose down
```
