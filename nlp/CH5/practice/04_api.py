from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.rag_pipeline import RAGService

app = FastAPI(title="CH5 RAG API")
rag_service = RAGService()


class ChatRequest(BaseModel):
    pergunta: str = Field(..., min_length=2)
    top_k: int = Field(default=3, ge=1, le=10)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    try:
        resposta, contextos = rag_service.answer(question=req.pergunta, top_k=req.top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Falha no pipeline RAG: {exc}"
        ) from exc

    return {
        "pergunta": req.pergunta,
        "resposta": resposta,
        "fontes": [
            {
                "chunk_id": c["chunk_id"],
                "source": c["source"],
                "chunk_index": c["chunk_index"],
            }
            for c in contextos
        ],
    }
