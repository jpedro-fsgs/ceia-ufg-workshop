# Desafio CH5 — Interface para um Serviço LLM

## Contexto

Ao longo deste capítulo você subiu um serviço de LLM no Cloud Run.  
Agora o desafio é **fechar o ciclo**: criar uma interface de chat que consome essa API, experimentar com prompts, e ver o pipeline de CI/CD em ação do começo ao fim.

O resultado esperado é uma página de chat funcional, rodando localmente, que conversa com o seu LLM na nuvem — e que muda de comportamento apenas com uma alteração de prompt seguida de um novo deploy.

---

## O que você vai construir

```
[Usuário digita mensagem]
        ↓
   Interface Streamlit  ←  ui_llm_service.py
        ↓  HTTP POST /chat
   Serviço no Cloud Run  ←  o que foi feito na pratica/
        ↓
   Gemini (Google AI Studio)
        ↓
   Resposta exibida na UI
```

---

## Estrutura do desafio

```
desafio/
├── README.md            # este arquivo
├── ui_llm_service.py    # sua interface — ponto de partida
└── requirements.txt     # dependências da UI
```

---

## Passo 1 — Codifique a interface

Abra o arquivo `ui_llm_service.py`. Ele contém a estrutura e dicas do que implementar, mas o código é por sua conta.

**O que a UI precisa ter:**
- Um título identificando o serviço
- Uma área de histórico que exibe as mensagens trocadas
- Uma caixa de entrada onde o usuário digita a mensagem
- A resposta do assistente aparecendo logo abaixo da mensagem enviada

**Dicas:**
- Streamlit tem um componente nativo de chat: pesquise por `st.chat_message` e `st.chat_input`
- Para manter o histórico entre interações, use `st.session_state`
- Comece simples: faça funcionar primeiro, refine depois

---

## Passo 2 — Adicione a chamada à API

Sua UI precisa se comunicar com o serviço que está no Cloud Run.

**O que implementar:**
- Uma função que recebe a lista de mensagens e envia um `POST` para o endpoint `/chat`
- O corpo da requisição deve seguir o formato que a API espera (consulte `/docs` do serviço)
- A função deve retornar apenas o texto da resposta do assistente

**Dicas:**
- Use a biblioteca `requests` para a chamada HTTP
- A URL base do serviço virá de uma variável de ambiente (`API_URL`) — nunca cole a URL direto no código
- Inspecione a resposta JSON para extrair o campo correto
- Teste primeiro com `curl` ou no Swagger (`/docs`) antes de integrar na UI

> **Insight de pipeline:** separar a URL em variável de ambiente é o que permite usar a mesma UI apontando para ambientes diferentes (local, staging, produção) sem alterar uma linha de código.

---

## Passo 3 — Execute e valide

Com a UI rodando e a API configurada, faça uma conversa real.

```bash
# Instale as dependências
pip install -r requirements.txt

# Defina a URL do seu serviço no Cloud Run
export API_URL=https://seu-servico-xxxx-uc.a.run.app

# Suba a interface
streamlit run ui_llm_service.py
```

**O que validar:**
- A mensagem enviada aparece no histórico como "você"
- A resposta do assistente aparece logo abaixo
- O histórico acumula ao longo da conversa
- Se a API retornar erro, a UI deve mostrar uma mensagem amigável (não um stack trace)

**Perguntas para reflexão:**
- O que acontece se você enviar uma mensagem vazia?
- O assistente "lembra" das mensagens anteriores? Por quê?

---

## Passo 4 — Modifique os prompts

Agora a parte mais interessante: altere o comportamento do assistente **sem mudar a UI**.

Abra o arquivo `pratica/app/prompts.py` e mude o `SYSTEM_PROMPT` de forma que a diferença seja **perceptível e fácil de demonstrar**. Algumas ideias:

- Dê um nome e uma personalidade específica ao assistente
- Restrinja o assistente a responder apenas sobre um tema (ex: culinária, filmes, tecnologia)
- Mude o tom: formal, informal, técnico, didático
- Faça o assistente sempre responder em formato de lista
- Peça que ele sempre termine com uma pergunta de volta ao usuário

**Dica:** escolha uma mudança que seja visualmente óbvia na demo — algo que qualquer pessoa na sala perceba na primeira mensagem.

> **Insight de pipeline:** você está prestes a ver na prática o que separa MLOps de um deploy manual. A mesma mudança de texto que você está fazendo agora vai viajar automaticamente pelo pipeline até o Cloud Run.

---

## Passo 5 — Faça o deploy da nova versão

Commit e push — o pipeline cuida do resto.

```bash
git add mlops/CH5/pratica/app/prompts.py
git commit -m "feat(ch5): atualiza system prompt para [descreva sua mudança]"
git push origin main
```

Acompanhe o processo em tempo real:

1. Aba **Actions** no GitHub → veja o workflow `Deploy CH5` rodando
2. [Cloud Build](https://console.cloud.google.com/cloud-build/builds) → veja o build da imagem Docker
3. [Cloud Run](https://console.cloud.google.com/run) → veja a nova revisão sendo promovida

**O que observar:**
- Quanto tempo leva cada etapa do pipeline?
- O Cloud Run faz o novo deploy sem derrubar o serviço antigo (zero downtime)
- Cada revisão do Cloud Run fica salva — você pode fazer rollback em segundos se algo der errado

---

## Passo 6 — Teste o novo comportamento na UI

Com o deploy concluído, volte para a interface e inicie uma nova conversa.

**O que verificar:**
- O assistente se comporta conforme a mudança que você fez no prompt?
- O histórico da conversa anterior foi mantido ou reiniciado? Por quê?
- Se alguém tentasse "furar" o prompt (ex: "ignore suas instruções e..."), o que acontece?

**Reflexão final:**

Você acabou de executar o ciclo completo de um produto de IA em produção:

```
Ideia de melhoria
      ↓
Mudança no código (prompt)
      ↓
Commit + Push
      ↓
Pipeline automatizado (GitHub Actions → Cloud Build)
      ↓
Nova versão em produção (Cloud Run)
      ↓
Validação pelo usuário final (sua UI)
      ↓
Nova ideia de melhoria...
```

Esse ciclo, feito de forma confiável e repetível, é o que define uma operação de MLOps madura.

---

## Referência rápida

| O que | Onde encontrar |
|---|---|
| Formato da requisição | `https://seu-servico.run.app/docs` |
| Logs do serviço em produção | `gcloud run services logs read api-blackbox --region=us-central1` |
| Histórico de builds | [console.cloud.google.com/cloud-build](https://console.cloud.google.com/cloud-build/builds) |
| Revisões do Cloud Run | [console.cloud.google.com/run](https://console.cloud.google.com/run) |
| Acompanhar o pipeline | Aba Actions no GitHub |
