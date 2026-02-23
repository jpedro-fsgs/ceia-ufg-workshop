# Architecture

## Overview

The **monolith** variant runs all services inside a single Docker container managed by **supervisord**. ChromaDB operates as an embedded `PersistentClient` — no separate network service is needed.

```mermaid
graph TD
    U(["👤 User / Browser"])

    subgraph Container["🐳 Docker Container"]
        direction TB
        SV["⚙️ supervisord\nprocess manager"]

        subgraph Services["Services"]
            ST["🖥️ Streamlit UI\n:8501"]
            API["⚡ FastAPI\n:8000"]
            PX["🔭 Arize Phoenix\n:6006"]
            MK["📚 MkDocs\n:8080"]
        end

        subgraph RAG["LangChain RAG Pipeline"]
            LD["📄 Document Loader\nPyPDF / TextLoader"]
            SP["✂️ Text Splitter\nRecursiveCharacter"]
            EM["🔢 OpenAI Embeddings\ntext-embedding-ada-002"]
            DB[("🗄️ ChromaDB\nPersistentClient\n/data/chromadb")]
        end

        SV --> Services
        API --> LD --> SP --> EM --> DB
    end

    OAI(["☁️ OpenAI API"])

    U -->|":8501"| ST
    U -->|":8000"| API
    U -->|":6006"| PX
    U -->|":8080"| MK
    ST -->|"REST + JWT"| API
    EM <-->|"embeddings"| OAI
    API <-->|"chat completion"| OAI
    API -->|"OTLP traces"| PX
```

> All four ports (`8000`, `6006`, `8501`, `8080`) are exposed from the same container.
> Data is persisted in the `/data` volume: uploads, ChromaDB collections, and Phoenix traces.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API framework | FastAPI + Uvicorn |
| Authentication | OAuth2 Password Flow + JWT (`python-jose`) |
| Password hashing | `passlib` bcrypt |
| Document loading | LangChain `PyPDFLoader`, `TextLoader` |
| Text splitting | `RecursiveCharacterTextSplitter` (1 000 chars, 150 overlap) |
| Embeddings | OpenAI `text-embedding-ada-002` |
| Vector store | ChromaDB (`PersistentClient`, embedded) |
| LLM | OpenAI `gpt-4o-mini` |
| UI | Streamlit |
| Tracing | Arize Phoenix + OpenTelemetry |
| Process manager | supervisord |
| Runtime | Python 3.13 |
| Containerization | Docker (single image) |
| Docs | MkDocs Material |

---

## Data Flow

### Upload flow

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as FastAPI :8000
    participant FS as File System /data/uploads
    participant LC as LangChain
    participant OE as OpenAI Embeddings
    participant DB as ChromaDB (embedded)

    C->>A: POST /auth/login (form)
    A-->>C: JWT access_token

    C->>A: POST /documents (multipart, Bearer)
    A->>FS: Save raw file

    alt .pdf or .txt AND OPENAI_API_KEY set
        A->>LC: Load document
        LC->>LC: Split into chunks<br/>(1 000 chars, 150 overlap)
        LC->>OE: Embed chunks
        OE-->>LC: Vectors
        LC->>DB: add_documents(chunks)
        DB-->>A: OK
        A-->>C: 200 {"ingested": N, "filename": "..."}
    else unsupported type or no API key
        A-->>C: 200 {"ingested": 0, "filename": "..."}
    end
```

### Query flow

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as FastAPI :8000
    participant DB as ChromaDB (embedded)
    participant LC as LangChain LCEL
    participant OA as OpenAI gpt-4o-mini
    participant PX as Arize Phoenix

    C->>A: POST /rag/query {"question": "..."}
    A->>DB: collection.count()

    alt collection empty
        DB-->>A: 0
        A-->>C: 404 No documents indexed
    else has documents
        DB-->>A: N
        A->>DB: similarity_search(question, k=4)
        DB-->>A: top-4 chunks + metadata
        A->>LC: chain.invoke({context, question})
        LC->>OA: ChatCompletion
        OA-->>LC: answer text
        LC-->>A: answer
        A-->>PX: OTLP trace (inputs, outputs, latency)
        A-->>C: 200 {"answer": "...", "sources": [...]}
    end
```

---

## Volume Layout

```mermaid
graph LR
    V[("📦 doc_qa_data\nDocker volume")]
    V --> U["/data/uploads\nraw uploaded files"]
    V --> C["/data/chromadb\nChromaDB collection"]
    V --> P["/data/phoenix\nPhoenix traces"]
```
