from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import random, os

model = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient(path="./qdrant_data")

qdrant.recreate_collection(
    collection_name="mensagens",
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
)

def guardar_mensagem(user, texto, resposta):
    embedding = model.encode(texto).tolist()
    qdrant.upsert(
        collection_name="mensagens",
        points=[models.PointStruct(id=random.randint(0, 1e9),
                                   vector=embedding,
                                   payload={"user": user, "texto": texto, "resposta": resposta})]
    )

def procurar_resposta_semelhante(texto, limiar=0.85):
    query = model.encode(texto).tolist()
    resultados = qdrant.search(collection_name="mensagens", query_vector=query, limit=1)
    if resultados and resultados[0].score >= limiar:
        return resultados[0].payload["resposta"]
    return None
