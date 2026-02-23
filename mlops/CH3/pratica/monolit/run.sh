#!/usr/bin/env bash
set -e

IMAGE_NAME="doc-qa"
CONTAINER_NAME="doc-qa-monolit"

# Build da imagem
docker build -t "$IMAGE_NAME" "$(dirname "$0")"

# Sobe o container
docker run -d \
  --name "$CONTAINER_NAME" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY:?Defina a variável OPENAI_API_KEY}" \
  -e SECRET_KEY="$(openssl rand -hex 32)" \
  -e APP_USER="${APP_USER:-admin:changeme}" \
  ${GOOGLE_API_KEY:+-e GOOGLE_API_KEY="$GOOGLE_API_KEY"} \
  ${GOOGLE_MODEL:+-e GOOGLE_MODEL="$GOOGLE_MODEL"} \
  -p 8000:8000 \
  -p 6006:6006 \
  -p 8501:8501 \
  -p 8080:8080 \
  -v doc_qa_data:/data \
  "$IMAGE_NAME"

echo ""
echo "Container '$CONTAINER_NAME' rodando. Portas expostas:"
echo "  FastAPI  → http://localhost:8000/docs"
echo "  Phoenix  → http://localhost:6006"
echo "  Streamlit→ http://localhost:8501"
echo "  MkDocs   → http://localhost:8080"
