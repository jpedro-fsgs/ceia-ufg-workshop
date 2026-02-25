"""
Schemas Pydantic — contratos de dados da API.

Usamos Pydantic para validação automática de tipos e
geração automática da documentação OpenAPI (Swagger).
"""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Representa uma mensagem no formato ChatML.

    Roles:
    - system: instruções de comportamento para o modelo
    - user: mensagem enviada pelo usuário
    - assistant: resposta gerada pelo modelo
    """

    role: str = Field(..., description="Papel da mensagem: system, user ou assistant")
    content: str = Field(..., description="Conteúdo da mensagem")


class ChatRequest(BaseModel):
    """
    Payload de entrada do endpoint POST /chat.

    Exemplo:
        {
            "messages": [{"role": "user", "content": "Olá!"}],
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
    """

    messages: list[ChatMessage] = Field(..., description="Histórico da conversa")

    model: str = Field(
        "gpt-4o-mini",
        description="Modelo OpenAI a ser utilizado",
        examples=["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"],
    )

    temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Criatividade da resposta (0 = determinístico, 2 = muito criativo)",
    )

    max_tokens: int | None = Field(
        None,
        gt=0,
        description="Limite de tokens na resposta. None = sem limite",
    )


class ChatResponse(BaseModel):
    """
    Resposta do endpoint POST /chat.
    """

    message: ChatMessage = Field(..., description="Resposta gerada pelo modelo")
    model: str = Field(..., description="Modelo que gerou a resposta")
    usage: dict = Field(..., description="Contagem de tokens (prompt, completion, total)")
