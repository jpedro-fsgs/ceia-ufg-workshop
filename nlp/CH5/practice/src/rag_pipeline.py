import uuid
from typing import Dict, List, Tuple

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from src.settings import (
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    OPENAI_CHAT_MODEL,
    QDRANT_COLLECTION,
    QDRANT_HOST,
    QDRANT_PORT,
)


def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def generate_embeddings(
    model: SentenceTransformer, chunks: List[Dict], batch_size: int = 16
) -> List[Dict]:
    texts = [c["text"] for c in chunks]
    vectors = model.encode(texts, batch_size=batch_size, show_progress_bar=True)

    rows: List[Dict] = []
    for chunk, vector in zip(chunks, vectors):
        rows.append({**chunk, "embedding": vector.tolist()})
    return rows


def recreate_collection(client: QdrantClient, vector_size: int) -> None:
    if client.collection_exists(QDRANT_COLLECTION):
        client.delete_collection(QDRANT_COLLECTION)
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def upload_embeddings(client: QdrantClient, rows: List[Dict]) -> int:
    points = []
    for row in rows:
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, row["chunk_id"]))
        points.append(
            PointStruct(
                id=point_id,
                vector=row["embedding"],
                payload={
                    "chunk_id": row["chunk_id"],
                    "source": row["source"],
                    "chunk_index": row["chunk_index"],
                    "text": row["text"],
                },
            )
        )

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return len(points)


class RAGService:
    def __init__(self):
        self.embedding_model = get_embedding_model()
        self.qdrant_client = get_qdrant_client()
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

    def retrieve(self, question: str, top_k: int = 3) -> List[Dict]:
        query_vector = self.embedding_model.encode(question).tolist()
        hits = self.qdrant_client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=top_k,
        )
        return [hit.payload for hit in hits]

    def answer(self, question: str, top_k: int = 3) -> Tuple[str, List[Dict]]:
        if self.openai_client is None:
            raise RuntimeError("OPENAI_API_KEY não configurada. Crie um arquivo .env.")

        contexts = self.retrieve(question=question, top_k=top_k)
        context_text = "\n\n".join(
            [f"[Fonte {i + 1}] {ctx['text']}" for i, ctx in enumerate(contexts)]
        )

        prompt = (
            "Responda usando somente o contexto recuperado.\n"
            "Se a resposta não estiver no contexto, diga explicitamente que não encontrou.\n\n"
            f"Contexto:\n{context_text}\n\nPergunta: {question}"
        )

        completion = self.openai_client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente objetivo e fiel ao contexto fornecido.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        return completion.choices[0].message.content or "", contexts
