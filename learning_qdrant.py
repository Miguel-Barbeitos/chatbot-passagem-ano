import os
import random
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import json

# =====================================================
# ⚙️ Inicialização do modelo e base vetorial
# =====================================================

# Modelo semântico (gratuito e leve)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Base Qdrant em memória (compatível com Streamlit Cloud)
client = QdrantClient(":memory:")

# Criação da coleção, se ainda não existir
if "mensagens" not in [c.name for c in client.get_collections().collections]:
    client.create_collection(
        collection_name="mensagens",
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
    )

# =====================================================
# 💾 Guardar mensagens
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
# 🔍 Pesquisa simples
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
# 🔍 Pesquisa com contexto
# =====================================================
def procurar_resposta_contextual(pergunta, historico, top_k=3):
    """
    Pesquisa no Qdrant com base no contexto da conversa.
    Junta o embedding da pergunta com o das últimas mensagens do utilizador.
    """
    if not pergunta.strip():
        return None

    vec_pergunta = model.encode(pergunta).tolist()

    if historico:
        texto_contexto = " ".join(historico[-5:])
        vec_historico = model.encode(texto_contexto).tolist()
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
# 🧠 Deteção de intenção
# =====================================================
def identificar_intencao(pergunta):
    """
    Classifica a intenção da pergunta (ex: música, comida, bebida, fogo, etc.)
    com base em embeddings e intenções pré-definidas.
    """
    if not os.path.exists("intencoes.json"):
        return None

    # Tenta ler com UTF-8 e fallback para Latin-1
    try:
        with open("intencoes.json", encoding="utf-8") as f:
            intencoes = json.load(f)
    except UnicodeDecodeError:
        with open("intencoes.json", encoding="latin-1") as f:
            intencoes = json.load(f)

    vec_pergunta = model.encode(pergunta).tolist()

    melhor_intencao = None
    melhor_score = 0.0

    # Calcula similaridade com cada exemplo
    for categoria, exemplos in intencoes.items():
        for exemplo in exemplos:
            vec_exemplo = model.encode(exemplo).tolist()
            dot = sum(a * b for a, b in zip(vec_pergunta, vec_exemplo))
            norm1 = sum(a * a for a in vec_pergunta) ** 0.5
            norm2 = sum(b * b for b in vec_exemplo) ** 0.5
            sim = dot / (norm1 * norm2)
            if sim > melhor_score:
                melhor_score = sim
                melhor_intencao = categoria

    if melhor_score > 0.60:
        return melhor_intencao
    return None

# =====================================================
# 🧹 Limpeza da base
# =====================================================
def limpar_mensagens():
    """Apaga todas as mensagens guardadas (reset)."""
    client.delete(collection_name="mensagens", points_selector=models.FilterSelector())
    print("🧹 Base de dados de mensagens limpa com sucesso!")
