# alimentar_qdrant_2000.py
import os, random
from itertools import product
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"
MODEL_NAME = "intfloat/multilingual-e5-base"
VECTOR_SIZE = 768

random.seed(42)
os.makedirs(QDRANT_PATH, exist_ok=True)

print("🔧 A carregar modelo:", MODEL_NAME)
model = SentenceTransformer(MODEL_NAME)
client = QdrantClient(path=QDRANT_PATH)

# ⚠️ LIMPA E RECRIA
if COLLECTION_NAME in [c.name for c in client.get_collections().collections]:
    print(f"⚠️ Coleção '{COLLECTION_NAME}' existe. A apagar…")
    client.delete_collection(COLLECTION_NAME)

print("🆕 A criar coleção…")
client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
)

def pairs(intents, replies, contexto, augment_syns=None):
    """Gera pares (pergunta, resposta, contexto) com combinações e sinónimos simples."""
    res = []
    base = intents[:]
    if augment_syns:
        # cria variacoes simples substituindo termos
        for q in intents:
            for a, b in augment_syns:
                if a in q:
                    base.append(q.replace(a, b))
    for q in base:
        for r in replies:
            res.append((q, r, contexto))
    return res

# ---------- Temas e respostas ----------
nomes = ["Miguel", "Jojo", "Catarina", "Diogo", "Inês", "Barbeitos", "Raquel", "Gustavo"]

festa_local = pairs(
    intents=[
        "onde é a festa", "onde vai ser", "qual é o local", "morada da festa",
        "é no porto", "fica longe de gaia", "qual o sítio"
    ],
    replies=[
        "A festa é em Casa do Miguel, no Porto 🎆",
        "Casa do Miguel, Porto — o epicentro da diversão 😎",
        "No Porto, em casa do Miguel. Não tem como falhar! 🏠"
    ],
    contexto="festa",
    augment_syns=[("porto", "Porto"), ("sítio", "sitio")]
)

festa_hora = pairs(
    intents=[
        "a que horas começa", "quando começa a festa", "qual é a hora", "quando é"
    ],
    replies=[
        "Começa às 21h00 e vai até ao nascer do sol 🌅",
        "A partir das 21h00. Leva energia, vai ser longo! 💃🕺",
        "21h00 em ponto — o Diácono é pontual ⏰"
    ],
    contexto="festa"
)

comida_bebida = pairs(
    intents=[
        "vai haver comida", "há jantar", "o que vamos comer", "que bebidas há",
        "há cerveja", "vai haver vinho", "tem caipirinha", "há champanhe"
    ],
    replies=[
        "Vai haver comida e bebida em abundância 🍽️🥂",
        "Cerveja fria, vinho bom e caipirinhas — serviço completo 🍹",
        "Champanhe já está no gelo. Brinde garantido 🍾",
        "Há de tudo um pouco — confia no Diácono 😇"
    ],
    contexto="festa"
)

musica_dj = pairs(
    intents=[
        "vai haver musica", "vai haver música", "há dj", "quem é o dj", "vai dar para dançar",
        "vai ter karaoke", "posso pedir músicas"
    ],
    replies=[
        "DJ confirmado — o chão vai tremer 💃🕺",
        "Sim, e dá para pedidos (com moderação 😄) 🎧",
        "Karaoke depois da meia-noite… por tua conta e risco 🎤"
    ],
    contexto="musica",
    augment_syns=[("musica", "música")]
)

wifi = pairs(
    intents=[
        "qual é o wifi", "qual a senha do wifi", "qual a rede wi fi", "wi-fi", "senha da internet"
    ],
    replies=[
        "Wi-Fi: CasaDoMiguel2025 📶",
        "A senha do Wi-Fi é CasaDoMiguel2025 — usa com juízo 😉",
        "Rede: CasaDoMiguel2025. Palavra-passe: diversão 🎉"
    ],
    contexto="wifi"
)

dress = pairs(
    intents=[
        "qual é o dress code", "o que vestir", "que roupa devo levar", "há tema de roupa", "qual é a cor do ano"
    ],
    replies=[
        "Dress code: casual elegante ✨ e a cor é amarelo 💛",
        "Vem bonito e confortável; amarelo dá sorte 💛",
        "Brilha com amarelo — combina com o brinde 🎇"
    ],
    contexto="roupa"
)

logistica = pairs(
    intents=[
        "há estacionamento", "posso levar alguém", "dá para uber", "há metro perto", "é longe"
    ],
    replies=[
        "Há lugares nas ruas próximas e Uber funciona bem 🚗",
        "Podes levar companhia — quanto mais almas, melhor 🎉",
        "Metro e Uber são boas opções. O importante é chegar 😄"
    ],
    contexto="logistica"
)

piadas_geral = pairs(
    intents=[
        "conta uma piada", "faz-me rir", "diz uma anedota", "uma piada do diacono",
        "diz algo engraçado", "estás com humor"
    ],
    replies=[
        "Quer uma piada? O Porto ganhar ao Benfica 😂",
        "Dizem que o Diácono não dança… a pista discorda 🕺",
        "O meu médico receitou gargalhadas — dose diária ilimitada 😄"
    ],
    contexto="piadas"
)

futebol_benfica = pairs(
    intents=[
        "hoje joga o benfica", "o benfica vai ganhar", "quem é melhor benfica ou porto",
        "benfica é o maior", "o sporting tem hipótese", "quem vai ser campeão"
    ],
    replies=[
        "O Benfica, claro! O maior de Portugal 🔴⚪",
        "Benfica campeão — escreve o que te digo ✍️",
        "O Porto? Só o da cidade da festa, não o do campeonato 😏",
        "Sporting tenta, mas o Glorioso manda 💪"
    ],
    contexto="futebol"
)

ressaca = pairs(
    intents=[
        "e a ressaca amanhã", "amanhã trabalho", "cura para ressaca", "vou sofrer amanhã"
    ],
    replies=[
        "Hidratação, café e fé. O Diácono abençoa ☕🙏",
        "Dormir, pizza e arrependimento — ritual oficial 😅",
        "Água hoje, gratidão amanhã 💧"
    ],
    contexto="dia_seguinte"
)

tempo = pairs(
    intents=[
        "vai chover", "vai estar frio", "como vai estar o tempo", "vai estar calor", "previsão do tempo"
    ],
    replies=[
        "Nem chuva nem frio param esta festa 🎆",
        "Se estiver frio, a dança aquece 🔥",
        "O clima é de alegria — isso eu garanto 😎"
    ],
    contexto="tempo"
)

smalltalk = pairs(
    intents=[
        "vai ser fixe", "há surpresas", "o que vai acontecer", "tens novidades",
        "fala comigo", "responde", "estás aí", "podes ajudar"
    ],
    replies=[
        "Vai ser épico! Mesmo o Diácono vai dançar 🕺",
        "Há surpresas… mas se conto deixa de ser surpresa 😉",
        "Sempre aqui, pronto para animar a conversa 😄",
        "Claro que ajudo — dispara!"
    ],
    contexto="geral"
)

# juntar tudo e aumentar com nomes em respostas
datasets = [festa_local, festa_hora, comida_bebida, musica_dj, wifi, dress, logistica,
            piadas_geral, futebol_benfica, ressaca, tempo, smalltalk]

dados = []
for bloque in datasets:
    for q, r, ctx in bloque:
        if "{nome}" in r:
            r = r.format(nome=random.choice(nomes))
        dados.append((q, r, ctx))

# Aumentar volume com variações simples de pontuação e maiúsculas
def expand(q):
    opts = {q}
    opts.add(q.capitalize())
    opts.add(q + "?")
    opts.add(q + "!")
    return list(opts)

dados_expand = []
for q, r, ctx in dados:
    for qv in expand(q):
        dados_expand.append((qv, r, ctx))

# Limitar ~1200 pares para não exceder tempo
random.shuffle(dados_expand)
dados_final = dados_expand[:1200]
print(f"🧠 A preparar {len(dados_final)} pares para indexação…")

# Encode em batch
perguntas = [q for q, _, _ in dados_final]
vetores = model.encode(perguntas, batch_size=64, show_progress_bar=False).tolist()

# Upsert em chunks
points = []
for i, (q, r, ctx) in enumerate(dados_final):
    points.append(
        models.PointStruct(
            id=i + 1,
            vector=vetores[i],
            payload={"pergunta": q, "resposta": r, "contexto": ctx}
        )
    )
    if len(points) == 500:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        points = []

if points:
    client.upsert(collection_name=COLLECTION_NAME, points=points)

print(f"✅ Inseridos {len(dados_final)} pares na coleção '{COLLECTION_NAME}'.")
