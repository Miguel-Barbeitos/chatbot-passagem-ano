import streamlit as st
import json, random, os, time, re, unicodedata
from datetime import datetime
from learning_qdrant import guardar_mensagem, procurar_resposta_semelhante

# =====================================================
# ⚙️ Configuração
# =====================================================
st.set_page_config(page_title="🎉 Chatbot 🎆", page_icon="🎆")
st.title("🎉 Assistente da Passagem de Ano 2025/2026 🎆")

# =====================================================
# 🔧 Utilitários
# =====================================================
def normalizar(txt: str) -> str:
    """Minúsculas, remover acentos, pontuação e espaços duplicados."""
    if not isinstance(txt, str):
        return ""
    t = txt.lower().strip()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def carregar_json(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

# =====================================================
# 📂 Dados
# =====================================================
profiles = carregar_json("profiles.json")
event = carregar_json("event.json")

# =====================================================
# 🧍 Identificação
# =====================================================
nomes = [p["nome"] for p in profiles]
params = st.query_params

if "user" not in st.session_state:
    if "user" in params and params["user"] in nomes:
        st.session_state["user"] = params["user"]
    else:
        nome_sel = st.selectbox("Quem és tu?", nomes)
        if st.button("Confirmar"):
            st.session_state["user"] = nome_sel
            st.query_params["user"] = nome_sel
            st.rerun()
        st.stop()

nome = st.session_state["user"]
perfil = next(p for p in profiles if p["nome"] == nome)

# =====================================================
# 👋 Saudação inicial
# =====================================================
hora = datetime.now().hour
saud = "Bom dia" if hora < 12 else "Boa tarde" if hora < 20 else "Boa noite"
st.success(f"{saud}, {nome}! 👋 Bem-vindo ao Assistente da Passagem de Ano!")

# =====================================================
# 💬 Interface
# =====================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

prompt = st.chat_input("Escreve aqui a tua mensagem 👇")

# =====================================================
# 🧠 Geração de resposta
# =====================================================
def gerar_resposta(pergunta, perfil):
    pergunta_l = normalizar(pergunta)

    # 1️⃣ — Procurar respostas no Qdrant (inteligência vetorial)
    resposta_memoria = procurar_resposta_semelhante(pergunta_l, limite_conf=0.7, top_k=3)
    if resposta_memoria:
        guardar_mensagem(perfil["nome"], pergunta_l, resposta_memoria, perfil)
        return ajustar_tom_por_perfil(resposta_memoria, perfil)

    # 2️⃣ — Regras básicas (fallback)
    if any(p in pergunta_l for p in ["como te chamas", "quem es tu", "qual e o teu nome", "te chamas"]):
        return ajustar_tom_por_perfil("Sou o Diácono Remédios, ao vosso serviço 🙏😄", perfil)

    if any(p in pergunta_l for p in ["onde", "local", "sitio", "morada", "porto", "fica longe"]):
        local = event.get("local", "Casa do Miguel, Porto")
        return ajustar_tom_por_perfil(f"A festa vai ser em **{local}** 🎉", perfil)

    if any(p in pergunta_l for p in ["hora", "quando", "que horas", "a que horas"]):
        return ajustar_tom_por_perfil(f"Começa às **{event.get('hora', '21h00')}** — e promete durar até ao nascer do sol 🌅", perfil)

    if any(p in pergunta_l for p in ["wifi", "wi fi", "internet", "rede"]):
        return ajustar_tom_por_perfil(f"A senha do Wi-Fi é **{event.get('wifi', 'CasaDoMiguel2025')}** 📶", perfil)

    if any(p in pergunta_l for p in ["dress", "roupa", "vestir", "codigo", "cor", "amarelo"]):
        return ajustar_tom_por_perfil(
            f"O dress code é **{event.get('dress_code', 'casual elegante')}**, e a cor deste ano é **amarelo 💛**.", perfil
        )

    respostas_default = [
        "Vai ser uma noite épica 🎉",
        "Só posso dizer que vai haver surpresas 😉",
        "Não revelo tudo, mas vai ser memorável 🎆"
    ]
    resposta = random.choice(respostas_default)
    guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil)
    return ajustar_tom_por_perfil(resposta, perfil)

# =====================================================
# 🎭 Ajustar o tom conforme o perfil
# =====================================================
def ajustar_tom_por_perfil(resposta, perfil):
    tipo = perfil.get("personalidade", "neutro").lower()

    humor_extra = {
        "divertido": ["😂", "😎", "🎉", "😉", "O Diácono aprova! 🙌", "Que comece a festa! 🥳"],
        "extrovertido": ["🔥", "💃🕺", "😄", "Isso vai ser épico!", "O DJ já sabe o teu nome 😜"],
        "sério": ["Entendido.", "Percebo.", "Certo.", "👍"],
        "formal": ["Com os meus melhores cumprimentos.", "Será um prazer recebê-lo.", "Tenha uma excelente noite."],
        "sarcastico": ["Ah pois claro… 🙃", "Pergunta retórica ou quer mesmo saber? 😏", "Com tanto suspense, parece novela das 9 😅"],
        "calmo": ["Tudo tranquilo, sem stress. ✨", "Vai correr tudo bem. 🌙", "Mantém o espírito leve. 🕊️"]
    }

    if tipo in humor_extra:
        extra = random.choice(humor_extra[tipo])
        resposta = f"{resposta} {extra}"

    return resposta

# =====================================================
# 💬 Ciclo da conversa
# =====================================================
if prompt:
    st.session_state.chat_history.append(("user", prompt))
    with st.spinner("💭 O Diácono está a pensar..."):
        time.sleep(0.8)
        resposta = gerar_resposta(prompt, perfil)
    st.session_state.chat_history.append(("bot", resposta))

# Mostrar conversa
for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"**{nome}:** {msg}")
    else:
        st.markdown(f"**Assistente:** {msg}")
