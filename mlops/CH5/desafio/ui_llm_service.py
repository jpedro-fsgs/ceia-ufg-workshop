"""
Desafio CH5 — Interface de Chat para o Serviço LLM

Objetivo: construir uma UI de chat com Streamlit que consome
a API do serviço LLM rodando no Cloud Run.

Siga os comentários marcados com TODO para implementar cada parte.
Não existe uma única forma certa — use a estrutura abaixo como guia.

Dependências:
    pip install streamlit requests

Como rodar:
    export API_URL=https://seu-servico-xxxx-uc.a.run.app
    streamlit run ui_llm_service.py
"""

import os
import json
import time

import requests
import streamlit as st


# ------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# Dica: st.set_page_config() deve ser a primeira chamada Streamlit
# ------------------------------------------------------------

st.set_page_config(page_title="Chat LLM Service", page_icon="🤖")


# ------------------------------------------------------------
# TÍTULO E DESCRIÇÃO
# ------------------------------------------------------------

st.title("🤖 Chat LLM Service")
st.write("Converse com o serviço LLM publicado no Cloud Run.")


# ------------------------------------------------------------
# URL DA API
# Dica: nunca cole a URL diretamente no código.
#       Leia de uma variável de ambiente com os.getenv().
#       Defina um valor padrão para facilitar testes locais.
# ------------------------------------------------------------

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")


# ------------------------------------------------------------
# HISTÓRICO DE MENSAGENS
# Para que o chat "lembre" das mensagens anteriores durante
# a sessão, você precisa armazená-las em st.session_state.
#
# Estrutura sugerida para cada mensagem:
#   {"role": "user" | "assistant", "content": "texto aqui"}
#
# Dica: inicialize a lista apenas se ela ainda não existir.
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state["messages"] = []


# ------------------------------------------------------------
# EXIBIÇÃO DO HISTÓRICO
# Renderize as mensagens já existentes na tela.
# Dica: st.chat_message(role) cria o balão correto para cada papel.
# ------------------------------------------------------------

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ------------------------------------------------------------
# FUNÇÃO DE CHAMADA À API
# Encapsule a lógica HTTP em uma função separada.
# Isso facilita testes e deixa o código mais organizado.
#
# Assinatura sugerida:
#   def call_llm(messages: list[dict]) -> str
#
# O que ela deve fazer:
#   1. Montar o payload no formato que a API espera
#      (consulte /docs do seu serviço para ver o schema)
#   2. Fazer um POST para {API_URL}/chat
#   3. Extrair e retornar apenas o texto da resposta
#   4. Em caso de erro, retornar uma mensagem amigável
#      (não deixe o erro estourar na tela do usuário)
#
# Dica: use requests.post() com o parâmetro json= para o payload
# Dica: inspecione response.json() para ver o que a API retorna
# ------------------------------------------------------------

def stream_llm(messages: list[dict]):
    payload = {
        "messages": messages,
        "model": "gpt-4o-mini",
    }

    try:
        with requests.post(
            f"{API_URL}/chat/stream",
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=(10, 300),
        ) as response:
            response.raise_for_status()

            event_data_lines = []
            for raw_line in response.iter_lines(decode_unicode=True):
                if raw_line is None:
                    continue

                line = raw_line.strip("\r")

                if line == "":
                    if not event_data_lines:
                        continue

                    raw_event = "\n".join(event_data_lines)
                    event_data_lines = []

                    try:
                        event = json.loads(raw_event)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type")
                    if event_type == "token":
                        content = event.get("content", "")
                        if content:
                            yield content
                    elif event_type == "error":
                        yield f"\n\n⚠️ {event.get('content', 'Erro ao processar resposta do modelo.')}"
                        return
                    elif event_type == "done":
                        return

                    continue

                if line.startswith("data:"):
                    event_data_lines.append(line[5:].lstrip())

            if event_data_lines:
                try:
                    event = json.loads("\n".join(event_data_lines))
                    if event.get("type") == "token":
                        content = event.get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    pass
    except requests.RequestException:
        yield (
            "Não consegui conectar ao serviço agora. "
            "Verifique a variável API_URL e tente novamente."
        )


# ------------------------------------------------------------
# CAIXA DE ENTRADA DO USUÁRIO
# Dica: st.chat_input() fica fixo na parte inferior da tela
#       e retorna o texto digitado (ou None se vazio).
# ------------------------------------------------------------

user_input = st.chat_input("Digite sua mensagem...")

# Quando o usuário enviar uma mensagem, você deve:
#   1. Adicioná-la ao histórico (role: "user")
#   2. Exibi-la na tela imediatamente
#   3. Chamar a função call_llm com o histórico completo
#   4. Adicionar a resposta ao histórico (role: "assistant")
#   5. Exibir a resposta na tela

if user_input and user_input.strip():
    user_message = {"role": "user", "content": user_input.strip()}
    st.session_state["messages"].append(user_message)

    with st.chat_message("user"):
        st.markdown(user_message["content"])

    with st.chat_message("assistant"):
        placeholder = st.empty()
        assistant_text = ""
        last_render = 0.0
        for chunk in stream_llm(st.session_state["messages"]):
            assistant_text += chunk

            now = time.perf_counter()
            should_render = (now - last_render) >= 0.05 or chunk.endswith(
                ("\n", ".", "!", "?", ":")
            )
            if should_render:
                placeholder.markdown(f"{assistant_text}▌")
                last_render = now

        if not assistant_text:
            assistant_text = "Não recebi resposta do serviço. Tente novamente."
        placeholder.markdown(assistant_text)

    st.session_state["messages"].append(
        {"role": "assistant", "content": assistant_text}
    )


# ------------------------------------------------------------
# DICAS FINAIS
#
# - st.spinner("...") exibe um indicador de carregamento
#   enquanto a API responde — melhora muito a experiência
#
# - st.error("...") exibe mensagens de erro em vermelho
#
# - Se quiser limpar o histórico, st.button("Nova conversa")
#   combinado com del st.session_state["messages"] funciona bem
#
# - Explore st.sidebar para colocar configurações (ex: URL da API,
#   temperatura do modelo) fora da área principal do chat
# ------------------------------------------------------------
