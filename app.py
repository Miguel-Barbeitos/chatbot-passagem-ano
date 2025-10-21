import streamlit as st
import random
import json
from learning_qdrant import (
    guardar_mensagem,
    procurar_resposta_semelhante,
    procurar_resposta_contextual,
    limpar_qdrant
)

# =====================================================
# ⚙️ Configuração base
# =====================================================
st.set_page_config(page_title="🎉 Assistente da Passagem de Ano 2025/2026 🎆", page_icon="🎆")
st.title("🎉 Assistente da Passagem de Ano 2025/2026 🎆")

# =====================================================
# 🔧 Funções utilitárias
# =====================================================
def normalizar(txt: str) -> str:
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
# 📂 Dados base
# =====================================================
profiles = carregar_json("profiles.json")
event = carregar_json("event.json")

# =====================================================
# 🧍 Identificação do utilizador
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
# 💬 Entrada de mensagem
# =====================================================
prompt = st.chat_input("Escreve aqui a tua mensagem 👇")

# =====================================================
# 🎭 Ajustar tom pela personalidade
# =====================================================
def ajustar_tom_por_perfil(resposta, perfil):
    humor = perfil.get("personalidade", "").lower()
    if "divertido" in humor or "extrovertido" in humor:
        return resposta + " 😄"
    if "formal" in humor:
        return "Com todo o respeito, " + resposta
    if "sarcástico" in humor:
        return resposta + " 😉"
    return resposta

# =====================================================
# 🧠 Função principal de resposta (AI-first)
# =====================================================
def gerar_resposta(pergunta, perfil):
    pergunta_l = normalizar(pergunta)

    # 1️⃣ — Saudações diretas (evita respostas exageradas)
    if any(w in pergunta_l for w in ["ola", "olá", "boas", "bom dia", "boa tarde", "boa noite"]):
        resposta = random.choice([
            f"Olá, {perfil['nome']}! 👋 Pronto para começar a festa?",
            f"Boas, {perfil['nome']}! 😄 Já a pensar na noite de ano?",
            f"Olá, {perfil['nome']}! O Diácono Remédios ao seu dispor 🙏✨",
            f"Bem-vindo, {perfil['nome']}! 🎉 Está quase na hora do brinde!"
        ])
        guardar_mensagem(perfil["nome"], pergunta_l, resposta, "saudacao")
        return ajustar_tom_por_perfil(resposta, perfil)

    # 2️⃣ — Procurar no Qdrant (IA semântica)
    resposta_memoria = procurar_resposta_semelhante(pergunta_l, limite_conf=0.65, top_k=5)
    if resposta_memoria:
        guardar_mensagem(perfil["nome"], pergunta_l, resposta_memoria, "memoria")
        return ajustar_tom_por_perfil(resposta_memoria, perfil)

    # 3️⃣ — Regras temáticas (fallback)
    if any(p in pergunta_l for p in ["como te chamas", "quem es tu", "qual e o teu nome", "te chamas"]):
        resposta = random.choice([
            "Sou o Diácono Remédios, ao vosso serviço 🙏😄",
            "Chamam-me Diácono Remédios — e trago boa disposição! 😎",
            "Sou o Diácono Remédios, o assistente oficial da festa 🎉",
        ])

    elif any(p in pergunta_l for p in ["onde", "local", "sitio", "morada", "porto", "fica longe"]):
        local = event.get("local", "Casa do Miguel, Porto")
        resposta = f"A festa vai ser em **{local}** 🎉"

    elif any(p in pergunta_l for p in ["hora", "quando", "que horas", "a que horas"]):
        hora_festa = event.get("hora", "21h00")
        resposta = f"Começa às **{hora_festa}** — e promete durar até ao nascer do sol 🌅"

    elif any(p in pergunta_l for p in ["wifi", "wi fi", "internet", "rede"]):
        resposta = f"A senha do Wi-Fi é **{event.get('wifi', 'CasaDoMiguel2025')}** 📶"

    elif any(p in pergunta_l for p in ["dress", "roupa", "vestir", "codigo", "cor", "amarelo"]):
        resposta = f"O dress code é **{event.get('dress_code', 'casual elegante')}**, e a cor deste ano é **amarelo 💛**."

    elif any(p in pergunta_l for p in ["musica", "música", "dj", "som"]):
        resposta = "DJ confirmado, e vai tocar até os vizinhos dançarem 💃🕺"

    else:
        resposta = random.choice([
            "Vai ser uma noite épica 🎉",
            "Só posso dizer que vai haver surpresas 😉",
            "Não revelo tudo, mas vai ser memorável 🎆",
        ])

    guardar_mensagem(perfil["nome"], pergunta_l, resposta, "regras")
    return ajustar_tom_por_perfil(resposta, perfil)

# =====================================================
# 💬 Loop da conversa
# =====================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if prompt:
    st.session_state.chat_history.append(("user", prompt))
    with st.spinner("💭 O Diácono está a pensar..."):
        time.sleep(0.8)
        resposta = gerar_resposta(prompt, perfil)
    st.session_state.chat_history.append(("bot", resposta))

for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"**{nome}:** {msg}")
    else:
        st.markdown(f"**Assistente:** {msg}")
