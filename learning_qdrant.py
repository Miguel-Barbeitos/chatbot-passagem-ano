import os, random
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

# =====================================================
# ⚙️ Configuração inicial do modelo e base vetorial
# =====================================================

# Modelo leve e gratuito da Hugging Face
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Cria ou liga à base local do Qdrant
qdrant_path = "./data/qdrant_db"
os.makedirs(qdrant_path, exist_ok=True)
client = QdrantClient(path=qdrant_path)

# =====================================================
# 🧩 Criação da coleção se ainda não existir
# =====================================================
if "mensagens" not in [c.name for c in client.get_collections().collections]:
    client.create_collection(
        collection_name="mensagens",
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
    )

# =====================================================
# 💾 Guardar mensagem (pergunta + resposta)
# =====================================================
def guardar_mensagem(nome, pergunta, resposta):
    """Guarda a pergunta e resposta do utilizador no Qdrant."""
    if not pergunta.strip():
        return
    vector = model.encode(pergunta).tolist()

    client.upsert(
        collection_name="mensagens",
        points=[
            models.PointStruct(
                id=random.randint(1, 1_000_000_000),
                vector=vector,
                payload={"nome": nome, "pergunta": pergunta, "resposta": resposta}
            )
        ]
    )

# =====================================================
# 🔍 Pesquisa semântica simples
# =====================================================
def procurar_resposta_semelhante(pergunta, top_k=3):
    """Pesquisa uma resposta semelhante no Qdrant."""
    if not pergunta.strip():
        return None
    vector = model.encode(pergunta).tolist()

    res = client.search(
        collection_name="mensagens",
        query_vector=vector,
        limit=top_k
    )

    if not res:
        return None

    melhor = res[0]
    if melhor.score < 0.65:
        return None

    return melhor.payload.get("resposta", None)

# =====================================================
# 🔍 Pesquisa semântica com contexto
# =====================================================
def procurar_resposta_contextual(pergunta, historico, top_k=3):
    """
    Pesquisa no Qdrant tendo em conta o contexto da conversa.
    Junta o embedding da pergunta com o das últimas mensagens do utilizador.
    """
    if not pergunta.strip():
        return None

    vec_pergunta = model.encode(pergunta).tolist()

    # Se houver histórico, cria embedding médio do contexto
    if historico:
        texto_contexto = " ".join(historico[-5:])  # últimas 5 mensagens
        vec_historico = model.encode(texto_contexto).tolist()
        # Combinação simples: média dos vetores
        vec_contexto = [(a + b) / 2 for a, b in zip(vec_pergunta, vec_historico)]
    else:
        vec_contexto = vec_pergunta

    res = client.search(
        collection_name="mensagens",
        query_vector=vec_contexto,
        limit=top_k
    )

    if not res:
        return None

    melhor = res[0]
    if melhor.score < 0.65:
        return None

    return melhor.payload.get("resposta", None)

# =====================================================
# 🧹 Limpeza e gestão
# =====================================================
def limpar_mensagens():
    """Apaga todas as mensagens guardadas (reset da base)."""
    client.delete(collection_name="mensagens", points_selector=models.FilterSelector())
    print("🧹 Base de dados de mensagens limpa com sucesso!")
