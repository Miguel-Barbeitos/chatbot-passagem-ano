import os
import random
import time
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

# =====================================================
# ⚙️ Configuração
# =====================================================
QDRANT_PATH = "./qdrant_storage"
COLLECTION = "chat_memoria"

os.makedirs(QDRANT_PATH, exist_ok=True)

# Modelo multilíngue (excelente para PT)
print("🔧 A inicializar modelo multilíngue…")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Cliente Qdrant
client = QdrantClient(path=QDRANT_PATH)

# Criar coleção (se não existir)
if COLLECTION not in [c.name for c in client.get_collections().collections]:
    print("🧠 A criar coleção 'chat_memoria'...")
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=model.get_sentence_embedding_dimension(),
            distance=models.Distance.COSINE,
        ),
    )
else:
    print("✅ Coleção existente carregada.")

# =====================================================
# 🎉 Lista de 50 saudações variadas
# =====================================================
saudacoes = [
    "Olá, seja muito bem-vindo!",
    "Boa noite, é um prazer vê-lo por aqui.",
    "Bom dia! Espero que esteja tudo ótimo.",
    "Boa tarde, pronto para celebrar?",
    "Que bom revê-lo! Preparado para o evento?",
    "Saudações cordiais, espero que traga boas vibrações.",
    "Seja bem-vindo à festa mais aguardada do ano.",
    "É um prazer recebê-lo nesta celebração especial.",
    "Muito boa noite, espero que esteja confortável.",
    "Cumprimentos! Que a sua noite comece com alegria.",
    "Boas, tudo em cima? 😎",
    "Eia, já chegaste! Bora lá!",
    "Olá! Finalmente alguém com estilo 😏",
    "Hey! Tudo tranquilo por aí?",
    "Que bom ver-te por aqui, pronto para o brinde? 🍾",
    "Yo! Preparado para virar o ano com classe?",
    "Boas! Bora começar a festa?",
    "Opa! Já cheira a festa no ar 🎉",
    "Olá, campeão! Vieste cedo desta vez!",
    "Ei! Que bom ter-te por aqui 😁",
    "Olá, alma festiva! Trouxeste o teu melhor sorriso? 😁",
    "Bem-vindo! O Diácono Remédios aprova a tua presença 🙏",
    "Olá, pronto para dançar até cair ou vais ficar no sofá?",
    "Chegou quem faltava! Já podemos começar 🎊",
    "Olá! Espero que tenhas trazido boa disposição e um carregador de telemóvel 🔋",
    "Boas! Trouxeste o champanhe ou só a vontade? 🍾",
    "Olá, olha quem apareceu! Pensei que tinhas ficado no trânsito 🚗",
    "Bem-vindo, estrela da noite! 🌟",
    "Olá! Já escolheste a tua música para dançar mal? 💃",
    "Boas! Cuidado que o Diácono anda a avaliar os brindes 😇",
    "Olá e feliz quase Ano Novo! 🎆",
    "Boas! Está na hora de preparar o brinde 🍾",
    "Olá! 2026 vai ser o teu ano, acredita! 💪",
    "Bem-vindo à contagem decrescente mais animada do país 🎇",
    "Boas festas e que venham as boas energias! ✨",
    "Olá! O Diácono Remédios já está a aquecer as cordas vocais 🎤",
    "Feliz quase-ano-novo! 😄 Preparado para o brinde?",
    "Boas! Hoje ninguém dorme antes das 4h 🎊",
    "Olá, o Porto vai tremer com esta festa 🔥",
    "Bem-vindo! Que a tua entrada em 2026 seja épica 🥂",
    "Boas vibrações! Já sentes o espírito da festa?",
    "Olá! Que nunca falte música e boa companhia!",
    "Ei, olha quem voltou! Pronto para mais uma noite épica?",
    "Boas, mestre das selfies! 📸",
    "Olá! Diz-me que vieste dançar!",
    "Bem-vindo! O bar já abriu e o DJ está à tua espera 🎧",
    "Boas! Este ano promete gargalhadas e memórias novas 😄",
    "Olá! Pronto para deixar 2025 no passado com estilo?",
    "Boas! Espero que tragas energia, porque vai ser longa 🎶",
    "Olá! O Diácono Remédios declara aberta a festa 🥳"
]

# =====================================================
# 🧩 Inserção no Qdrant
# =====================================================
print(f"💾 A inserir {len(saudacoes)} saudações na coleção...")

for frase in saudacoes:
    try:
        vector = model.encode(frase).tolist()
        ponto = models.PointStruct(
            id=random.randint(1, 1_000_000_000),
            vector=vector,
            payload={
                "tema": "saudacao",
                "pergunta": frase,
                "resposta": frase,
                "tipo": "saudacao",
                "timestamp": time.time(),
            },
        )
        client.upsert(collection_name=COLLECTION, points=[ponto])
    except Exception as e:
        print(f"⚠️ Erro ao inserir '{frase}': {e}")

print(f"✅ Inserção concluída! {len(saudacoes)} saudações adicionadas à coleção.")
