"""
Ponto de entrada da aplicação FastAPI.

Responsabilidades:
- Criação e configuração da app
- Registro de middlewares
- Inclusão de rotas
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.chat import router as chat_router

app = FastAPI(
    title="LLM Service",
    description="Serviço de chamada a LLMs via OpenRouter",
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
