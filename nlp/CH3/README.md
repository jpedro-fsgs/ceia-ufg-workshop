Colab: https://colab.research.google.com/drive/1OzWEh-TV4gHutLYxhcnOkKSzRODQchWx?usp=sharing

Apresentação: https://docs.google.com/presentation/d/1OU37_k4vqa0F8Gwx7_mXPiXXjPhQD3l8T2k8HBX6ub8/edit?usp=sharing


# CH3 — Embeddings Avançados, Recuperação de Informação, Bancos Vetoriais e RAG

## Visão Geral do Capítulo

Este capítulo aprofunda os conceitos e práticas relacionados à representação semântica de texto, recuperação de informação e arquiteturas modernas para sistemas baseados em busca semântica. O foco principal é compreender como modelos de embeddings podem ser utilizados para indexação eficiente de conhecimento, como estruturar pipelines de busca semântica e como integrar esses componentes em sistemas Retrieval-Augmented Generation (RAG).

O conteúdo foi projetado para conectar fundamentos teóricos com aplicações práticas, preparando os participantes para construir sistemas capazes de recuperar conhecimento relevante e utilizá-lo para enriquecer respostas de modelos de linguagem.

## Aprofundamento em Modelos de Embeddings

Embeddings são representações vetoriais densas que codificam significado semântico em um espaço matemático contínuo. Diferentemente de representações baseadas em frequência, embeddings capturam relações contextuais e semânticas, permitindo que textos semanticamente similares sejam representados por vetores próximos no espaço vetorial.

Neste capítulo, são exploradas diferenças entre embeddings clássicos e embeddings contextuais, abordando arquiteturas modernas baseadas em Transformers, como Sentence Transformers e modelos otimizados para busca semântica. Também são discutidos fatores que impactam a qualidade de embeddings, incluindo tokenização, tamanho de contexto, normalização vetorial e estratégias de pooling.

Além da teoria, o capítulo demonstra como gerar embeddings para textos em escala, como avaliar sua qualidade e como utilizá-los para tarefas de similaridade semântica, clustering e recuperação de documentos.

## Bancos Vetoriais e Infraestrutura para Busca Semântica

Bancos vetoriais são sistemas especializados para armazenamento e consulta eficiente de embeddings em alta dimensão. Eles implementam algoritmos de Approximate Nearest Neighbors para garantir escalabilidade e baixa latência mesmo com milhões de vetores.

Neste capítulo, é apresentada a arquitetura de um banco vetorial moderno, incluindo processos de ingestão, indexação, busca e filtragem por metadados. Também são discutidas integrações comuns com pipelines de Machine Learning e sistemas de produção, destacando boas práticas para versionamento de embeddings, controle de qualidade dos dados e manutenção de índices.

O conteúdo enfatiza como bancos vetoriais são fundamentais para aplicações como busca semântica, recomendação, análise de similaridade e Retrieval-Augmented Generation.

## Recuperação de Informação Baseada em Similaridade Semântica

Recuperação de informação moderna vai além da correspondência de palavras-chave e passa a considerar similaridade semântica entre consultas e documentos. Sistemas baseados em embeddings transformam consultas e documentos em vetores, permitindo buscas por proximidade em um espaço vetorial.

Este capítulo explora os conceitos de indexação vetorial, métricas de similaridade como cosseno e distância euclidiana, estratégias de chunking para documentos longos e técnicas de otimização para aumentar relevância e reduzir latência. Também são discutidas limitações comuns, como a diferença entre similaridade e relevância e a necessidade de estratégias híbridas que combinem sinais semânticos e léxicos.

## RAG — Retrieval-Augmented Generation na Prática

Retrieval-Augmented Generation é uma arquitetura que combina recuperação de informação com modelos generativos. Em vez de depender apenas do conhecimento interno do modelo, sistemas RAG recuperam documentos relevantes em tempo real e os utilizam como contexto para gerar respostas mais precisas e fundamentadas.

Neste capítulo, é detalhado o fluxo completo de um sistema RAG, desde a ingestão de documentos e geração de embeddings até a recuperação de contexto e integração com modelos de linguagem. Também são discutidas estratégias de chunking, reranking, filtragem contextual e engenharia de prompts para maximizar a qualidade das respostas.

São abordados desafios práticos como redução de alucinações, otimização de custo computacional, controle de latência e avaliação automática de qualidade em pipelines RAG.

## Arquitetura do Projeto do Capítulo

O diretório deste capítulo segue uma organização modular, contendo código para geração de embeddings, indexação vetorial, consultas semânticas e pipelines RAG. A estrutura foi projetada para permitir experimentação incremental, desde consultas básicas até sistemas completos de recuperação aumentada por geração.

O projeto inclui exemplos de ingestão de documentos, criação de índices vetoriais, consultas semânticas e integração com modelos de linguagem para geração de respostas contextualizadas.

## Quickstart — Gerando Embeddings e Criando um Índice Vetorial

O comando abaixo instala as dependências necessárias para execução do pipeline de embeddings e recuperação semântica.

```bash
pip install sentence-transformers qdrant-client fastapi uvicorn
```

O próximo comando executa o script responsável por gerar embeddings a partir de um conjunto de textos e armazená-los em um banco vetorial.

```bash
python scripts/generate_embeddings.py --input data/documents.json --output data/embeddings.json
```

Após a geração dos embeddings, o índice vetorial pode ser criado e inicializado com o seguinte comando.

```bash
python scripts/create_vector_index.py --embeddings data/embeddings.json
```

## Quickstart — Consulta Semântica em Banco Vetorial

Para executar uma consulta semântica e recuperar documentos similares a uma pergunta, utilize o comando abaixo.

```bash
python scripts/query_vector_db.py --query "Explique recuperação de informação baseada em embeddings"
```

Esse comando converte a consulta em embedding, executa a busca vetorial e retorna os documentos mais semanticamente relevantes.

## Quickstart — Executando um Pipeline RAG Completo

O pipeline completo de Retrieval-Augmented Generation pode ser executado com o comando abaixo.

```bash
python scripts/run_rag_pipeline.py --query "O que é RAG e como funciona?"
```

Esse fluxo executa a recuperação de contexto em um banco vetorial, monta um prompt enriquecido e gera uma resposta utilizando um modelo de linguagem.

## Objetivo de Aprendizado do Capítulo

Ao concluir este capítulo, o participante terá compreendido como embeddings são gerados e avaliados, como sistemas de recuperação semântica são estruturados e como bancos vetoriais podem ser integrados em pipelines de produção. Também será capaz de construir um sistema funcional de RAG, combinando busca semântica com geração de linguagem natural.

O conhecimento adquirido neste módulo prepara o terreno para aplicações avançadas em chatbots inteligentes, sistemas de busca semântica corporativos, agentes de conhecimento e plataformas de IA orientadas a contexto.

