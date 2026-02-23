from src.document_pipeline import read_jsonl
from src.rag_pipeline import get_qdrant_client, recreate_collection, upload_embeddings
from src.settings import ARTIFACTS_DIR, QDRANT_COLLECTION


def main() -> None:
    embeddings_path = ARTIFACTS_DIR / "embeddings.jsonl"
    rows = read_jsonl(embeddings_path)
    if not rows:
        raise RuntimeError(
            f"Nenhum embedding encontrado em {embeddings_path}. Rode primeiro o script 02."
        )

    vector_size = len(rows[0]["embedding"])
    client = get_qdrant_client()
    recreate_collection(client, vector_size=vector_size)
    uploaded = upload_embeddings(client, rows)

    print(f"Coleção recriada: {QDRANT_COLLECTION}")
    print(f"Vetores inseridos: {uploaded}")


if __name__ == "__main__":
    main()
