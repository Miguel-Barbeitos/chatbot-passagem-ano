import os
import random
import time
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

# =====================================================
# ⚙️ Configuração
# =====================================================
QDRANT_PATH = "./qdrant_storage"
COLLECTION = "chat_memoria"

os.makedirs(QDRANT_PATH, exist_ok=True)

# Modelo multilíngue otimizado para português e humor
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Cliente Qdrant (local)
client = QdrantClient(path=QDRANT_PATH)

# Garante que a coleção existe
if COLLECTION not in [c.name for c in client.get_collections().collections]:
    print("🧠 A coleção não existe, a criar nova...")
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=model.get_sentence_embedding_dimension(),
            distance=models.Distance.COSINE,
        ),
    )
else:
    print("✅ Coleção existente carregada.")

# =====================================================
# 💾 Guardar mensagens
# =====================================================
def guardar_mensagem(user: str, pergunta: str, resposta: str, tema: str = "geral"):
    """Guarda uma nova mensagem no Qdrant com embeddings."""
    try:
        vector = model.encode(pergunta).tolist()
        payload = {
            "user": user,
            "pergunta": pergunta,
            "resposta": resposta,
            "timestamp": time.time(),
            "tema": tema,
            "fonte": "interacao",
        }
        ponto = models.PointStruct(
            id=random.randint(1, 1_000_000_000),
            vector=vector,
            payload=payload,
        )
        client.upsert(collection_name=COLLECTION, points=[ponto])
    except Exception as e:
        print(f"⚠️ Erro ao guardar mensagem: {e}")

# =====================================================
# 🔍 Procurar respostas semelhantes
# =====================================================
def procurar_resposta_semelhante(pergunta: str, limite_conf: float = 0.7, top_k: int = 3):
    """Procura respostas semelhantes no Qdrant com base semântica."""
    try:
        vector = model.encode(pergunta).tolist()

        resultados = client.search(
            collection_name=COLLECTION,
            query_vector=vector,
            limit=top_k,
        )

        if not resultados:
            return None

        melhor = resultados[0]
        score = melhor.score
        if score < limite_conf:
            return None

        resposta = melhor.payload.get("resposta")
        tema = melhor.payload.get("contexto", {}).get("tema") if "contexto" in melhor.payload else None
        return resposta or None

    except Exception as e:
        print(f"⚠️ Erro ao procurar resposta semelhante: {e}")
        return None

# =====================================================
# 🧩 Procurar resposta contextual
# =====================================================
def procurar_resposta_contextual(pergunta: str, historico_user: list, limite_conf: float = 0.65):
    """Procura respostas semelhantes tendo em conta o histórico do utilizador."""
    try:
        contexto = " ".join(historico_user[-3:]) if historico_user else ""
        entrada = f"{contexto} {pergunta}"
        vector = model.encode(entrada).tolist()

        resultados = client.search(
            collection_name=COLLECTION,
            query_vector=vector,
            limit=5,
        )

        if not resultados:
            return None

        for r in resultados:
            if r.score >= limite_conf:
                return r.payload.get("resposta")

        return None

    except Exception as e:
        print(f"⚠️ Erro ao procurar resposta contextual: {e}")
        return None

# =====================================================
# 🧭 Identificar intenção (com base no dataset)
# =====================================================
def identificar_intencao(pergunta: str):
    """Verifica se a pergunta tem intenção reconhecida no dataset base."""
    try:
        vector = model.encode(pergunta).tolist()
        resultados = client.search(
            collection_name=COLLECTION,
            query_vector=vector,
            limit=3,
        )

        if not resultados:
            return None

        melhor = resultados[0]
        if melhor.score > 0.75:
            tema = (
                melhor.payload.get("contexto", {}).get("tema")
                if "contexto" in melhor.payload
                else None
            )
            return tema
        return None

    except Exception as e:
        print(f"⚠️ Erro ao identificar intenção: {e}")
        return None

# =====================================================
# 🧹 Função de limpeza (opcional)
# =====================================================
def limpar_qdrant():
    """Limpa toda a coleção (usar com cuidado)."""
    try:
        client.delete_collection(collection_name=COLLECTION)
        print("🧹 Coleção apagada com sucesso.")
    except Exception as e:
        print(f"⚠️ Erro ao apagar coleção: {e}")
