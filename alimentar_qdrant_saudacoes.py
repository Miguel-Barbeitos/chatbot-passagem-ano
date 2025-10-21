# alimentar_qdrant_saudacoes.py
import os, random
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"
MODEL_NAME = "intfloat/multilingual-e5-base"
VECTOR_SIZE = 768

random.seed(21)
os.makedirs(QDRANT_PATH, exist_ok=True)
model = SentenceTransformer(MODEL_NAME)
client = QdrantClient(path=QDRANT_PATH)

saudacoes_base = [
    "olá", "ola", "boas", "bom dia", "boa tarde", "boa noite",
    "como estás", "tudo bem", "que tal", "hey", "oi", "estás por aí",
    "saudações", "então", "olá a todos", "olá pessoal"
]

respostas = [
    "Olá, {nome}! 👋 Pronto para começar a festa?",
    "Boas, {nome}! 😄 Já a pensar na noite de ano?",
    "O Diácono Remédios ao seu dispor 🙏✨",
    "Bem-vindo, {nome}! 🎉 Está quase na hora do brinde!",
    "Que alegria ver-te, {nome}! 💫"
]

nomes = ["Miguel", "Jojo", "Catarina", "Diogo", "Inês", "Barbeitos", "Raquel", "Gustavo"]

def expand(q):
    return list({q, q.capitalize(), q + "?", q + "!", q.replace("  ", " ")})

dados = []
for q in saudacoes_base:
    for qv in expand(q):
        for r in respostas:
            dados.append((qv, r.format(nome=random.choice(nomes)), "saudacao"))

random.shuffle(dados)
dados = dados[:400]

perguntas = [q for q, _, _ in dados]
vecs = model.encode(perguntas, batch_size=64, show_progress_bar=False).tolist()

points, start_id = [], 50_000
for i, (q, r, ctx) in enumerate(dados):
    points.append(
        models.PointStruct(
            id=start_id + i,
            vector=vecs[i],
            payload={"pergunta": q, "resposta": r, "contexto": ctx}
        )
    )
    if len(points) == 500:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        points = []
if points:
    client.upsert(collection_name=COLLECTION_NAME, points=points)

print(f"✅ Inseridas {len(dados)} saudações na coleção.")
