import os, time, random, itertools
from typing import List, Tuple, Dict, Set
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

# =========================
# ⚙️ Configuração
# =========================
COLLECTION = "chat_memoria"
QDRANT_PATH = "./qdrant_storage"   # usa armazenamento local; se precisares em memória troca para QdrantClient(":memory:")
os.makedirs(QDRANT_PATH, exist_ok=True)

print("🔧 A inicializar modelo multilíngue…")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
dim = model.get_sentence_embedding_dimension()

print("🗂️ A preparar Qdrant…")
client = QdrantClient(path=QDRANT_PATH)

# Recria a coleção para começar limpo
client.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
)

# =========================
# 🧩 “Linguagem” (sinónimos/slots)
# =========================
CIDADES_PT = ["Porto", "Lisboa", "Coimbra", "Braga", "Aveiro", "Faro", "Guimarães", "Viana do Castelo"]
TRANSPORTES = ["carro", "comboio", "metro", "autocarro", "a pé", "TVDE"]
HORAS = ["21h00", "20h30", "22h00"]
COMIDAS = ["bacalhau", "polvo", "leitão", "francesinha", "caldo verde", "rabanadas", "bolo de chocolate"]
BEBIDAS = ["espumante", "vinho", "cerveja", "gin", "cocktails"]
MUSICAS = ["DJ Tiago", "playlist anos 2000", "kizomba", "funk", "hip hop", "pop", "rock clássico"]
VESTUARIO = ["casual elegante", "smart casual"]
CORES = ["amarelo 💛", "dourado ✨"]
EMOJIS_FESTA = ["🎉", "🥳", "🎆", "🎇", "💃", "🕺"]
EMOJIS_BEBIDAS = ["🍾", "🍻", "🍷", "🍸"]
EMOJIS_MUSICA = ["🎶", "🎧", "🎤"]

# Benfica ❤️
CLUBES = ["Benfica", "Porto", "Sporting", "Braga"]
BENFICA_ELOGIOS = [
    "Sou do **Benfica**, o maior de Portugal! ❤️⚽",
    "O Glorioso ganha até nos treinos 😎",
    "Benfica? Sempre — os outros que tentem acompanhar 🦅",
    "Mais uma vitória do Benfica? O normal 🔴⚪",
    "O Benfica vai ser campeão — assunto arrumado! 💪",
]
PIADAS_RIVAIS = [
    "Do Porto? Só para ir lá buscar os 3 pontos 😏",
    "Sporting? Só se for o de Braga 🤭",
]

# =========================
# 🧠 Templates por tema
# =========================
TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "local": {
        "perguntas": [
            "Onde é a festa?",
            "Vai ser em {cidade}?",
            "É longe?",
            "Dá para estacionar?",
            "Dá para ir de {meio}?",
            "Fica em casa de quem?",
            "É perto do centro?",
            "Dá para ir a pé?",
        ],
        "respostas": [
            "Vai ser em Casa do Miguel, {cidade}! {festa}",
            "Mesmo no coração de {cidade} — fácil de chegar! {festa}",
            "Nada de longe: o GPS do Diácono guia-te {carro} {festa}",
            "Há espaço para estacionar, mas chega cedo 😜",
            "Se vieres de {meio}, também dá perfeitamente!",
        ],
    },
    "horario": {
        "perguntas": [
            "A que horas começa?",
            "Quando é a festa?",
            "Vai acabar tarde?",
            "Quando se janta?",
            "A que horas é o brinde?",
            "Posso chegar mais tarde?",
        ],
        "respostas": [
            "Começa às {hora} e vai até o sol nascer {festa}",
            "O brinde é à meia-noite, como manda a tradição 🥂",
            "Janta-se por volta das {hora}, por isso não te atrases 😉",
            "Chega quando puderes, mas não percas o brinde!",
        ],
    },
    "comida": {
        "perguntas": [
            "O que vai haver para jantar?",
            "Posso levar sobremesa?",
            "Vai haver comida vegetariana?",
            "Há {prato}?",
            "Há sobremesas?",
            "Há comida para crianças?",
        ],
        "respostas": [
            "Vai haver jantar completo — ninguém passa fome 🍽️",
            "Temos {prato} e mais delícias, até opções vegetarianas 🥦",
            "Podes levar sobremesa, mas as rabanadas já estão reservadas 😏",
            "Haverá doces e {prato}, prepara o estômago 😋",
        ],
    },
    "bebida": {
        "perguntas": [
            "Vai haver bebidas?",
            "Há {bebida}?",
            "Vai ter bar?",
            "Posso levar {bebida}?",
            "Há copos suficientes?",
            "Vai haver {bebida} para o brinde?",
        ],
        "respostas": [
            "Há bar aberto e copo nunca vazio {bebidas}",
            "Vai haver {bebida} e mais — espumante incluído 🍾",
            "Podes levar {bebida}, mas partilha 😜",
        ],
    },
    "roupa": {
        "perguntas": [
            "Qual é o dress code?",
            "O que devo vestir?",
            "Tenho de levar amarelo?",
            "Posso ir casual?",
            "Há código de vestuário?",
        ],
        "respostas": [
            "Dress code: {vestuario} — e um toque de {cor} dá sorte!",
            "Vem bonito mas confortável; vamos dançar muito {festa}",
            "Não é obrigatório, mas um toque de {cor} fica top ✨",
        ],
    },
    "musica": {
        "perguntas": [
            "Vai haver música?",
            "Quem é o DJ?",
            "Posso pedir uma música?",
            "Vai haver karaoke?",
            "Há pista de dança?",
            "Que tipo de música vai tocar?",
            "O som é bom?",
        ],
        "respostas": [
            "Claro! {dj} confirmado {musica}",
            "Há pista de dança e karaoke — cuidado com o micro 🎤",
            "Podes pedir música, mas nada de baladas às 23h59 😅",
            "O som vai estar afinado — até o vizinho dança!",
        ],
    },
    "clima": {
        "perguntas": [
            "Vai estar frio?",
            "Se chover há plano B?",
            "A festa é dentro ou fora?",
            "Vai estar calor?",
            "Preciso de casaco?",
            "Há aquecedores?",
        ],
        "respostas": [
            "Mesmo que chova, a festa é indoor ☔",
            "Frio lá fora, calor cá dentro 🔥",
            "Traz casaco para a rua, mas por dentro vais suar a dançar {festa}",
        ],
    },
    "humor": {
        "perguntas": [
            "Estás animado?",
            "Conta-me uma piada!",
            "Quem é o mais divertido?",
            "És engraçado?",
            "Quem dança pior?",
            "És melhor que o ChatGPT?",
        ],
        "respostas": [
            "Estou elétrico — como as luzes do Benfica na Luz 🎇",
            "Piada: qual é o cúmulo da festa? Acabar antes do brinde 😂",
            "O mais divertido? Quem trouxer {bebida} para toda a gente 😎",
            "Danço tão bem que até o DJ aplaude {musica}",
        ],
    },
    "futebol": {
        "perguntas": [
            "Gostas de futebol?",
            "Qual é o teu clube?",
            "És do Benfica?",
            "És do Porto?",
            "És do Sporting?",
            "Quem é o maior de Portugal?",
            "Quem vai ganhar o campeonato?",
            "Viste o jogo do Benfica?",
            "O Benfica vai ser campeão?",
        ],
        "respostas": (
            BENFICA_ELOGIOS
            + [
                "Benfica acima de tudo — isto é de família ❤️",
                "Futebol? Só se for para ver o Glorioso a ganhar!",
                "No dia do título do Benfica a festa dura dois dias 😎",
            ]
            + PIADAS_RIVAIS
        ),
    },
    "fora_tema": {
        "perguntas": [
            "Quanto é 2+2?",
            "Qual é o teu signo?",
            "Tens sentimentos?",
            "És real?",
            "O que achas de política?",
            "Quem te criou?",
            "Posso levar o cão?",
            "Gostas de filmes?",
        ],
        "respostas": [
            "2+2? Quatro copos de espumante 🥂",
            "O meu signo? Festa 🎉",
            "Sou 100% digital, mas rio-me como gente — sobretudo com golos do Benfica 😍",
            "Não falo de política — só de sobremesas 🍰",
            "O cão é bem-vindo se souber dançar 🐶💃",
        ],
    },
}

# =========================
# 🛠️ Helpers
# =========================
def pick(seq): return random.choice(seq)

def render(template: str) -> str:
    return (
        template
        .replace("{cidade}", pick(CIDADES_PT))
        .replace("{meio}", pick(TRANSPORTES))
        .replace("{hora}", pick(HORAS))
        .replace("{prato}", pick(COMIDAS))
        .replace("{bebida}", pick(BEBIDAS))
        .replace("{vestuario}", pick(VESTUARIO))
        .replace("{cor}", pick(CORES))
        .replace("{festa}", pick(EMOJIS_FESTA))
        .replace("{musica}", pick(EMOJIS_MUSICA))
        .replace("{bebidas}", pick(EMOJIS_BEBIDAS))
        .replace("{dj}", pick(MUSICAS))
    )

def dedup_pairs(pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen: Set[Tuple[str, str]] = set()
    out: List[Tuple[str, str]] = []
    for q, a in pairs:
        key = (q.strip().lower(), a.strip().lower())
        if key not in seen:
            seen.add(key)
            out.append((q.strip(), a.strip()))
    return out

# =========================
# 🧪 Geração massiva
# =========================
def gerar_pares_objetivo(min_total: int = 2200) -> List[Tuple[str, str, str]]:
    pares: List[Tuple[str, str, str]] = []
    # Para cada tema, vamos criar bastantes variações
    for tema, blocos in TEMPLATES.items():
        perguntas = blocos["perguntas"]
        respostas = blocos["respostas"]
        # mais variações para futebol e música
        multiplicador = 5 if tema in ["futebol", "musica", "comida", "bebida"] else 3
        for _ in range(multiplicador):
            for p in perguntas:
                p_r = render(p)
                # Seleciona 2-3 respostas para diversidade
                rs = random.sample(respostas, k=min(3, len(respostas)))
                for r in rs:
                    r_r = render(r)
                    pares.append((tema, p_r, r_r))

    # Duplica com pequenas perturbações de fraseado (sinónimos simples)
    sin_troca = [
        ("vai", "vai haver"),
        ("há", "vai haver"),
        ("é", "vai ser"),
        ("posso", "dá para eu"),
        ("qual é", "que é"),
        ("onde é", "onde vai ser"),
        ("a que horas", "às quantas horas"),
    ]
    extra: List[Tuple[str, str, str]] = []
    for tema, q, a in pares:
        q_alt = q
        if random.random() < 0.6:
            old, new = pick(sin_troca)
            q_alt = q_alt.replace(f" {old} ", f" {new} ")
        extra.append((tema, q_alt, a))
    pares += extra

    # Deduplicar
    pares_dedup = []
    seen = set()
    for tema, q, a in pares:
        key = (tema, q.strip().lower(), a.strip().lower())
        if key not in seen:
            seen.add(key)
            pares_dedup.append((tema, q.strip(), a.strip()))

    # Garantir volume
    if len(pares_dedup) < min_total:
        # repetir amostras aleatórias até atingir mínimo
        shortfall = min_total - len(pares_dedup)
        amostra = random.choices(pares_dedup, k=shortfall)
        pares_dedup.extend(amostra)

    random.shuffle(pares_dedup)
    return pares_dedup

# =========================
# 📤 Inserção em lotes
# =========================
def upsert_em_lotes(pares: List[Tuple[str, str, str]], batch_size: int = 256):
    total = len(pares)
    print(f"🚚 A inserir {total} pares em lotes de {batch_size}…")
    inserted = 0
    t0 = time.time()

    for i in range(0, total, batch_size):
        batch = pares[i:i + batch_size]
        perguntas = [q for _, q, _ in batch]
        vectors = model.encode(perguntas, batch_size=64, show_progress_bar=False)

        pontos = []
        for (tema, q, a), vec in zip(batch, vectors):
            payload = {
                "user": "sistema",
                "pergunta": q,
                "resposta": a,
                "timestamp": time.time(),
                "fonte": "gerador-2000+",
                "contexto": {
                    "tema": tema,
                    "evento": "Passagem de Ano 2025/2026",
                    "local": "Casa do Miguel, Porto",
                    "benfica": True if tema == "futebol" else False
                },
            }
            pontos.append(
                models.PointStruct(
                    id=random.randint(1, 1_000_000_000),
                    vector=vec.tolist(),
                    payload=payload
                )
            )

        client.upsert(collection_name=COLLECTION, points=pontos)
        inserted += len(batch)
        if (i // batch_size) % 5 == 0:
            print(f"   … {inserted}/{total} inseridos")

    dt = time.time() - t0
    print(f"✅ Inseridos {inserted} pares no Qdrant em {dt:.1f}s")

# =========================
# ▶️ Run
# =========================
if __name__ == "__main__":
    random.seed(42)
    print("🧠 A gerar pares de treino…")
    pares = gerar_pares_objetivo(min_total=2200)
    print(f"🧮 Gerados {len(pares)} pares. Exemplo:")
    for i in range(3):
        print("   •", pares[i])

    upsert_em_lotes(pares, batch_size=256)
    print("🏁 Concluído! O Diácono já está com memória encarnada 🔴⚪")
