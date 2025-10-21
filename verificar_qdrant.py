from qdrant_client import QdrantClient, models

QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"

# Inicializa cliente local
client = QdrantClient(path=QDRANT_PATH)

# Mostra número total de pontos
info = client.get_collection(COLLECTION_NAME)
print(f"📊 Vetores armazenados: {info.points_count}\n")

# Pesquisa apenas confirmações
resultados = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter=models.Filter(
        must=[models.FieldCondition(key="contexto", match=models.MatchValue(value="confirmacoes"))]
    ),
    limit=200,
)

print("✅ Confirmações encontradas:\n")
if not resultados[0]:
    print("⚠️ Nenhuma confirmação registada.")
else:
    for ponto in resultados[0]:
        payload = ponto.payload
        print(f"🧍 {payload.get('user')} → {payload.get('resposta')}")
