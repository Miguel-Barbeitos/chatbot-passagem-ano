import os
import json
import random
import numpy as np
from sentence_transformers import SentenceTransformer, util
from qdrant_client import QdrantClient, models
import zipfile, tarfile, shutil

# =====================================================
# ⚙️ CONFIGURAÇÃO GERAL
# =====================================================
QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"

# --- Auto-extração da base Qdrant no arranque ---
if not os.path.exists(QDRANT_PATH):
    if os.path.exists("qdrant_data.zip"):
        print("📦 A extrair base Qdrant (zip)...")
        with zipfile.ZipFile("qdrant_data.zip", "r") as zip_ref:
            zip_ref.extractall()
    elif os.path.exists("qdrant_data.tar.gz"):
        print("📦 A extrair base Qdrant (tar.gz)...")
        with tarfile.open("qdrant_data.tar.gz", "r:gz") as tar:
            tar.extractall()

# =====================================================
# 🧠 MODELO DE EMBEDDINGS
# =====================================================
print("🔧 A inicializar modelo de embeddings multilíngue...")
model = SentenceTransformer("intfloat/multilingual-e5-base")

# =====================================================
# 💾 INICIALIZAÇÃO QDRANT
# =====================================================
def inicializar_qdrant():
    try:
        client = QdrantClient(path=QDRANT_PATH)
    except RuntimeError:
        print("⚠️ Base corrompida — recriando diretório...")
        shutil.rmtree(QDRANT_PATH, ignore_errors=True)
        os.makedirs(QDRANT_PATH, exist_ok=True)
        client = QdrantClient(path=QDRANT_PATH)

    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
        )
        print("✨ Nova coleção criada!")
    return client

client = inicializar_qdrant()

# =====================================================
# 🧭 DETEÇÃO DE INTENÇÃO SEMÂNTICA
# =====================================================
INTENCOES_BASE = {
    "saudacao": ["olá", "bom dia", "boa tarde", "boa noite", "como estás"],
    "festa": ["onde é a festa", "hora da festa", "quem vai", "vai haver música", "DJ", "vai ser no porto"],
    "comida": ["vai haver jantar", "o que vai haver para comer", "há sobremesas", "menu"],
    "bebida": ["vai haver cerveja", "há vinho", "cocktails", "shots", "champanhe"],
    "roupa": ["dress code", "o que vestir", "cor do ano", "amarelo"],
    "futebol": ["benfica", "porto", "sporting", "futebol", "jogo", "ganhar"],
    "piadas": ["conta uma piada", "faz-me rir", "piada", "anedota"],
    "confirmacoes": ["quem vai", "a jojo vai", "o miguel confirmou", "quantas pessoas vão"],
    "logistica": ["há estacionamento", "transporte", "como chegar", "longe", "uber"]
}
intencoes_embeds = {k: model.encode(v, convert_to_tensor=True) for k, v in INTENCOES_BASE.items()}

def identificar_intencao(pergunta):
    """Deteta a intenção mais próxima com embeddings"""
    pergunta_vec = model.encode(pergunta, convert_to_tensor=True)
    melhor_intencao, melhor_score = "geral", 0.4
    for k, embeds in intencoes_embeds.items():
        sim = util.cos_sim(pergunta_vec, embeds).mean().item()
        if sim > melhor_score:
            melhor_intencao, melhor_score = k, sim
    return melhor_intencao

# =====================================================
# 💾 GUARDAR MENSAGEM
# =====================================================
def guardar_mensagem(nome, pergunta, resposta, perfil, contexto="geral"):
    """Guarda a interação no Qdrant com identificação completa do utilizador."""
    try:
        # Garante que o nome é válido
        user_name = nome or perfil.get("nome", "Desconhecido")

        # Cria o vetor de embedding da pergunta
        vector = model.encode(pergunta).tolist()

        # Payload completo e coerente
        payload = {
            "user": user_name,
            "pergunta": pergunta,
            "resposta": resposta,
            "contexto": contexto,
            "perfil": perfil.get("tipo", "desconhecido"),
        }

        # Inserção na coleção
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=random.randint(0, 1_000_000_000),
                    vector=vector,
                    payload=payload,
                )
            ],
        )

        print(f"💾 Mensagem guardada para {user_name} ({contexto})")

    except Exception as e:
        print(f"❌ Erro ao guardar mensagem no Qdrant: {e}")


# =====================================================
# 🔍 PROCURA SEMÂNTICA COM CONTEXTO
# =====================================================
def procurar_resposta_semelhante(pergunta, intencao=None, limite_conf=0.6, top_k=3):
    """Procura a resposta mais relevante filtrada pela intenção (corrigido e mais permissivo)"""
    try:
        vector = model.encode(pergunta).tolist()
        filtro = None

        # 🔤 Normalizar a intenção (remover acentos e minúsculas)
        if intencao:
            intencao = intencao.lower().replace("ç", "c").replace("ã", "a").replace("á", "a").replace("é", "e")

        # Aplicar filtro de contexto apenas se existir intenção válida
        if intencao and intencao != "geral":
            filtro = models.Filter(
                must=[models.FieldCondition(key="contexto", match=models.MatchValue(value=intencao))]
            )

        resultado = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            query_filter=filtro,
            limit=top_k
        )

        if not resultado:
            return None

        melhor = resultado[0]
        if melhor.score >= limite_conf:
            return melhor.payload.get("resposta")

    except Exception as e:
        print(f"❌ Erro ao procurar resposta: {e}")
    return None


# =====================================================
# 🧹 LIMPAR COLEÇÃO
# =====================================================
def limpar_qdrant():
    try:
        client.delete_collection(COLLECTION_NAME)
        print("🧹 Coleção Qdrant apagada.")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
        )
        print("✨ Nova coleção criada.")
    except Exception as e:
        print(f"Erro ao limpar Qdrant: {e}")
