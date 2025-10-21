# alimentar_qdrant_social.py
import os, random
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"
MODEL_NAME = "intfloat/multilingual-e5-base"
VECTOR_SIZE = 768

random.seed(7)
os.makedirs(QDRANT_PATH, exist_ok=True)
model = SentenceTransformer(MODEL_NAME)
client = QdrantClient(path=QDRANT_PATH)

def gen_pairs(intents, replies, contexto):
    res = []
    for q in intents:
        qvars = {q, q.capitalize(), q + "?", q + "!", q.replace("  ", " ")}
        for qv in qvars:
            for r in replies:
                res.append((qv, r, contexto))
    return res

nomes = ["Miguel", "Jojo", "Catarina", "Diogo", "Inês", "Barbeitos", "Raquel", "Gustavo"]

confirmacoes = gen_pairs(
    intents=[
        "quem vai", "quem confirmou", "quem falta confirmar", "já há muita gente confirmada",
        "a Inês vai", "o Diogo vem", "o Miguel vai", "a Jojo confirmou", "o Jorge confirmou"
    ],
    replies=[
        "Até agora a lista está forte! Não faltes, {nome} 🎉",
        "Inês e Diogo confirmados; a Jojo disse que leva glitter ✨",
        "O Miguel é o anfitrião — esse não falha 🏠",
        "Faltam alguns confirmar, mas vai ficar cheio 😄"
    ],
    contexto="confirmacoes"
)

levar_coisas = gen_pairs(
    intents=[
        "o que devo levar", "preciso levar algo", "levo sobremesa", "levo bebida", "posso levar alguém",
        "posso levar jogo", "querem que leve gelo", "levo copos"
    ],
    replies=[
        "Traz o teu melhor espírito e, se quiseres, sobremesa 😄",
        "Gelo e copos são sempre bem-vindos 🧊🥤",
        "Podes levar alguém — quanto mais, melhor 🎉",
        "Se trouxeres um jogo, a casa agradece 😎"
    ],
    contexto="logistica"
)

interacao_amigos = gen_pairs(
    intents=[
        "o Diogo já chegou", "a Inês está a caminho", "a Catarina vai se atrasar", "o Jorge vem com filhos",
        "a Raquel vem", "o Gustavo confirmou", "o Barbeitos vai"
    ],
    replies=[
        "Estão a caminho — a animação já começou no grupo 🤳",
        "Alguns chegam mais tarde, mas vão todos aparecer 😉",
        "Sim, confirmaram — e com boa disposição!"
    ],
    contexto="social"
)

elogios_troca = gen_pairs(
    intents=[
        "estás impecável", "gosto do teu estilo", "curto o teu humor", "gosto do diacono",
        "és top", "és o maior", "és divertido"
    ],
    replies=[
        "O Diácono agradece e retribui com confetes 🎊",
        "És tu que brilhas, {nome}! 💫",
        "A missão é espalhar boa energia — cumprida 😄"
    ],
    contexto="elogios"
)

pos_festa = gen_pairs(
    intents=[
        "mandas fotos depois", "partilhas as fotos", "vai haver álbum",
        "manda localização", "envias a morada"
    ],
    replies=[
        "Claro! Depois partilhamos o álbum no grupo 📸",
        "A morada é Casa do Miguel, Porto — simples e direto 🏠",
        "Localização segue no grupo antes da hora 📍"
    ],
    contexto="pos_festa"
)

# Agregar e personalizar
dados = []
for bloco in [confirmacoes, levar_coisas, interacao_amigos, elogios_troca, pos_festa]:
    for q, r, ctx in bloco:
        if "{nome}" in r:
            r = r.format(nome=random.choice(nomes))
        dados.append((q, r, ctx))

random.shuffle(dados)
dados = dados[:700]

perguntas = [q for q, _, _ in dados]
vecs = model.encode(perguntas, batch_size=64, show_progress_bar=False).tolist()

points, start_id = [], 10_000
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

print(f"✅ Inseridos {len(dados)} pares sociais na coleção.")
