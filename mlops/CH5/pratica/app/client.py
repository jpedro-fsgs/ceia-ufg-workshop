"""
Cliente Google AI Studio (Gemini) — compatível com a interface da OpenAI SDK.

O Google AI Studio expõe uma API compatível com o padrão da OpenAI,
o que nos permite usar o SDK oficial da OpenAI apontando apenas para
um base_url diferente — sem precisar instalar nenhuma dependência extra.

Como obter sua chave gratuita:
  1. Acesse https://aistudio.google.com/apikey
  2. Clique em "Create API Key"
  3. Copie a chave e cole no seu .env como GOOGLE_API_KEY

Documentação: https://ai.google.dev/gemini-api/docs/openai
"""

import os

from openai import AsyncOpenAI


def get_client() -> AsyncOpenAI:
    """
    Retorna um cliente configurado para usar o Google AI Studio (Gemini).

    A variável GOOGLE_API_KEY deve estar definida no ambiente.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    return AsyncOpenAI(
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
