import os, zipfile, json

# === Estrutura base ===
base_dir = "chatbot-passagem-ano"
os.makedirs(base_dir, exist_ok=True)

# --- requirements.txt ---
req = """streamlit
sentence-transformers
qdrant-client
numpy
scikit-learn
"""
with open(os.path.join(base_dir, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(req)

# --- learning_qdrant.py ---
learning_code = """from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import random, os

model = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient(path="./qdrant_data")

qdrant.recreate_collection(
    collection_name="mensagens",
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
)

def guardar_mensagem(user, texto, resposta):
    embedding = model.encode(texto).tolist()
    qdrant.upsert(
        collection_name="mensagens",
        points=[models.PointStruct(id=random.randint(0, 1e9),
                                   vector=embedding,
                                   payload={"user": user, "texto": texto, "resposta": resposta})]
    )

def procurar_resposta_semelhante(texto, limiar=0.85):
    query = model.encode(texto).tolist()
    resultados = qdrant.search(collection_name="mensagens", query_vector=query, limit=1)
    if resultados and resultados[0].score >= limiar:
        return resultados[0].payload["resposta"]
    return None
"""
with open(os.path.join(base_dir, "learning_qdrant.py"), "w", encoding="utf-8") as f:
    f.write(learning_code)

# --- app.py ---
app_code = """import streamlit as st
import json, random, os, time
from datetime import datetime
from learning_qdrant import guardar_mensagem, procurar_resposta_semelhante

st.set_page_config(page_title="🎉 Diácono Remédios - Chatbot 🎆", page_icon="🎆")
st.title("🎉 Assistente da Passagem de Ano 2025/2026 🎆")

def carregar_json(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

profiles = carregar_json("profiles.json")
event = carregar_json("event.json")

nomes = [p["nome"] for p in profiles]
params = st.experimental_get_query_params()

if "user" not in st.session_state:
    if "user" in params and params["user"][0] in nomes:
        st.session_state["user"] = params["user"][0]
    else:
        nome_sel = st.selectbox("Quem és tu?", nomes)
        if st.button("Confirmar"):
            st.session_state["user"] = nome_sel
            st.experimental_set_query_params(user=nome_sel)
            st.rerun()
        st.stop()

nome = st.session_state["user"]
perfil = next(p for p in profiles if p["nome"] == nome)

hora = datetime.now().hour
saud = "Bom dia" if hora < 12 else "Boa tarde" if hora < 20 else "Boa noite"
st.success(f"{saud}, {nome}! 👋 Bem-vindo ao Assistente da Passagem de Ano!")

def gerar_resposta(pergunta, perfil):
    pergunta_l = pergunta.lower()
    resposta_memoria = procurar_resposta_semelhante(pergunta_l)
    if resposta_memoria:
        return f"Lembro-me disso! 😉 {resposta_memoria}"

    if "como te chamas" in pergunta_l or "quem es tu" in pergunta_l:
        resposta = random.choice([
            "Sou o Diácono Remédios, o assistente oficial desta festa 🎉",
            "Chamam-me Diácono Remédios — o guru da boa disposição 😄"
        ])
    elif "wifi" in pergunta_l or "wi-fi" in pergunta_l:
        resposta = f"A senha do Wi-Fi é **{event.get('wifi','CasaDoMiguel2025')}** 😉"
    elif "onde" in pergunta_l:
        resposta = f"A festa vai ser em **{event.get('local','Porto')}** 🎆"
    elif "hora" in pergunta_l or "quando" in pergunta_l:
        resposta = f"Começa às **{event.get('hora','21h00')}** — não faltes! 🕺"
    elif "roupa" in pergunta_l or "dress" in pergunta_l:
        resposta = f"A cor deste ano é **amarelo 💛** — brilha muito, {nome}!"
    else:
        resposta = random.choice([
            "Vai ser uma noite épica 🎉",
            "Só posso dizer que vai haver surpresas 😉",
            "Não revelo tudo, mas vai ser memorável 🎆"
        ])

    guardar_mensagem(perfil["nome"], pergunta, resposta)
    return resposta

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

prompt = st.chat_input("Escreve aqui a tua mensagem 👇")

if prompt:
    st.session_state.chat_history.append(("user", prompt))
    with st.spinner("💭 O Diácono está a pensar..."):
        time.sleep(0.7)
        resposta = gerar_resposta(prompt, perfil)
    st.session_state.chat_history.append(("bot", resposta))

for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"**{nome}:** {msg}")
    else:
        st.markdown(f"**Assistente:** {msg}")
"""
with open(os.path.join(base_dir, "app.py"), "w", encoding="utf-8") as f:
    f.write(app_code)

# --- profiles.json (exemplo) ---
profiles = [
    {"nome": "Miguel", "personalidade": "divertido"},
    {"nome": "Jojo", "personalidade": "brincalhao"},
    {"nome": "Barbeitos", "personalidade": "sarcastico"}
]
with open(os.path.join(base_dir, "profiles.json"), "w", encoding="utf-8") as f:
    json.dump(profiles, f, ensure_ascii=False, indent=2)

# --- event.json (exemplo) ---
event = {
    "local": "Casa do Miguel, Porto",
    "hora": "21h00",
    "wifi": "CasaDoMiguel2025",
    "trazer": ["boa disposição", "bebida favorita", "amarelo"]
}
with open(os.path.join(base_dir, "event.json"), "w", encoding="utf-8") as f:
    json.dump(event, f, ensure_ascii=False, indent=2)

# --- ZIP final ---
zip_path = "chatbot-passagem-ano.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for folder, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(folder, file)
            zipf.write(file_path, os.path.relpath(file_path, base_dir))

print(f"✅ Ficheiro ZIP criado com sucesso: {zip_path}")
