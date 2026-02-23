import io
import logging
import os
import uuid
from typing import Dict, List, Tuple

import docx
import pypdf
import pytesseract
import requests
from fastembed import TextEmbedding
from PIL import Image
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    @staticmethod
    def process_pdf(file_content: bytes) -> str:
        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return ""

    @staticmethod
    def process_docx(file_content: bytes) -> str:
        try:
            doc = docx.Document(io.BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error processing DOCX: {e}")
            return ""

    @staticmethod
    def process_image(file_content: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(file_content))
            return pytesseract.image_to_string(image)
        except Exception as e:
            logger.error(f"Error processing Image: {e}")
            return ""

    @staticmethod
    def process_txt(file_content: bytes) -> str:
        try:
            return file_content.decode("utf-8")
        except Exception as e:
            logger.error(f"Error processing TXT: {e}")
            return ""


class VectorDbService:
    def __init__(self):
        self.collection_name = os.getenv("QDRANT_COLLECTION", "workshop_docs")
        qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

        logger.info("Loading FastEmbed model...")
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        logger.info(f"Connecting to Qdrant: {qdrant_host}:{qdrant_port}")
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.vector_size = 384

    def ensure_collection(self) -> None:
        try:
            if not self.qdrant.collection_exists(self.collection_name):
                logger.info(f"Creating collection: {self.collection_name}")
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_size,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")

    def check_health(self) -> bool:
        try:
            # Lightweight check: get collection info
            self.qdrant.get_collection(self.collection_name)
            return True
        except Exception:
            return False

    def ingest(self, texts: List[str], source: str) -> int:
        self.ensure_collection()
        if not texts:
            return 0

        embeddings = list(self.embedder.embed(texts))

        points = [
            qmodels.PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload={"text": text, "source": source},
            )
            for text, emb in zip(texts, embeddings)
        ]

        self.qdrant.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def search(self, query: str, top_k: int) -> List[Dict]:
        query_vector = list(self.embedder.embed([query]))[0].tolist()

        try:
            if hasattr(self.qdrant, "query_points"):
                hits = self.qdrant.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=top_k,
                    with_payload=True,
                ).points
            elif hasattr(self.qdrant, "search"):
                hits = self.qdrant.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    with_payload=True,
                )
            else:
                # HTTP Fallback
                url = f"{self.qdrant.rest_uri}/collections/{self.collection_name}/points/search"
                resp = requests.post(
                    url,
                    json={"vector": query_vector, "limit": top_k, "with_payload": True},
                )
                resp.raise_for_status()
                hits = []

            return [
                {
                    "text": hit.payload.get("text", ""),
                    "source": hit.payload.get("source", "unknown"),
                    "score": float(hit.score),
                }
                for hit in hits
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


class LLMService:
    def __init__(self):
        # External LLM Service URL
        self.api_url = os.getenv("LLM_API_URL", "http://llm_service:8000/v1")
        logger.info(f"LLM Service URL: {self.api_url}")

    def generate_response(self, context: str, question: str) -> Tuple[str, str]:
        """Returns (answer, full_prompt)"""

        system_prompt = "Você é um assistente médico útil e preciso. Use o contexto abaixo para responder à pergunta."

        # OpenaAI-compatible Prompt Construction
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\nContexto:\n{context}"},
            {"role": "user", "content": question},
        ]

        # Visualize prompt for education
        full_prompt_debug = (
            f"SYSTEM: {system_prompt}\nCONTEXT: {context}\nUSER: {question}"
        )

        try:
            resp = requests.post(
                f"{self.api_url}/chat/completions",
                json={"messages": messages, "max_tokens": 512, "temperature": 0.3},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
            return answer, full_prompt_debug
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"Erro ao contatar LLM: {str(e)}", full_prompt_debug

    def check_health(self) -> bool:
        try:
            # Lightweight check to LLM models endpoint
            resp = requests.get(f"{self.api_url}/models", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

class OrchestratorService:
    def __init__(self):
        self.vector_db = VectorDbService()
        self.llm_service = LLMService()
        self.document_processor = DocumentProcessor()

    def ask(self, question: str) -> Tuple[str, List[Dict], List[str], str]:
        # 1. Retrieve
        docs = self.vector_db.search(question, top_k=3)
        retrieved_texts = [d["text"] for d in docs]
        context_str = "\n".join([f"- {t}" for t in retrieved_texts])

        # 2. Generate
        answer, debug_prompt = self.llm_service.generate_response(context_str, question)

        return answer, docs, retrieved_texts, debug_prompt
    
    def get_health(self) -> Dict[str, str]:
        return {
            "vector_db": "online" if self.vector_db.check_health() else "offline",
            "llm": "online" if self.llm_service.check_health() else "offline"
        }
    
    def process_and_ingest_file(self, content: bytes, filename: str) -> int:
        ext = filename.split(".")[-1].lower()
        text = ""

        if ext == "pdf":
            text = self.document_processor.process_pdf(content)
        elif ext in ["docx", "doc"]:
            text = self.document_processor.process_docx(content)
        elif ext in ["png", "jpg", "jpeg", "tiff"]:
            text = self.document_processor.process_image(content)
        elif ext == "txt":
            text = self.document_processor.process_txt(content)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        if not text.strip():
            logger.warning(f"No text extracted from {filename}")
            return 0

        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        if not chunks:
            chunks = [text]  # Fallback

        return self.vector_db.ingest(chunks, source=filename)


# --- Seeder Logic ---
MEDICAL_DATA = [
    (
        "Protocolo de Manchester: Classifica riscos por cores. Vermelho (Emergência - 0min), Laranja (Muito Urgente - 10min), Amarelo (Urgente - 60min), Verde (Pouco Urgente - 120min), Azul (Não Urgente - 240min).",
        "Protocolos Triage",
    ),
    (
        "Anamnese é a entrevista inicial realizada pelo profissional de saúde para identificar sintomas, histórico e queixas do paciente.",
        "Conceitos Básicos",
    ),
    (
        "Sintomas de Dengue: Febre alta, dor de cabeça, dor atrás dos olhos, dores no corpo de articulações.",
        "Doenças Tropicais",
    ),
    (
        "Sintomas de Covid-19: Febre, tosse seca, cansaço, perda de paladar ou olfato.",
        "Doenças Respiratórias",
    ),
    (
        "Hipertensão Arterial: Condição em que a força do sangue contra a parede das artérias é muito grande. Acima de 140/90 mmHg.",
        "Cardiologia",
    ),
    (
        "Diabetes Tipo 2: Condição crônica que afeta a forma como o corpo processa o açúcar no sangue (glicose).",
        "Endocrinologia",
    ),
    (
        "AVC Isquêmico: Ocorre quando há obstrução de uma artéria, impedindo a passagem de oxigênio para células cerebrais.",
        "Neurologia",
    ),
    (
        "AVC Hemorrágico: Ocorre quando há rompimento de um vaso cerebral, provocando hemorragia.",
        "Neurologia",
    ),
    (
        "Infarto Agudo do Miocárdio: Necrose de parte do músculo cardíaco causada pela ausência de irrigação sanguínea.",
        "Cardiologia",
    ),
    (
        "Arritmia Cardíaca: Alterações na frequência ou no ritmo dos batimentos cardíacos.",
        "Cardiologia",
    ),
    (
        "Insuficiência Cardíaca: O coração não consegue bombear sangue suficiente para atender às necessidades do corpo.",
        "Cardiologia",
    ),
    (
        "Asma: Doença inflamatória crônica das vias aéreas que causa dificuldade respiratória.",
        "Pneumologia",
    ),
    (
        "DPOC: Doença Pulmonar Obstrutiva Crônica, caracteriza-se pela obstrução do fluxo de ar nos pulmões.",
        "Pneumologia",
    ),
    (
        "Pneumonia: Infecção que inflama os sacos de ar em um ou ambos os pulmões, que podem ficar cheios de fluido.",
        "Pneumologia",
    ),
    (
        "Tuberculose: Doença infecciosa causada pela bactéria Mycobacterium tuberculosis, que afeta principalmente os pulmões.",
        "Infectologia",
    ),
    (
        "HIV/AIDS: Vírus que ataca o sistema imunológico do corpo. AIDS é o estágio mais avançado da infecção pelo HIV.",
        "Infectologia",
    ),
    ("Hepatite B: Infecção viral grave que ataca o fígado.", "Infectologia"),
    (
        "Dengue: Doença viral transmitida pelo mosquito Aedes aegypti.",
        "Doenças Tropicais",
    ),
    (
        "Zika Vírus: Transmitido pelo Aedes aegypti, pode causar microcefalia em bebês se a mãe for infectada na gravidez.",
        "Doenças Tropicais",
    ),
    (
        "Chikungunya: Doença viral transmitida por mosquitos que causa febre e fortes dores nas articulações.",
        "Doenças Tropicais",
    ),
    (
        "Malária: Doença causada por parasitas transmitidos pela picada de mosquitos Anopheles infectados.",
        "Doenças Tropicais",
    ),
    (
        "Leptospirose: Doença bacteriana transmitida pela urina de animais infectados, principalmente ratos.",
        "Infectologia",
    ),
    ("Diabetes Tipo 1: O pâncreas produz pouca ou nenhuma insulina.", "Endocrinologia"),
    (
        "Hipotireoidismo: A glândula tireoide não produz hormônios suficientes.",
        "Endocrinologia",
    ),
    (
        "Hipertireoidismo: A glândula tireoide produz hormônios em excesso.",
        "Endocrinologia",
    ),
    (
        "Obesidade: Acúmulo anormal ou excessivo de gordura que apresenta risco à saúde.",
        "Endocrinologia",
    ),
    (
        "Anemia Ferropriva: Tipo mais comum de anemia, causada pela deficiência de ferro.",
        "Hematologia",
    ),
    (
        "Leucemia: Câncer dos tecidos formadores de sangue, incluindo a medula óssea.",
        "Oncologia",
    ),
    ("Linfoma: Câncer que começa nas células do sistema linfático.", "Oncologia"),
    ("Câncer de Mama: Crescimento descontrolado de células da mama.", "Oncologia"),
    ("Câncer de Próstata: Câncer que ocorre na próstata.", "Oncologia"),
    ("Câncer de Pele Melanoma: Tipo mais grave de câncer de pele.", "Oncologia"),
    (
        "Alzheimer: Doença progressiva que destrói a memória e outras funções mentais importantes.",
        "Neurologia",
    ),
    (
        "Parkinson: Doença degenerativa do sistema nervoso central que afeta o movimento, muitas vezes com tremores.",
        "Neurologia",
    ),
    (
        "Epilepsia: Distúrbio do sistema nervoso central em que a atividade das células nervosas no cérebro é perturbada, causando convulsões.",
        "Neurologia",
    ),
    (
        "Esclerose Múltipla: Doença em que o sistema imunológico destrói a cobertura protetora de nervos.",
        "Neurologia",
    ),
    (
        "Depressão: Transtorno de saúde mental caracterizado por depressão persistente ou perda de interesse nas atividades.",
        "Psiquiatria",
    ),
    (
        "Ansiedade Generalizada: Preocupação excessiva e persistente e ansiedade sobre vários eventos ou atividades.",
        "Psiquiatria",
    ),
    (
        "Transtorno Bipolar: Distúrbio associado a episódios de alterações de humor que variam de baixos depressivos a altos maníacos.",
        "Psiquiatria",
    ),
    (
        "Esquizofrenia: Transtorno que afeta a capacidade de uma pessoa de pensar, sentir e se comportar com clareza.",
        "Psiquiatria",
    ),
    (
        "Autismo (TEA): Transtorno do desenvolvimento que afeta a comunicação e o comportamento.",
        "Psiquiatria",
    ),
    (
        "Bursite: Inflamação das pequenas bolsas cheias de líquido (bursas) que protegem as articulações.",
        "Ortopedia",
    ),
    ("Tendinite: Inflamação ou irritação de um tendão.", "Ortopedia"),
    (
        "Osteoporose: Condição em que os ossos se tornam frágeis e quebradiços.",
        "Ortopedia",
    ),
    (
        "Hérnia de Disco: Ocorre quando parte de um disco intervertebral sai de sua posição normal e comprime as raízes nervosas.",
        "Ortopedia",
    ),
    ("Gastrite: Inflamação do revestimento do estômago.", "Gastroenterologia"),
    (
        "Refluxo Gastroesofágico: Doença digestiva em que o ácido do estômago ou a bile volta pelo esôfago.",
        "Gastroenterologia",
    ),
    (
        "Úlcera Péptica: Ferida no revestimento do estômago, intestino delgado ou esôfago.",
        "Gastroenterologia",
    ),
    (
        "Cirrose: Lesão hepática crônica de várias causas que leva à formação de cicatrizes e insuficiência hepática.",
        "Gastroenterologia",
    ),
    (
        "Cálculo Renal: Depósitos duros de minerais e sais que se formam dentro dos rins.",
        "Nefrologia",
    ),
    ("Insuficiência Renal Crônica: Perda gradual da função renal.", "Nefrologia"),
    (
        "Infecção Urinária: Infecção em qualquer parte do sistema urinário, rins, bexiga ou uretra.",
        "Nefrologia",
    ),
    (
        "Conjuntivite: Inflamação ou infecção da membrana externa do globo ocular e da pálpebra interior.",
        "Oftalmologia",
    ),
    (
        "Glaucoma: Grupo de condições oculares que danificam o nervo óptico.",
        "Oftalmologia",
    ),
    (
        "Catarata: Opacidade do cristalino do olho que leva a uma diminuição na visão.",
        "Oftalmologia",
    ),
    (
        "Otite Média: Infecção do espaço cheio de ar atrás do tímpano.",
        "Otorrinolaringologia",
    ),
]


def seed_database(service: VectorDbService):
    try:
        service.ensure_collection()
        count = service.qdrant.count(collection_name=service.collection_name).count
        if count == 0:
            logger.info("Database empty. Seeding medical data...")
            texts = [item[0] for item in MEDICAL_DATA]
            service.ingest(texts, source="System Init")
            logger.info("Seeding complete!")
    except Exception as e:
        logger.warning(f"Seeding failed: {e}")
