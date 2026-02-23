import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

from pypdf import PdfReader

from src.settings import CHUNK_OVERLAP, CHUNK_SIZE


def load_documents(directory: Path) -> List[Dict[str, str]]:
    docs: List[Dict[str, str]] = []
    supported = {".txt", ".md", ".pdf"}

    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in supported:
            continue
        text = extract_document_text(path)
        if not text:
            continue
        docs.append({"source": str(path), "text": normalize_whitespace(text)})

    return docs


def extract_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8").strip()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    return ""


def extract_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: List[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(page_text)

    return "\n".join(pages).strip()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_text(
    text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> List[str]:
    if overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP deve ser menor que CHUNK_SIZE.")

    chunks: List[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_len:
            break
        start = max(0, end - overlap)

    return chunks


def build_chunks(documents: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    result: List[Dict[str, str]] = []
    for doc in documents:
        chunks = split_text(doc["text"])
        for idx, chunk_text in enumerate(chunks):
            chunk_id = f"{Path(doc['source']).name}::chunk_{idx:04d}"
            result.append(
                {
                    "chunk_id": chunk_id,
                    "source": doc["source"],
                    "chunk_index": idx,
                    "text": chunk_text,
                }
            )
    return result


def write_jsonl(path: Path, rows: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
