"""
Cliente OpenAI SDK.

Este módulo cria uma instância de `AsyncOpenAI` usando a chave definida
na variável de ambiente `OPENAI_API_KEY`.
"""

import os

from openai import AsyncOpenAI


def get_client() -> AsyncOpenAI:
    """
    Retorna um cliente configurado para usar a API da OpenAI.

    A variável OPENAI_API_KEY deve estar definida no ambiente.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    return AsyncOpenAI(api_key=api_key)
