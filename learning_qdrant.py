import os
import json
import random
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"

os.makedirs(QDRANT_PATH, exist_ok=True)

print("🔧 A inicializar modelo multilíngue (intfloat/multilingual-e5-base)…")
model = SentenceTransformer("intfloat/multilingual-e5-base")

# =====================================================
# Inicializar cliente Qdrant
# =====================================================
def inicializar_qdrant():
    try:
        client = QdrantClient(path=QDRANT_PATH)
    except RuntimeError:
        print("⚠️ Base Qdrant corrompida — recriando…")
        import shutil
        shutil.rmtree(QDRANT_PATH)
        os.makedirs(QDRANT_PATH, exist_ok=True)
        client = QdrantClient(path=QDRANT_PATH)

    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
        )
        print("✅ Nova coleção criada com sucesso!")
    return client

client = inicializar_qdrant()

# =====================================================
# Guardar mensagem
# =====================================================
def guardar_mensagem(nome, pergunta, resposta, contexto="geral"):
    try:
        vector = model.encode(pergunta).tolist()
        payload = {
            "user": nome,
            "pergunta": pergunta,
            "resposta": resposta,
            "contexto": contexto
        }
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=random.randint(0, 1_000_000_000),
                    vector=vector,
                    payload=payload
                )
            ]
        )
    except Exception as e:
        print(f"❌ Erro ao guardar mensagem no Qdrant: {e}")

# =====================================================
# Procurar resposta semelhante
# =====================================================
def procurar_resposta_semelhante(pergunta, limite_conf=0.75, top_k=5):
    try:
        vector = model.encode(pergunta).tolist()
        resultado = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=top_k
        )
        if not resultado:
            return None

        melhor = resultado[0]
        if melhor.score >= limite_conf:
            # Evita responder "olá" se não for saudação
            if melhor.payload.get("contexto") == "saudacao" and not any(
                p in pergunta for p in ["ola", "olá", "bom dia", "boa tarde", "boa noite", "boas"]
            ):
                return None
            return melhor.payload.get("resposta")
    except Exception as e:
        print(f"❌ Erro ao procurar no Qdrant: {e}")
    return None

# =====================================================
# Procurar com contexto
# =====================================================
def procurar_resposta_contextual(pergunta, historico):
    try:
        contexto = " ".join(historico[-5:])
        texto_completo = contexto + " " + pergunta
        vector = model.encode(texto_completo).tolist()
        resultado = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=5
        )
        if resultado and resultado[0].score > 0.6:
            return resultado[0].payload.get("resposta")
    except Exception as e:
        print(f"❌ Erro no contexto Qdrant: {e}")
    return None

# =====================================================
# Limpar coleção
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
