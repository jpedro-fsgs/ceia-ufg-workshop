from src.document_pipeline import read_jsonl, write_jsonl
from src.rag_pipeline import generate_embeddings, get_embedding_model
from src.settings import ARTIFACTS_DIR


def main() -> None:
    chunks_path = ARTIFACTS_DIR / "chunks.jsonl"
    chunks = read_jsonl(chunks_path)
    if not chunks:
        raise RuntimeError(
            f"Nenhum chunk encontrado em {chunks_path}. Rode primeiro o script 01."
        )

    model = get_embedding_model()
    rows = generate_embeddings(model, chunks)

    output_path = ARTIFACTS_DIR / "embeddings.jsonl"
    write_jsonl(output_path, rows)

    print(f"Embeddings gerados: {len(rows)}")
    print(f"Arquivo salvo em: {output_path}")


if __name__ == "__main__":
    main()
