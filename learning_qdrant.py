# learning_qdrant.py
import os, random, subprocess
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"
MODEL_NAME = "intfloat/multilingual-e5-base"
VECTOR_SIZE = 768
MIN_POINTS = 1500  # se a base estiver abaixo disto, re-alimenta

os.makedirs(QDRANT_PATH, exist_ok=True)
print(f"🔧 A carregar modelo: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

def alimentar_tudo():
    scripts = [
        "alimentar_qdrant_2000.py",      # limpa e recria
        "alimentar_qdrant_social.py",    # acrescenta
        "alimentar_qdrant_saudacoes.py"  # acrescenta
    ]
    for s in scripts:
        if os.path.exists(s):
            print(f"🚀 A executar {s} …")
            subprocess.run(["python", s], check=False)
        else:
            print(f"⚠️ Script {s} não encontrado.")

def inicializar_qdrant():
    client = QdrantClient(path=QDRANT_PATH)
    colnames = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in colnames:
        print("🆕 Coleção não existe. A criar e alimentar…")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
        )
        alimentar_tudo()
    else:
        info = client.get_collection(COLLECTION_NAME)
        size = getattr(info.config.params.vectors, "size", None)
        count = getattr(info, "points_count", 0)
        if size != VECTOR_SIZE or (count is not None and count < MIN_POINTS):
            print(f"⚠️ Coleção desatualizada (size={size}, points={count}). Recriando + alimentando…")
            client.delete_collection(COLLECTION_NAME)
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
            )
            alimentar_tudo()
        else:
            print(f"✅ Coleção ok (size={size}, points={count}).")
    return client

client = inicializar_qdrant()

def guardar_mensagem(nome, pergunta, resposta, contexto="geral"):
    try:
        vec = model.encode(pergunta).tolist()
        payload = {"user": nome, "pergunta": pergunta, "resposta": resposta, "contexto": contexto}
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[models.PointStruct(
                id=random.randint(1, 1_000_000_000),
                vector=vec,
                payload=payload
            )]
        )
    except Exception as e:
        print(f"❌ Erro ao guardar mensagem no Qdrant: {e}")

def procurar_resposta_semelhante(pergunta, limite_conf=0.6, top_k=5):
    try:
        vec = model.encode(pergunta).tolist()
        rs = client.search(collection_name=COLLECTION_NAME, query_vector=vec, limit=top_k)
        if rs and rs[0].score >= limite_conf:
            return rs[0].payload.get("resposta")
    except Exception as e:
        print(f"❌ Erro ao procurar no Qdrant: {e}")
    return None

def procurar_resposta_contextual(pergunta, historico):
    try:
        contexto = " ".join(historico[-5:])
        txt = (contexto + " " + pergunta).strip()
        vec = model.encode(txt).tolist()
        rs = client.search(collection_name=COLLECTION_NAME, query_vector=vec, limit=5)
        if rs and rs[0].score > 0.55:
            return rs[0].payload.get("resposta")
    except Exception as e:
        print(f"❌ Erro no contexto Qdrant: {e}")
    return None

def limpar_qdrant(confirmar=False):
    if not confirmar:
        print("⚠️ Confirma com limpar_qdrant(confirmar=True) para apagar tudo.")
        return
    try:
        client.delete_collection(COLLECTION_NAME)
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
        )
        alimentar_tudo()
        print("🧹 Coleção apagada e recarregada.")
    except Exception as e:
        print(f"Erro ao limpar Qdrant: {e}")
