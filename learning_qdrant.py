import random
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

# Inicialização
client = QdrantClient(":memory:")  # usa base em memória (sem servidor externo)
collection_name = "chat_history"
model = SentenceTransformer("all-MiniLM-L6-v2")

# Cria a coleção se não existir
client.recreate_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
)

def guardar_mensagem(user, pergunta, resposta):
    """Guarda a pergunta e resposta no Qdrant com embedding."""
    try:
        # Gerar embedding (vector)
        vector = model.encode(pergunta).tolist()

        # Inserir ponto no Qdrant
        points = [
            models.PointStruct(
                id=random.randint(0, int(1e9)),
                vector=vector,
                payload={"user": user, "pergunta": pergunta, "resposta": resposta}
            )
        ]
        client.upsert(collection_name=collection_name, points=points)

    except Exception as e:
        print(f"[ERRO guardar_mensagem] {e}")

def procurar_resposta_semelhante(pergunta, limite=0.8):
    """Procura respostas semelhantes no Qdrant."""
    try:
        vector = model.encode(pergunta).tolist()
        resultados = client.search(collection_name=collection_name, query_vector=vector, limit=1)
        if resultados and resultados[0].score >= limite:
            return resultados[0].payload["resposta"]
    except Exception as e:
        print(f"[ERRO procurar_resposta_semelhante] {e}")
    return None
