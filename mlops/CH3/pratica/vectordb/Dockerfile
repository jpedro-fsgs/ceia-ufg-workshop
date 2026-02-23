FROM chromadb/chroma:latest

# Install curl for healthcheck (image has no wget/python3)
RUN apt-get update -qq && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Disable anonymous telemetry
ENV ANONYMIZED_TELEMETRY=false

# Ensure data is persisted to the mounted volume
ENV IS_PERSISTENT=TRUE
ENV PERSIST_DIRECTORY=/chroma/chroma

EXPOSE 8000
