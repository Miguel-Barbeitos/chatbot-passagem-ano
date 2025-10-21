from qdrant_client import QdrantClient

# =====================================================
# ⚙️ Configuração
# =====================================================
QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"

# =====================================================
# 🔍 Conectar ao Qdrant local
# =====================================================
client = QdrantClient(path=QDRANT_PATH)

# =====================================================
# 📦 Verificar coleção
# =====================================================
try:
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        print(f"❌ A coleção '{COLLECTION_NAME}' não existe.")
    else:
        print(f"✅ Coleção '{COLLECTION_NAME}' encontrada!")
except Exception as e:
    print(f"Erro ao aceder ao Qdrant: {e}")
    exit()

# =====================================================
# 📊 Estatísticas básicas
# =====================================================
try:
    info = client.get_collection(COLLECTION_NAME)
    print(f"📊 Vectores armazenados: {info.points_count}")
    # O campo 'distance' foi removido nas versões recentes do Qdrant
except Exception as e:
    print(f"Erro ao obter info: {e}")

# =====================================================
# 🔎 Amostra de dados
# =====================================================
print("\n🔍 Amostras aleatórias de perguntas/respostas guardadas:")
try:
    resultados = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=5,
        with_payload=True
    )

    for ponto in resultados[0]:
        payload = ponto.payload
        pergunta = payload.get("pergunta", "—")
        resposta = payload.get("resposta", "—")
        contexto = payload.get("contexto", "—")
        print(f"\n🗨️ Pergunta: {pergunta}\n💬 Resposta: {resposta}\n🎭 Contexto: {contexto}")
except Exception as e:
    print(f"Erro ao listar amostras: {e}")
