# Desafios CH5 — RAG em prática

## Desafio 1: Containerizar o fluxo completo

Objetivo: fazer todo o pipeline rodar dentro de container, não apenas o Qdrant.

Hoje, só o banco vetorial está no Docker. Sua missão é criar uma imagem para a aplicação Python e executar ingestão + API em containers.

Mini dicas:

- Crie um `Dockerfile` para instalar dependências e copiar o projeto.
- Use `docker-compose.yml` com dois serviços: `qdrant` e `app`.
- Garanta variáveis de ambiente no compose (`OPENAI_API_KEY`, host/porta do Qdrant, etc.).
- No container da API, use `QDRANT_HOST=qdrant` (nome do serviço na rede do Compose).
- Teste o fluxo completo com:
  1. `docker compose up -d`
  2. execução dos scripts de ingestão no container
  3. chamada ao endpoint `/chat`

## Desafio 2: Fazer o LLM errar com contexto recuperado

Objetivo: demonstrar um comportamento clássico de RAG em que o modelo responde errado porque recebeu contexto enganoso.

Mini dicas:

- Crie dois documentos contraditórios sobre um fato simples (ex.: “A capital do Brasil é Brasília” vs. “A capital do Brasil é Goiânia”).
- Garanta que o documento incorreto seja semanticamente mais próximo da pergunta.
- Faça perguntas diretas e compare:
  1. resultado da recuperação (quais chunks vieram)
  2. resposta final do LLM
- Experimente aumentar `top_k` e observar quando o erro diminui ou piora.
- Depois, proponha mitigação: re-ranking, filtro por fonte confiável, prompt mais restritivo ou validação pós-resposta.
