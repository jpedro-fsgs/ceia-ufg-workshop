"""
Rota de chat — endpoint principal do serviço.
"""

import asyncio
import json

from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import StreamingResponse

from client import get_client
from models import ChatMessage, ChatRequest, ChatResponse
from prompts import SYSTEM_PROMPT

router = APIRouter()


def _build_messages(request: ChatRequest) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m.role, "content": m.content} for m in request.messages]
    return messages


def _sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest = Body(
        ...,
        example={
            "messages": [{"role": "user", "content": "Olá! Quem é você?"}],
            "model": "gpt-4o-mini",
        },
    ),
):
    """
    Envia mensagens para um LLM (OpenAI) e retorna a resposta.

    O sistema injeta automaticamente o SYSTEM_PROMPT antes das mensagens
    do usuário para definir o comportamento do assistente.

    Exemplo de request:
        POST /chat
        {
          "messages": [{"role": "user", "content": "Olá! Quem é você?"}],
                    "model": "gpt-4o-mini"
        }
    """
    client = get_client()

    messages = _build_messages(request)

    try:
        response = await client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao chamar o modelo: {e}",
        ) from e

    return ChatResponse(
        message=ChatMessage(
            role="assistant",
            content=response.choices[0].message.content,
        ),
        model=response.model,
        usage=response.usage.model_dump() if response.usage else {},
    )


@router.post("/chat/stream")
async def chat_completion_stream(
    request: ChatRequest = Body(
        ...,
        example={
            "messages": [{"role": "user", "content": "Olá! Quem é você?"}],
            "model": "gpt-4o-mini",
        },
    ),
):
    """
    Envia mensagens para um LLM (OpenAI) e retorna a resposta em stream SSE.

    Eventos SSE emitidos em `data:`:
    - {"type": "token", "content": "..."}
    - {"type": "done"}
    - {"type": "error", "content": "..."}
    """
    client = get_client()
    messages = _build_messages(request)

    async def event_generator():
        try:
            stream = await client.chat.completions.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta.content
                if not delta:
                    continue

                yield _sse_event({"type": "token", "content": delta})

            yield _sse_event({"type": "done"})

        except asyncio.CancelledError:
            raise

        except Exception as e:
            yield _sse_event(
                {"type": "error", "content": f"Erro ao chamar o modelo: {e}"}
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
