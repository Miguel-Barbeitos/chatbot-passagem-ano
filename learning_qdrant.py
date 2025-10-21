import os, json, random, time
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

# =====================================================
# ⚙️ Configuração do Qdrant e Modelo
# =====================================================
qdrant_path = "./qdrant_storage"
os.makedirs(qdrant_path, exist_ok=True)

client = QdrantClient(path=qdrant_path)
collection = "chat_memoria"

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Criar coleção se não existir
if collection not in [c.name for c in client.get_collections().collections]:
    client.recreate_collection(
        collection_name=collection,
        vectors_config=models.VectorParams(size=model.get_sentence_embedding_dimension(), distance=models.Distance.COSINE),
    )

# =====================================================
# 🧠 Guardar mensagem (com payload completo)
# =====================================================
def guardar_mensagem(nome, pergunta, resposta, perfil=None):
    vector = model.encode(pergunta).tolist()

    perfil_tipo = "desconhecido"
    if perfil:
        perfil_tipo = perfil.get("personalidade", "desconhecido")

    payload = {
        "user": nome,
        "pergunta": pergunta,
        "resposta": resposta,
        "timestamp": time.time(),
        "fonte": "chat",
        "contexto": {
            "evento": "Passagem de Ano 2025/2026",
            "local": "Casa do Miguel, Porto",
            "perfil": perfil_tipo
        }
    }

    client.upsert(
        collection_name=collection,
        points=[
            models.PointStruct(
                id=random.randint(1, 1_000_000_000),
                vector=vector,
                payload=payload
            )
        ]
    )

# =====================================================
# 🔍 Procurar resposta semelhante (nível 2 vetorial)
# =====================================================
def procurar_resposta_semelhante(pergunta, limite_conf=0.7, top_k=3):
    vector = model.encode(pergunta).tolist()

    results = client.search(
        collection_name=collection,
        query_vector=vector,
        limit=top_k
    )

    respostas = [hit.payload.get("resposta") for hit in results if hit.score >= limite_conf and hit.payload.get("resposta")]
    if not respostas:
        return None

    # Combinar respostas semelhantes de forma natural
    if len(respostas) == 1:
        return respostas[0]
    elif len(respostas) == 2:
        return f"{respostas[0]} Além disso, {respostas[1].lower()}"
    else:
        return f"{respostas[0]} Também {respostas[1].lower()} e {respostas[2].lower()}."
