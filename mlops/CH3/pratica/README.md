# CH3 — Prática: Document Q&A API

API de perguntas e respostas sobre documentos construída com **FastAPI**, **LangChain** e **ChromaDB**. O usuário faz upload de PDFs ou arquivos de texto, e a API indexa o conteúdo num banco vetorial. A partir daí, perguntas em linguagem natural são respondidas via pipeline RAG (Retrieval-Augmented Generation) usando **GPT-4o-mini**, com fallback automático para **Google Gemini** caso a OpenAI não esteja disponível. Todo o fluxo é observado em tempo real pelo **Arize Phoenix**.

```
┌─────────────────────────────────────────────────────┐
│  Você faz upload de um PDF                          │
│       ↓                                             │
│  LangChain divide em chunks → OpenAI embeddings     │
│       ↓                                             │
│  ChromaDB armazena os vetores                       │
│       ↓                                             │
│  Você faz uma pergunta                              │
│       ↓                                             │
│  API recupera os 4 chunks mais relevantes           │
│       ↓                                             │
│  GPT-4o-mini (ou Gemini) gera a resposta            │
│       ↓                                             │
│  Phoenix registra tudo: inputs, outputs, latência   │
└─────────────────────────────────────────────────────┘
```

---

## Pré-requisitos

| Ferramenta | Versão mínima |
|------------|---------------|
| Docker | 24+ |
| Docker Compose | v2 |
| OpenAI API key | — |
| Google AI API key _(opcional)_ | — |

---

## Como Rodar

Existem dois modos: **Docker Compose** (recomendado para este capítulo) e **Monolito** (será usado no CH4).

### Docker Compose — recomendado para o CH3

Cada serviço roda em seu próprio container. É o modo que melhor ilustra os conceitos de MLOps deste capítulo: separação de responsabilidades, health checks, volumes e rede Docker.

```bash
# 1. Crie o arquivo .env na raiz do projeto
echo "OPENAI_API_KEY=sk-..."  > .env
echo "GOOGLE_API_KEY=AIza..." >> .env   # opcional — ativa o fallback Gemini

# 2. Suba todos os serviços
docker compose up --build -d

# 3. Acompanhe os logs
docker compose logs -f api
```

Aguarde os health checks passarem (~15 s):

```bash
docker compose ps
```

| Serviço | URL |
|---------|-----|
| API (Swagger) | http://localhost:8000/docs |
| Streamlit UI | http://localhost:8501 |
| Phoenix (traces) | http://localhost:6006 |
| ChromaDB | http://localhost:8001 |
| Documentação | http://localhost:8080 |

---

### Monolito — usado no CH4

Todos os serviços rodam dentro de um único container gerenciado pelo `supervisord`, com ChromaDB embarcado. Este modo é o ponto de partida da prática do próximo capítulo.

```bash
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."   # opcional

bash monolit/run.sh
```

---

## Uso rápido via cURL

```bash
# 1. Obter token JWT
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=changeme" | jq -r .access_token)

# 2. Fazer upload de um documento
curl -s -X POST http://localhost:8000/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@meu_documento.pdf"

# 3. Fazer uma pergunta
curl -s -X POST http://localhost:8000/rag/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual o assunto principal do documento?"}' | jq
```

A resposta inclui o campo `provider` indicando se foi `"openai"` ou `"gemini"` que respondeu.

---

## Credenciais padrão

| Campo | Valor |
|-------|-------|
| Usuário | `admin` |
| Senha | `changeme` |

> Altere via variável de ambiente `APP_USER=usuario:senha` antes de subir o container.

---

## Variáveis de Ambiente principais

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | Sim | Chave da OpenAI |
| `GOOGLE_API_KEY` | Não | Chave Google AI — ativa o fallback Gemini |
| `GOOGLE_MODEL` | Não | Modelo Gemini (padrão: `gemini-2.0-flash`) |
| `OPENAI_MODEL` | Não | Modelo OpenAI (padrão: `gpt-4o-mini`) |
| `APP_USER` | Não | Credenciais `usuario:senha` (padrão: `admin:changeme`) |
| `SECRET_KEY` | Não | Chave JWT — gere com `openssl rand -hex 32` |

---

---

## 🎯 Desafios do Workshop

O projeto já está funcional. Os desafios abaixo propõem extensões reais — do tipo que aparece no dia a dia de quem mantém APIs de ML em produção.

> **Dica:** Leia o código em `main.py` antes de começar. Ele tem ~380 linhas e está organizado em seções comentadas.

---

### Nível 1 — Explorar (faça isso primeiro)

**Objetivo:** Entender o sistema antes de mexer nele.

1. Suba o projeto e acesse o Swagger em `http://localhost:8000/docs`
2. Autentique-se com `admin / changeme` e obtenha um token
3. Faça upload de qualquer PDF que você tenha (ou baixe um)
4. Faça uma pergunta sobre o documento e observe a resposta
5. Abra o Phoenix em `http://localhost:6006` e encontre o trace da sua pergunta
6. No trace, verifique: qual foi o prompt enviado ao LLM? Quantos tokens foram usados?

---

### Nível 2 — Modificar

Escolha **um** dos desafios abaixo:

#### 2-A: Adicionar o campo `chunk_count` na resposta do upload

Atualmente o endpoint `POST /documents` retorna apenas os nomes dos arquivos:
```json
{ "documents": ["relatorio.pdf"] }
```

Modifique para retornar também quantos chunks foram indexados:
```json
{ "documents": ["relatorio.pdf"], "chunk_count": 42 }
```

**Dica:** A função `_ingest_file` já retorna `len(chunks)`. Você precisa capturar esse valor no endpoint e expô-lo no modelo Pydantic.

---

#### 2-B: Tornar o número de chunks recuperados configurável

Atualmente o retriever sempre busca `k=4` chunks. Permita que o usuário passe esse valor na requisição:

```json
POST /rag/query
{ "question": "O que é MLOps?", "top_k": 8 }
```

**Dica:** Adicione o campo `top_k: int = 4` ao modelo `QueryRequest` e passe-o para `search_kwargs={"k": top_k}` na função `_run_rag_query`.

---

#### 2-C: Endpoint para apagar um documento

Implemente `DELETE /documents/{filename}` que:
1. Remove o arquivo físico de `UPLOAD_DIR`
2. Remove os chunks correspondentes do ChromaDB

```bash
curl -X DELETE http://localhost:8000/documents/relatorio.pdf \
  -H "Authorization: Bearer $TOKEN"
```

**Dica:** No ChromaDB você pode usar `collection.delete(where={"source": str(path)})` para remover chunks por metadado.

---

### Nível 3 — Construir

Desafios mais abertos, sem solução única:

#### 3-A: Testar o fallback Gemini

Configure `GOOGLE_API_KEY` com uma chave válida e force o fallback simulando uma falha na OpenAI. Uma forma simples: passe uma `OPENAI_API_KEY` inválida e uma `GOOGLE_API_KEY` válida.

Observe no Phoenix se o trace mostra a tentativa com OpenAI e o retry com Gemini. O campo `provider` na resposta deve retornar `"gemini"`.

**Pergunta para reflexão:** Em produção, além de fallback de LLM, o que mais você protegeria com retry/fallback nesse pipeline?

---

#### 3-B: Health check inteligente

O endpoint `/health` atual retorna apenas `{"status": "ok"}` sem verificar nada. Melhore-o para que reporte o estado real dos serviços dependentes:

```json
{
  "status": "ok",
  "chromadb": "ok",
  "documents_indexed": 127,
  "openai_key_configured": true,
  "gemini_key_configured": false
}
```

---

#### 3-C: Suporte a múltiplas coleções

Hoje todos os documentos vão para a coleção `"documents"`. Adicione suporte a coleções nomeadas, permitindo que o usuário isole contextos diferentes:

```bash
# Upload para uma coleção específica
POST /documents?collection=juridico

# Query em uma coleção específica
POST /rag/query
{ "question": "...", "collection": "juridico" }
```

**Ponto de atenção:** A coleção usada no upload precisa ser a mesma usada na query (os embeddings precisam estar no mesmo espaço vetorial).

---

### Nível 4 — Pesquisa

Para quem terminar tudo e quiser algo para pensar:

> O pipeline atual usa `text-embedding-ada-002` da OpenAI para gerar os embeddings — tanto no upload quanto na query. Isso significa que se você mudar o modelo de embedding, precisará re-indexar todos os documentos.
>
> **Desafio:** Como você arquitetaria um sistema que permita migrar modelos de embedding sem downtime e sem perder os documentos já indexados? Esboce a solução (pode ser em texto, diagrama ou pseudo-código).

---

## Estrutura do Projeto

```
pratica/
├── main.py                  # FastAPI — toda a lógica da API
├── pyproject.toml           # Dependências (gerenciadas com uv)
├── docker-compose.yml       # Stack multi-container
├── Dockerfile               # Imagem da API
├── .env.example             # Exemplo de variáveis de ambiente
├── streamlit_app/
│   └── app.py               # Interface web (Streamlit)
├── vectordb/
│   └── Dockerfile           # Imagem do ChromaDB
├── docs/                    # Fonte da documentação (MkDocs)
├── mkdocs.yml               # Configuração do MkDocs
└── monolit/                 # Versão single-container
    ├── main.py              # Mesma API, ChromaDB embarcado
    ├── Dockerfile           # Tudo num container só (supervisord)
    ├── supervisord.conf     # Gerenciador de processos
    └── run.sh               # Script de build + run
```
