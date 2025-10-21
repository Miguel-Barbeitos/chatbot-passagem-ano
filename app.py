import streamlit as st
import json, random, os, time
from datetime import datetime
from learning_qdrant import guardar_mensagem, procurar_resposta_semelhante
from learning_memory import atualizar_memoria, procurar_resposta_memorizada

# =====================================================
# ⚙️ Configuração
# =====================================================
st.set_page_config(page_title="🎉 Diácono Remédios - Chatbot 🎆", page_icon="🎆")
st.title("🎉 Assistente da Passagem de Ano 2025/2026 🎆")

# =====================================================
# 📂 Carregar dados
# =====================================================
def carregar_json(path):
    """Lê ficheiros JSON de perfis e evento."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

profiles = carregar_json("profiles.json")
event = carregar_json("event.json")

# =====================================================
# 🧍 Identificação do utilizador
# =====================================================
# Compatibilidade entre versões do Streamlit
try:
    params = st.query_params  # novas versões (>=1.39)
except AttributeError:
    params = st.experimental_get_query_params()  # versões antigas

nomes = [p["nome"] for p in profiles]

if "user" not in st.session_state:
    if "user" in params and params["user"] in nomes:
        st.session_state["user"] = params["user"]
    else:
        nome_sel = st.selectbox("Quem és tu?", nomes)
        if st.button("Confirmar"):
            st.session_state["user"] = nome_sel
            try:
                st.query_params["user"] = nome_sel
            except AttributeError:
                st.experimental_set_query_params(user=nome_sel)
            st.rerun()
        st.stop()

nome = st.session_state["user"]
perfil = next(p for p in profiles if p["nome"] == nome)

# =====================================================
# 👋 Saudação
# =====================================================
hora = datetime.now().hour
saud = "Bom dia" if hora < 12 else "Boa tarde" if hora < 20 else "Boa noite"
st.success(f"{saud}, {nome}! 👋 Bem-vindo ao Assistente da Passagem de Ano!")

# =====================================================
# 🧠 Função principal
# =====================================================
def gerar_resposta(pergunta, perfil):
    pergunta_l = pergunta.lower()

    # 1️⃣ Verifica memória local (aprendizagem simples)
    resposta_memorizada = procurar_resposta_memorizada(pergunta_l)
    if resposta_memorizada:
        return f"Lembro-me disso! 😉 {resposta_memorizada}"

    # 2️⃣ Verifica memória semântica (Qdrant)
    resposta_semelhante = procurar_resposta_semelhante(pergunta_l)
    if resposta_semelhante:
        return f"Já me perguntaste algo parecido 😄 {resposta_semelhante}"

    # 3️⃣ Caso contrário, aplica regras básicas
    if any(p in pergunta_l for p in ["como te chamas", "quem es tu", "quem és tu", "qual é o teu nome", "como te devo chamar", "teu nome", "te chamas"]):
        respostas_nome = [
            "Sou o Diácono Remédios, ao vosso serviço 🙏😄",
            "Chamam-me Diácono Remédios — e trago boa disposição! 😎",
            "Sou o Diácono Remédios, o assistente oficial da festa 🎉",
            "Diácono Remédios, para o servir com graça e alegria! ✨",
            "Sou o Diácono Remédios, receitando gargalhadas grátis — sem contraindicações! 😂",
        ]
        resposta = random.choice(respostas_nome)

    elif any(w in pergunta_l for w in ["wifi", "wi-fi", "wi fi", "internet", "rede"]):
        resposta = f"A senha do Wi-Fi é **{event.get('wifi', 'CasaDoMiguel2025')}** 😉"

    elif any(w in pergunta_l for w in ["onde", "local", "morada", "sitio", "localização", "fica longe"]):
        resposta = f"A festa vai ser em **{event.get('local', 'Porto')}** 🎆"

    elif any(w in pergunta_l for w in ["hora", "quando", "a que horas", "começa", "comeca"]):
        resposta = f"Começa às **{event.get('hora', '21h00')}** — não faltes! 🕺"

    elif any(w in pergunta_l for w in ["roupa", "dress", "vestir", "código", "cor", "amarelo"]):
        resposta = f"O dress code é **{event.get('dress_code', 'casual elegante')}**, e a cor deste ano é **amarelo 💛**."

    else:
        resposta = random.choice([
            "Vai ser uma noite épica 🎉",
            "Só posso dizer que vai haver surpresas 😉",
            "Não revelo tudo, mas vai ser memorável 🎆"
        ])

    # 4️⃣ Guarda conhecimento nas memórias
    guardar_mensagem(perfil["nome"], pergunta, resposta)
    atualizar_memoria(pergunta, resposta)

    return resposta

# =====================================================
# 💬 Interface do chat
# =====================================================
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
