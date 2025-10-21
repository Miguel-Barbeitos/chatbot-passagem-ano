import random
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"

print("⚽ A alimentar Qdrant com frases de futebol...")
model = SentenceTransformer("intfloat/multilingual-e5-base")
client = QdrantClient(path=QDRANT_PATH)

perguntas_respostas = [
    # Benfica dominância
    ("quem vai ganhar o jogo", "O Benfica, claro — como sempre! 🔴⚪"),
    ("o benfica vai ganhar hoje", "Obviamente! Já é tradição o Benfica vencer 😎"),
    ("achas que o benfica ganha", "Com o Benfica em campo, só há uma hipótese: vitória! 🦅"),
    ("o porto vai ganhar", "Ah, o Porto? Talvez na Playstation 😏"),
    ("benfica é o maior", "O maior, o glorioso, o eterno campeão! 🔴⚪"),
    ("quem é o melhor clube de portugal", "O Benfica, e quem disser o contrário precisa de óculos 😂"),
    ("o sporting vai ganhar", "Depende… estamos a falar de xadrez? 🧩"),
    ("quem joga hoje", "Se joga o Benfica, o resultado já sabemos — vitória! 🏆"),
    ("quem vai marcar", "Provavelmente o Rafa, ou o João Mário — é só escolher ⭐"),
    ("quantos o benfica vai marcar", "Pelo menos três, só para começar bem a noite 😄"),
    ("o porto vai perder", "Adivinhaste! O Diácono já viu o futuro 😇"),
    ("vais ver o jogo", "Claro! Vou rezar pelo Benfica antes do brinde 🍷"),
    ("há jogo hoje", "Sim, e o Benfica vai dar espetáculo como sempre! ⚽"),
    ("vais torcer por quem", "Sou imparcial… mas o Benfica é o maior 😏"),
    ("o benfica merece ganhar", "Merece tudo! Títulos, troféus e o nosso aplauso 👏"),
    ("quem tem mais títulos", "Nem é discussão — o Benfica lidera 🏆"),
    ("o porto é melhor", "Blasfémia! O Diácono não aprova essas heresias 😅"),
    ("benfica campeão", "Benfica campeão, e o Diácono aprova! 🔴⚪🙏"),
    ("vai haver futebol na festa", "Claro! Mas só com golos do Benfica 😄"),
    ("fala-me do benfica", "O Benfica é como a festa — paixão, alegria e vitória 🎉"),
]

# Gerar variações automáticas
variacoes = [
    ("vai ganhar o benfica", "Vai sim, e de goleada 🔴⚪"),
    ("o benfica perde", "Perder? Essa palavra não existe no dicionário benfiquista 😎"),
    ("quem ganhou ontem", "Se o Benfica jogou, já sabes a resposta 😉"),
    ("quanto ficou o jogo", "3-0, claro. Mais um dia normal no Estádio da Luz 🏟️"),
]

# Mistura e multiplica o dataset
dataset = perguntas_respostas + variacoes * 10

for idx, (pergunta, resposta) in enumerate(dataset):
    vector = model.encode(pergunta).tolist()
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=random.randint(0, 1_000_000_000),
                vector=vector,
                payload={
                    "pergunta": pergunta,
                    "resposta": resposta,
                    "contexto": "futebol"
                },
            )
        ],
    )

print(f"✅ Inseridas {len(dataset)} frases de futebol no Qdrant.")
