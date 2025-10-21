import os
import json
import random
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

# =====================================================
# ⚙️ Configuração
# =====================================================
QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"

# Garante que o diretório Qdrant existe
os.makedirs(QDRANT_PATH, exist_ok=True)

# =====================================================
# 🧠 Modelo de embeddings (multilíngue)
# =====================================================
print("🔧 A inicializar modelo multilíngue…")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# =====================================================
# 💾 Inicializar cliente Qdrant
# =====================================================
def inicializar_qdrant():
    try:
        client = QdrantClient(path=QDRANT_PATH)
    except RuntimeError:
        # Base corrompida → recriar
        print("⚠️ Base Qdrant corrompida — recriando…")
        if os.path.exists(QDRANT_PATH):
            import shutil
            shutil.rmtree(QDRANT_PATH)
            os.makedirs(QDRANT_PATH, exist_ok=True)
        client = QdrantClient(path=QDRANT_PATH)

    # Garantir que a coleção existe
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
        )
    return client

client = inicializar_qdrant()

# =====================================================
# 💾 Guardar mensagem (pergunta + resposta)
# =====================================================
def guardar_mensagem(nome, pergunta, resposta, contexto="geral"):
    """Guarda interações com embeddings no Qdrant"""
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
# 🔍 Procurar respostas semelhantes (semânticas)
# =====================================================
def procurar_resposta_semelhante(pergunta, limite_conf=0.7, top_k=3):
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
            resposta = melhor.payload.get("resposta")
            return resposta
    except Exception as e:
        print(f"❌ Erro ao procurar no Qdrant: {e}")
    return None

# =====================================================
# 🔍 Procurar respostas com contexto do histórico
# =====================================================
def procurar_resposta_contextual(pergunta, historico):
    """Combina embeddings com contexto de histórico anterior"""
    try:
        contexto = " ".join(historico[-5:])  # últimas 5 interações
        texto_completo = contexto + " " + pergunta
        vector = model.encode(texto_completo).tolist()
        resultado = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=5
        )
        if resultado:
            melhor = resultado[0]
            if melhor.score > 0.6:
                return melhor.payload.get("resposta")
    except Exception as e:
        print(f"❌ Erro no contexto Qdrant: {e}")
    return None

# =====================================================
# 🧹 Função opcional para limpar a base
# =====================================================
def limpar_qdrant():
    """Apaga toda a coleção"""
    try:
        client.delete_collection(COLLECTION_NAME)
        print("🧹 Coleção Qdrant apagada.")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
        )
        print("✨ Nova coleção criada.")
    except Exception as e:
        print(f"Erro ao limpar Qdrant: {e}")
