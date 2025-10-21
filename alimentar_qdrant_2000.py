import random
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

# =====================================================
# ⚙️ Configuração
# =====================================================
QDRANT_PATH = "qdrant_data"
COLLECTION_NAME = "chatbot_passagem_ano"
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

print("🎉 A alimentar o Qdrant com sabedoria do Diácono Remédios...")

client = QdrantClient(path=QDRANT_PATH)

# Garante que a coleção existe
collections = [c.name for c in client.get_collections().collections]
if COLLECTION_NAME not in collections:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
    )

# =====================================================
# 🎭 Base de temas
# =====================================================
temas = {
    "saudacao": [
        "olá", "boa noite", "como estás", "tudo bem", "hey", "oi", "bom dia", "boas"
    ],
    "festa": [
        "onde é a festa", "a que horas começa", "quem vai", "vai haver comida", "vai haver música",
        "vai haver dj", "posso levar alguém", "há estacionamento", "qual é o tema da festa"
    ],
    "benfica": [
        "quem vai ganhar o campeonato", "o benfica vai ganhar", "o porto tem hipótese",
        "o sporting está forte", "quem é o maior clube de portugal", "o benfica vai ser campeão",
        "achas que o benfica ganha hoje", "o benfica é o melhor"
    ],
    "bebidas": [
        "há cerveja", "vai haver vinho", "tem caipirinha", "que bebidas há", "posso levar gin",
        "há champanhe", "há água com gás"
    ],
    "piadas": [
        "conta uma piada", "faz-me rir", "diz uma anedota", "conta uma história engraçada",
        "tens sentido de humor", "és divertido"
    ],
    "roupa": [
        "o que devo vestir", "qual é o dress code", "tenho de levar amarelo", "há tema de roupa"
    ],
}

# =====================================================
# 💬 Possíveis respostas
# =====================================================
respostas_por_tema = {
    "saudacao": [
        "Bem-vindo, {nome}! 🎉 Está quase na hora do brinde!",
        "Olá {nome}! O Diácono Remédios ao seu dispor 🙏✨",
        "Boas, {nome}! Preparado para dançar até cair? 💃🕺",
        "Ora viva, {nome}! 😄 Que alegria vê-lo pronto para a festa!",
        "Bom ver-te, {nome}! Já cheira a champanhe e alegria 🍾",
    ],
    "festa": [
        "A festa vai ser em Casa do Miguel, no Porto — imperdível! 🎆",
        "Começa às 21h00, mas a animação dura até ao nascer do sol 🌅",
        "Vai haver comida, música e boa disposição — o Diácono garante!",
        "DJ confirmado, {nome}! Prepara-te para dançar 💃🕺",
        "Sim, podes levar companhia — quanto mais almas, melhor a festa 😄",
    ],
    "benfica": [
        "O Benfica, claro! O maior de Portugal 🔴⚪",
        "O Porto? Só o da cidade da festa, não o do campeonato 😏",
        "O Sporting até tenta, mas o Benfica é quem manda! 💪",
        "Benfica campeão — escreve o que o Diácono te diz ✍️",
        "Se o Benfica jogar, é vitória certa. É lei divina 😇",
        "O maior de Portugal, o Glorioso! 🔴⚪",
        "O Porto pode tentar, mas vai ver a festa pela televisão 📺😂"
    ],
    "bebidas": [
        "Há cerveja, vinho e até caipirinhas — é melhor que um bar! 🍹",
        "Claro que há cerveja, {nome}! Está mais fria que o coração do árbitro 😜",
        "O champanhe já está no gelo 🍾",
        "Há gin, vinho e boa disposição — o essencial! 🍸",
        "Tens de provar o ponche do Diácono… cura até ressacas 😇",
    ],
    "piadas": [
        "Sabes qual é o cúmulo do Diácono? Casar os outros e ficar solteiro 😂",
        "Dizem que o Diácono Remédios não bebe… mas a garrafa discorda 🍾",
        "Fui ao médico… ele disse que eu estava com excesso de alegria 😄",
        "Sabes por que o Benfica é santo? Porque faz milagres todos os domingos 😇",
        "Quer uma piada? O Porto ganhar ao Benfica 😂",
    ],
    "roupa": [
        "O dress code é elegante, mas a cor do ano é amarelo 💛",
        "Brilha muito, {nome}! Amarelo é a cor da sorte ✨",
        "Roupa leve, coração quente e sorriso aberto 😄",
        "O Diácono recomenda: amarelo e um copo na mão 🍸",
        "Casual elegante, mas com brilho — como o Benfica em campo 😎",
    ]
}

# =====================================================
# 🧠 Alimentar Qdrant
# =====================================================
def adicionar_pergunta_resposta(pergunta, resposta, contexto):
    vector = model.encode(pergunta).tolist()
    payload = {
        "pergunta": pergunta,
        "resposta": resposta,
        "contexto": contexto
    }
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[models.PointStruct(id=random.randint(0, 1_000_000_000), vector=vector, payload=payload)]
    )

total = 0
for contexto, perguntas in tqdm(temas.items(), desc="A alimentar o Qdrant..."):
    respostas = respostas_por_tema[contexto]
    for pergunta in perguntas:
        for _ in range(40):  # 40 variações por tema = ~2000 frases
            nome = random.choice(["Miguel", "Jojo", "Catarina", "Diogo", "Inês", "Barbeitos"])
            resposta = random.choice(respostas).format(nome=nome)
            adicionar_pergunta_resposta(pergunta, resposta, contexto)
            total += 1

print(f"✅ Alimentação concluída com {total} entradas!")
print("💾 O Diácono Remédios está cheio de sabedoria e pronto para a festa 🎉")
