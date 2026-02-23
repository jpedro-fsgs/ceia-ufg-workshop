"""
Prompts do sistema.

Centralize aqui todos os prompts para facilitar ajustes
sem precisar alterar a lógica da aplicação.
"""

SYSTEM_PROMPT = """
Você é um assistente prestativo, honesto e objetivo.
Responda sempre em português do Brasil.
Seja claro e conciso nas suas respostas.
""".strip()

# TODO: Adicionar outro prompt aqui e testar o import do prompt no arquivo routes/chat.py