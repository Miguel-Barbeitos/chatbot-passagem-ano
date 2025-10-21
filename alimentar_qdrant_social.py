import json
import random
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

# =====================================================
# ⚙️ CONFIGURAÇÃO
# =====================================================
QDRANT_PATH = "qdrant_db"
COLLECTION_NAME = "chatbot_passagem_ano"

print("🔧 A inicializar modelo multilíngue…")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
client = QdrantClient(path=QDRANT_PATH)

# =====================================================
# 🧹 LIMPAR COLEÇÃO (se já existir)
# =====================================================
if COLLECTION_NAME in [c.name for c in client.get_collections().collections]:
    print(f"⚠️ Coleção '{COLLECTION_NAME}' já existe. A apagar antes de recarregar…")
    client.delete_collection(collection_name=COLLECTION_NAME)

client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
)
print("✅ Nova coleção criada com sucesso!\n")

# =====================================================
# 🗣️ FRASES / CONTEXTOS
# =====================================================

def gerar_variacoes(base, respostas, contexto):
    """Cria pequenas variações de perguntas/respostas."""
    pares = []
    for pergunta in base:
        for resposta in respostas:
            pares.append((pergunta, resposta, contexto))
    return pares


# --- SAUDAÇÕES ---
saudacoes = gerar_variacoes(
    [
        "olá", "ola", "bom dia", "boa tarde", "boa noite",
        "como estás", "tudo bem", "como vai isso", "que tal", "e aí"
    ],
    [
        "Olá, {nome}! Pronto para a festa? 🎉",
        "Bom ver-te, {nome}! Já cheira a champanhe 🍾",
        "Tudo ótimo por aqui — e contigo? 😄",
        "O Diácono Remédios ao seu dispor 🙏✨",
        "Que alegria ver-te por aqui, {nome}! 💫"
    ],
    "saudacao"
)

# --- FESTA ---
festa = gerar_variacoes(
    [
        "onde é a festa", "qual é o local", "onde vai ser", "fica longe", "qual é o sitio",
        "vai haver comida", "há jantar", "vai haver música", "quem vai tocar", "há DJ",
        "a que horas começa", "quando começa", "quando é a festa"
    ],
    [
        "A festa vai ser em Casa do Miguel, no Porto 🎆",
        "DJ confirmado — o chão vai tremer 💃🕺",
        "Começa às 21h00 e promete durar até ao nascer do sol 🌅",
        "Vai haver comida e bebida em abundância 🍽️🥂",
        "Casa do Miguel, Porto — o palco da diversão 😎"
    ],
    "festa"
)

# --- CONFIRMAÇÕES / AMIGOS ---
confirmacoes = gerar_variacoes(
    [
        "quem vai", "quem confirmou", "a Inês vai", "o Diogo vem", "o Miguel vai",
        "a Jojo confirmou", "o Pedro vai", "quem não vai", "quem falta confirmar"
    ],
    [
        "Toda a gente boa vai! E tu, {nome}, não podes faltar 🎉",
        "A Inês confirmou e já escolheu o vestido 💃",
        "O Diogo disse que só vai se houver sobremesa 😏",
        "O anfitrião Miguel nunca falha 🏠🥳",
        "A Jojo disse que leva glitter e boa energia ✨"
    ],
    "confirmacoes"
)

# --- WIFI ---
wifi = gerar_variacoes(
    [
        "qual é o wifi", "qual é a senha", "qual é a rede", "wifi", "wi fi", "wi-fi"
    ],
    [
        "A senha do Wi-Fi é CasaDoMiguel2025 📶",
        "Wi-Fi: CasaDoMiguel2025 — não vale ver TikToks durante o brinde 😄",
        "Rede: CasaDoMiguel2025, palavra-passe: diversão 🎉"
    ],
    "wifi"
)

# --- ROUPA ---
roupa = gerar_variacoes(
    [
        "qual é o dress code", "que roupa devo levar", "como devo ir vestido",
        "há tema", "cor da roupa", "o que vestir"
    ],
    [
        "Dress code: casual elegante ✨ e a cor deste ano é amarelo 💛",
        "Amarelo é a cor da sorte — e do estilo! 💃",
        "Veste-te bem, mas com espaço para dançar! 😎"
    ],
    "roupa"
)

# --- PIADAS / HUMOR ---
piadas = gerar_variacoes(
    [
        "faz-me rir", "conta uma piada", "diz algo engraçado", "faz uma piada", "ri-te comigo",
        "piada sobre futebol", "piada do benfica", "piada do porto", "piada do sporting"
    ],
    [
        "Quer uma piada? O Porto ganhar ao Benfica 😂",
        "O Benfica é o maior de Portugal — o resto é paisagem 🔴⚪",
        "Sabes qual é o clube mais feliz? O que tem o Diácono como adepto 😎",
        "Dizem que o Porto vai ganhar... mas é só nas piadas! 😜",
        "O Sporting ainda está a contar os anos sem ganhar 🤭"
    ],
    "piadas"
)

# --- RESSACA / DIA SEGUINTE ---
ressaca = gerar_variacoes(
    [
        "como vai ser amanhã", "e a ressaca", "amanhã trabalho", "vai haver cura", "vou ter ressaca"
    ],
    [
        "O Diácono abençoa-te com hidratação e café ☕🙏",
        "Amanhã? Dormir, pizza e arrependimento — tradição 😅",
        "Reza três vezes e bebe água, é o ritual sagrado pós-festa 💧😂"
    ],
    "ressaca"
)

# --- TEMPO / CLIMA ---
tempo = gerar_variacoes(
    [
        "vai chover", "como vai estar o tempo", "vai estar frio", "vai estar calor", "clima"
    ],
    [
        "Nem chuva nem frio param esta festa 🎆",
        "Vai estar quente — ou sou eu que já estou animado? 🔥",
        "Mesmo que chova, o Diácono garante alegria ☔💃"
    ],
    "tempo"
)

# --- GERAL ---
geral = gerar_variacoes(
    [
        "vai ser fixe", "vai ser bom", "há surpresas", "o que vai acontecer", "vai ser divertido",
        "o que sabes", "tens novidades", "fala comigo", "responde", "estás aí"
    ],
    [
        "Vai ser épico! Mesmo o Diácono vai dançar 🕺",
        "Só posso dizer que vai haver surpresas 😉",
        "Mistério e diversão — combinação explosiva 🎉",
        "Estou aqui, pronto para animar esta conversa 😄"
    ],
    "geral"
)

# =====================================================
# 📦 INSERIR NO QDRANT
# =====================================================

dados = saudacoes + festa + confirmacoes + wifi + roupa + piadas + ressaca + tempo + geral
random.shuffle(dados)

vetores = model.encode([p for p, _, _ in dados]).tolist()

points = []
for i, (pergunta, resposta, contexto) in enumerate(dados):
    points.append(
        models.PointStruct(
            id=i + 1,
            vector=vetores[i],
            payload={"pergunta": pergunta, "resposta": resposta, "contexto": contexto},
        )
    )

client.upsert(collection_name=COLLECTION_NAME, points=points)

print(f"✅ Inseridas {len(points)} frases com sucesso no Qdrant!\n")

# =====================================================
# 🔍 AMOSTRA ALEATÓRIA
# =====================================================
for i in random.sample(range(len(points)), 10):
    p = dados[i]
    print(f"🗨️ {p[0]}  →  💬 {p[1]}  [{p[2]}]")

print("\n🎉 Base vetorial expandida com sucesso — Diácono Remédios pronto para tudo!")
