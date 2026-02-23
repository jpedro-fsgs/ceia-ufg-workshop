# CH5 — Deploy de um Serviço LLM com Pipeline Completo

Este documento guia você pelo processo completo: do código rodando localmente até o deploy automático na nuvem via pipeline de CI/CD.

---

## Visão Geral do Pipeline

Cada `push` na branch `main` com mudanças nesta pasta dispara a seguinte cadeia automática:

```
Você faz git push
      ↓
GitHub Actions detecta a mudança
      ↓
Autentica no Google Cloud e aciona o Cloud Build
      ↓
Cloud Build faz o build da imagem Docker
      ↓
Imagem é enviada para o Artifact Registry
      ↓
Cloud Run sobe o serviço com a nova imagem
      ↓
Serviço disponível publicamente via HTTPS ✅
```

---

## Estrutura do Projeto

```
pratica/
├── app/
│   ├── main.py          # Ponto de entrada da API (FastAPI)
│   ├── models.py        # Schemas de entrada e saída (Pydantic)
│   ├── client.py        # Cliente OpenRouter via OpenAI SDK
│   ├── prompts.py       # Prompts do sistema (edite aqui)
│   └── routes/
│       └── chat.py      # Endpoint POST /chat
│
├── Dockerfile.dev       # Imagem Docker para desenvolvimento local
├── cloudbuild.yaml      # Instruções de build e deploy no GCP
├── requirements.txt     # Dependências Python
└── .env.example         # Variáveis de ambiente necessárias
```

---

## Etapa 1 — Pré-requisitos

Antes de começar, você precisa ter instalado:

- [Docker](https://docs.docker.com/get-docker/)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- API Key do [Google AI Studio](https://aistudio.google.com/apikey) (gratuita)

E ter acesso a um projeto no Google Cloud com os seguintes serviços habilitados:
- Cloud Build
- Cloud Run
- Artifact Registry

---

## Etapa 2 — Rodando Localmente

### 2.1 Criar o arquivo de variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` e preencha sua chave:

```env
GOOGLE_API_KEY=AIza...
```

> Obtenha sua chave gratuitamente em [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 2.2 Build e start com Docker

```bash
docker build -f Dockerfile.dev -t llm-service:dev .
docker run --env-file .env -p 8000:8000 llm-service:dev
```

### 2.3 Testar o serviço

Acesse a documentação interativa: [http://localhost:8000/docs](http://localhost:8000/docs)

Ou teste via terminal:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Olá! Quem é você?"}],
    "model": "gemini-2.0-flash"
  }'
```

Resposta esperada:
```json
{
  "message": {"role": "assistant", "content": "Olá! Sou um assistente..."},
  "model": "openai/gpt-4o-mini",
  "usage": {"prompt_tokens": 30, "completion_tokens": 25, "total_tokens": 55}
}
```

---

## Etapa 3 — Configurar o Google Cloud

### 3.1 Autenticar no GCP

```bash
gcloud auth login
gcloud config set project SEU_PROJECT_ID
```

### 3.2 Criar o repositório no Artifact Registry

```bash
gcloud artifacts repositories create docker-images \
  --repository-format=docker \
  --location=us-central1
```

### 3.3 Criar a Service Account para o pipeline

```bash
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"
```

Conceder as permissões necessárias:

```bash
gcloud projects add-iam-policy-binding SEU_PROJECT_ID \
  --member="serviceAccount:github-deployer@SEU_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding SEU_PROJECT_ID \
  --member="serviceAccount:github-deployer@SEU_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding SEU_PROJECT_ID \
  --member="serviceAccount:github-deployer@SEU_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

Gerar e baixar a chave JSON:

```bash
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=github-deployer@SEU_PROJECT_ID.iam.gserviceaccount.com
```

> **Atenção:** nunca faça commit deste arquivo. Adicione `sa-key.json` ao seu `.gitignore`.

---

## Etapa 4 — Configurar os Secrets no GitHub

No repositório do GitHub, vá em:
**Settings → Secrets and variables → Actions → New repository secret**

Crie os dois secrets abaixo:

| Nome do Secret | Valor |
|---|---|
| `GCP_PROJECT_ID` | ID do seu projeto GCP (ex: `meu-projeto-123`) |
| `GCP_SA_KEY` | Conteúdo completo do arquivo `sa-key.json` |

---

## Etapa 5 — Deploy Automático

Com tudo configurado, o deploy acontece automaticamente. Basta fazer um push na `main`:

```bash
git add .
git commit -m "feat: ajuste no prompt do serviço LLM"
git push origin main
```

Acompanhe o pipeline em tempo real na aba **Actions** do GitHub.

Quando o pipeline terminar, o Cloud Run exibirá a URL pública do serviço:

```
https://api-blackbox-xxxx-uc.a.run.app
```

---

## Erros Comuns

### `GOOGLE_API_KEY not found` ou `401 Unauthorized`
A variável de ambiente não está configurada. Verifique se o arquivo `.env` existe e está preenchido corretamente. No Docker, confirme que está passando `--env-file .env`.

### `Permission denied` no Cloud Build
A Service Account não tem permissão suficiente. Verifique se os três papéis da Etapa 3.3 foram concedidos corretamente.

### `Repository not found` no Artifact Registry
O repositório `docker-images` não foi criado. Execute o comando da Etapa 3.2.

### Pipeline não dispara no GitHub Actions
Verifique se o commit alterou algum arquivo dentro de `mlops/CH5/`. O trigger do workflow só é ativado quando arquivos nesse caminho são modificados.

### `Invalid credentials` no GitHub Actions
O valor do secret `GCP_SA_KEY` pode estar incompleto ou mal formatado. Cole o conteúdo do `sa-key.json` diretamente, incluindo as chaves `{` e `}`.

### Cloud Run retorna `503 Service Unavailable`
O container iniciou com erro. Verifique os logs diretamente:
```bash
gcloud run services logs read api-blackbox --region=us-central1
```

OBS.: ATENÇÃO ao nome da região, pois uma letra errada produz um erro difícil de debuggar, pois esse tipo de erro não é acusado pelo CLI da GCP
---

## Resultado Final Esperado

Ao final do processo você terá:

- Um serviço LLM rodando no **Cloud Run**, acessível via HTTPS
- Um **pipeline de CI/CD** configurado: qualquer mudança na pasta `mlops/CH5/` e push na `main` resulta em um novo deploy automático
- A **documentação interativa** da API disponível em `https://sua-url.run.app/docs`
