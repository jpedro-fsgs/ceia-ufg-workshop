import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    AskRequest,
    AskResponse,
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
)
from services import OrchestratorService, seed_database

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Global Service
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    logger.info("Startup: Initializing Services...")

    # Initialize implementation
    orchestrator = OrchestratorService()

    # Run Seeder
    # Note: embedder model download might happen here
    seed_database(orchestrator.vector_db)

    yield
    logger.info("Shutdown: Cleaning up...")


app = FastAPI(title="Medical RAG (Edu)", version="3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Initializing")
    
    # Granular health check
    health_status = orchestrator.get_health()
    return {
        "status": "ok", 
        "mode": "edu",
        "services": {
            "api": "online",
            **health_status
        }
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest):
    try:
        count = orchestrator.vector_db.ingest(request.texts, request.source)
        return IngestResponse(
            collection=orchestrator.vector_db.collection_name, inserted=count
        )
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest-file")
async def ingest_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        count = orchestrator.process_and_ingest_file(content, file.filename)
        return {
            "filename": file.filename,
            "inserted_chunks": count,
            "status": "success",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    results = orchestrator.vector_db.search(request.query, request.top_k)
    return SearchResponse(results=results)


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        answer, docs, debug_texts, debug_prompt = orchestrator.ask(request.question)

        return AskResponse(
            answer=answer,
            context=docs,
            retrieved_docs=docs,
            built_prompt=debug_prompt
        )
    except Exception as e:
        logger.error(f"Error generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
