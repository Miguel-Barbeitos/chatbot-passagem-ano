import streamlit as st
import json, random, os, time, re, unicodedata
from datetime import datetime
from learning_qdrant import guardar_mensagem, procurar_resposta_semelhante
from learning_memory import atualizar_memoria, procurar_resposta_memorizada

# =====================================================
# ⚙️ Configuração inicial
# =====================================================
st.set_page_config(page_title="🎉 Diácono Remédios - Chatbot 🎆", page_icon="🎆")
st.title("🎉 Assistente da Passagem de Ano 2025/2026 🎆")

# =====================================================
# 📂 Utilitários
# =====================================================
def carregar_json(path):
    """Carrega ficheiros JSON com segurança."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def normalizar(txt: str) -> str:
    """Converte texto para minúsculas e remove acentos e pontuação."""
    if not isinstance(txt, str):
        return ""
    t = txt.lower().strip()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

# =====================================================
# 📄 Dados
# =====================================================
profiles = carregar_json("profiles.json")
event = carregar_json("event.json")

# =====================================================
# 🧍 Identificação do utilizador
# =====================================================
try:
    params = st.query_params  # versões novas (>= 1.39)
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
# 👋 Saudação inicial
# =====================================================
hora = datetime.now().hour
saud = "Bom dia" if hora < 12 else "Boa tarde" if hora < 20 else "Boa noite"
st.success(f"{saud}, {nome}! 👋 Bem-vindo ao Assistente da Passagem de Ano!")

# =====================================================
# 🧠 Função principal de geração de resposta
# =====================================================
def gerar_resposta(pergunta, perfil):
    pergunta_l = normalizar(pergunta)

    # 0️⃣ Cumprimentos simples
    if any(w in pergunta_l for w in ["ola", "boa tarde", "boa noite", "bom dia", "boas"]):
        respostas_cumprimentos = [
            f"Olá, {perfil['nome']}! 😄 Pronto para uma passagem de ano épica?",
            f"Boas, {perfil['nome']}! Preparado para dançar até cair? 💃🕺",
            f"Olá, {perfil['nome']}! O Diácono Remédios está ao seu dispor 🙏✨",
            f"Olá, {perfil['nome']}! Espero que tragas boa disposição 🍾",
        ]
        resposta = random.choice(respostas_cumprimentos)
        guardar_mensagem(perfil["nome"], pergunta, resposta)
        atualizar_memoria(pergunta, resposta)
        return resposta

    # 1️⃣ Identidade
    if any(p in pergunta_l for p in ["como te chamas", "quem es tu", "quem es", "qual e o teu nome", "como te devo chamar", "teu nome", "te chamas"]):
        respostas_nome = [
            "Sou o Diácono Remédios, ao vosso serviço 🙏😄",
            "Chamam-me Diácono Remédios — e trago boa disposição! 😎",
            "Sou o Diácono Remédios, o assistente oficial da festa 🎉",
            "Diácono Remédios, para o servir com graça e alegria! ✨",
            "Sou o Diácono Remédios, receitando gargalhadas grátis — sem contraindicações! 😂",
        ]
        resposta = random.choice(respostas_nome)
        guardar_mensagem(perfil["nome"], pergunta, resposta)
        atualizar_memoria(pergunta, resposta)
        return resposta

    # 2️⃣ Memória semântica (Qdrant)
    resposta_semelhante = procurar_resposta_semelhante(pergunta_l)
    if resposta_semelhante:
        return f"Já me perguntaste algo parecido 😄 {resposta_semelhante}"

    # 3️⃣ Memória local
    resposta_memorizada = procurar_resposta_memorizada(pergunta_l)
    if resposta_memorizada:
        return f"Lembro-me disso! 😉 {resposta_memorizada}"

    # 4️⃣ Regras gerais
    if any(w in pergunta_l for w in ["wifi", "wi fi", "wi fi", "internet", "rede"]):
        resposta = f"A senha do Wi-Fi é **{event.get('wifi', 'CasaDoMiguel2025')}** 😉"

    elif any(w in pergunta_l for w in ["onde", "local", "morada", "sitio", "localizacao", "fica longe"]):
        resposta = f"A festa vai ser em **{event.get('local', 'Porto')}** 🎆"

    elif any(w in pergunta_l for w in ["hora", "quando", "a que horas", "comeca", "começa"]):
        resposta = f"Começa às **{event.get('hora', '21h00')}** — não faltes! 🕺"

    elif any(w in pergunta_l for w in ["roupa", "dress", "vestir", "codigo", "cor", "amarelo"]):
        resposta = f"O dress code é **{event.get('dress_code', 'casual elegante')}**, e a cor deste ano é **amarelo 💛**."

    else:
        resposta = random.choice([
            "Vai ser uma noite épica 🎉",
            "Só posso dizer que vai haver surpresas 😉",
            "Não revelo tudo, mas vai ser memorável 🎆"
        ])

    guardar_mensagem(perfil["nome"], pergunta, resposta)
    atualizar_memoria(pergunta, resposta)
    return resposta

# =====================================================
# 💬 Interface do Chat
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
