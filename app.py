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
# ⚙️ Configuração inicial
# =====================================================
st.set_page_config(page_title="Chatbot da Passagem de Ano", page_icon="🎆")

with open("profiles.json", "r", encoding="utf-8") as f:
    profiles = json.load(f)

with open("event.json", "r", encoding="utf-8") as f:
    event = json.load(f)

# =====================================================
# 🎭 Interface Streamlit
# =====================================================
st.title("🎇 Chatbot da Passagem de Ano")
st.markdown("Conversa com o assistente oficial da festa 🎉")

nomes = [p["nome"] for p in profiles]
nome_sel = st.selectbox("Quem és tu?", nomes)
perfil = next(p for p in profiles if p["nome"] == nome_sel)

if "historico" not in st.session_state:
    st.session_state.historico = []

prompt = st.chat_input("Escreve a tua mensagem...")

# =====================================================
# 🧠 Funções auxiliares
# =====================================================
def normalizar(texto):
    return texto.lower().strip()

def ajustar_tom_por_perfil(texto, perfil):
    """Adapta o tom da resposta ao tipo de perfil."""
    if perfil.get("tom") == "humoristico":
        extras = ["😄", "😂", "😉", "🎉", "🥳"]
        if not any(e in texto for e in extras):
            texto += " " + random.choice(extras)
    elif perfil.get("tom") == "formal":
        texto = "Caro " + perfil["nome"] + ", " + texto
    return texto

def gerar_resposta(pergunta, perfil):
    pergunta_l = normalizar(pergunta)

    # 1️⃣ — Procurar no Qdrant (respostas inteligentes)
    resposta_memoria = procurar_resposta_semelhante(pergunta_l, limite_conf=0.75, top_k=5)

    # Evita respostas genéricas de saudação fora de contexto
    if resposta_memoria:
        if any(p in pergunta_l for p in ["olá", "ola", "bom dia", "boa tarde", "boa noite", "boas"]):
            return ajustar_tom_por_perfil(resposta_memoria, perfil)
        else:
            # Evita responder com saudação se a pergunta não for de saudação
            if "olá" in resposta_memoria.lower() and not any(p in pergunta_l for p in ["olá", "ola", "saudacao", "cumprimento"]):
                resposta_memoria = None

    if resposta_memoria:
        guardar_mensagem(perfil["nome"], pergunta_l, resposta_memoria, perfil)
        return ajustar_tom_por_perfil(resposta_memoria, perfil)

    # 2️⃣ — Regras simples (fallback)
    if any(p in pergunta_l for p in ["como te chamas", "quem és tu", "qual é o teu nome", "te chamas"]):
        return ajustar_tom_por_perfil("Sou o Diácono Remédios, ao vosso serviço 🙏😄", perfil)

    if any(p in pergunta_l for p in ["onde", "local", "sitio", "morada", "porto", "fica longe"]):
        local = event.get("local", "Casa do Miguel, Porto")
        return ajustar_tom_por_perfil(f"A festa vai ser em **{local}** 🎉", perfil)

    if any(p in pergunta_l for p in ["hora", "quando", "que horas", "a que horas"]):
        return ajustar_tom_por_perfil(
            f"Começa às **{event.get('hora', '21h00')}** — e promete durar até ao nascer do sol 🌅",
            perfil,
        )

    if any(p in pergunta_l for p in ["wifi", "wi fi", "internet", "rede"]):
        return ajustar_tom_por_perfil(
            f"A senha do Wi-Fi é **{event.get('wifi', 'CasaDoMiguel2025')}** 📶", perfil
        )

    if any(p in pergunta_l for p in ["dress", "roupa", "vestir", "codigo", "cor", "amarelo"]):
        return ajustar_tom_por_perfil(
            f"O dress code é **{event.get('dress_code', 'casual elegante')}**, e a cor deste ano é **amarelo 💛**.",
            perfil,
        )

    respostas_default = [
        "Vai ser uma noite épica 🎉",
        "Só posso dizer que vai haver surpresas 😉",
        "Não revelo tudo, mas vai ser memorável 🎆",
        "Benfica é o maior — e a festa também 🔴⚪",
        "O Diácono não revela segredos antes do brinde 🍾",
    ]
    resposta = random.choice(respostas_default)
    guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil)
    return ajustar_tom_por_perfil(resposta, perfil)

# =====================================================
# 💬 Interface de chat
# =====================================================
for msg in st.session_state.historico:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt:
    st.session_state.historico.append({"role": "user", "content": f"{perfil['nome']}: {prompt}"})
    resposta = gerar_resposta(prompt, perfil)
    st.session_state.historico.append({"role": "assistant", "content": f"**Assistente:** {resposta}"})

    with st.chat_message("assistant"):
        st.markdown(f"**Assistente:** {resposta}")
