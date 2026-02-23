from src.document_pipeline import build_chunks, load_documents, write_jsonl
from src.settings import ARTIFACTS_DIR, DOCUMENTS_DIR


def main() -> None:
    docs = load_documents(DOCUMENTS_DIR)
    if not docs:
        raise RuntimeError(
            f"Nenhum documento encontrado em {DOCUMENTS_DIR}. "
            "Adicione arquivos .txt, .md ou .pdf na pasta de documentos."
        )

    chunks = build_chunks(docs)
    output_path = ARTIFACTS_DIR / "chunks.jsonl"
    write_jsonl(output_path, chunks)

    print(f"Documentos processados: {len(docs)}")
    print(f"Chunks gerados: {len(chunks)}")
    print(f"Arquivo salvo em: {output_path}")


if __name__ == "__main__":
    main()
