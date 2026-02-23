# =============================================================================
# Document Q&A API — Monolith
#
# Single image running all services via supervisord:
#   - FastAPI backend        → :8000
#   - Arize Phoenix (traces) → :6006
#   - Streamlit UI           → :8501
#   - MkDocs docs            → :8080
#
# ChromaDB runs embedded (PersistentClient) — no separate process needed.
#
# Build:
#   docker build -t doc-qa .
#
# Run:
#   docker run -d \
#     -e OPENAI_API_KEY=sk-... \
#     -e SECRET_KEY=$(openssl rand -hex 32) \
#     -e APP_USER=admin:changeme \
#     -p 8000:8000 -p 6006:6006 -p 8501:8501 -p 8080:8080 \
#     -v doc_qa_data:/data \
#     doc-qa
# =============================================================================

FROM python:3.13-slim

# ---------------------------------------------------------------------------
# System packages
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        supervisor \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------------
# Python dependencies
# All services (API + Phoenix + Streamlit + MkDocs) installed in one layer.
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    `# API` \
    fastapi "uvicorn[standard]" \
    langchain langchain-community langchain-openai langchain-chroma langchain-google-genai \
    chromadb \
    "passlib[bcrypt]" pypdf python-dotenv "python-jose[cryptography]" python-multipart \
    `# Observability` \
    arize-phoenix arize-phoenix-otel \
    opentelemetry-instrumentation-fastapi \
    openinference-instrumentation-langchain openinference-instrumentation-openai \
    `# Streamlit UI` \
    streamlit requests \
    `# MkDocs docs` \
    mkdocs-material

# ---------------------------------------------------------------------------
# Application sources
# ---------------------------------------------------------------------------
COPY main.py ./
COPY streamlit_app/app.py ./streamlit_app/
COPY docs/ ./docs/
COPY mkdocs.yml ./

# ---------------------------------------------------------------------------
# Persistent data directories (override with a named volume in production)
# ---------------------------------------------------------------------------
RUN mkdir -p /data/uploads /data/chromadb /data/phoenix

# ---------------------------------------------------------------------------
# Process manager
# ---------------------------------------------------------------------------
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# API · Phoenix · Streamlit · MkDocs
EXPOSE 8000 6006 8501 8080

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
