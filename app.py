import streamlit as st
import json
import random
import time
import re
import unicodedata
from datetime import datetime

from learning_qdrant import (
    identificar_intencao,
    procurar_resposta_semelhante,
    guardar_mensagem,
)

# =====================================================
# ⚙️ Configuração da página
# =====================================================
st.set_page_config(page_title="🎉 Assistente da Passagem de Ano 2025/2026 🎆", page_icon="🎆")
st.title("🎉 Assistente da Passagem de Ano 2025/2026 🎆")

# =====================================================
# 🔧 Utilitários
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

def carregar_json(path: str, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

# =====================================================
# 📂 Dados base
# =====================================================
profiles = carregar_json("profiles.json", default=[])
event = carregar_json("event.json", default={
    "local": "Casa do Miguel, Porto",
    "hora": "21h00",
    "wifi": "CasaDoMiguel2025",
    "dress_code": "casual elegante",
    "trazer": ["boa disposição"]
})

if not profiles:
    st.error("⚠️ Faltam perfis em 'profiles.json'.")
    st.stop()

# =====================================================
# 🧍 Seleção do utilizador
# =====================================================
nomes = [p["nome"] for p in profiles]
params = st.query_params

if "user" in params and params["user"] in nomes:
    nome = params["user"]
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        nome_sel = st.selectbox("Quem és tu?", nomes, index=0)
    with col2:
        if st.button("Confirmar"):
            st.query_params.update({"user": nome_sel})
            st.rerun()
    st.stop()

perfil = next(p for p in profiles if p["nome"] == nome)

# =====================================================
# 👋 Saudação inicial
# =====================================================
hora = datetime.now().hour
saud = "Bom dia" if hora < 12 else "Boa tarde" if hora < 20 else "Boa noite"
st.success(f"{saud}, {nome}! 👋 Bem-vindo ao Assistente da Passagem de Ano!")

# =====================================================
# 🧠 Tom adaptativo
# =====================================================
def ajustar_tom(texto: str, contexto: str, perfil: dict) -> str:
    ctx_animado = {"festa", "piadas", "futebol", "social", "saudacao", "comida", "bebida"}
    ctx_informativo = {"wifi", "hora", "roupa", "logistica", "confirmacoes"}

    if contexto in ctx_informativo:
        return texto

    if contexto in ctx_animado:
        extras = ["🎉", "😄", "😉", "🥳", "✨", "💃🕺", "🍾"]
        if not any(e in texto for e in extras):
            texto = f"{texto} {random.choice(extras)}"
        return texto

    return texto

# =====================================================
# 💬 Motor de resposta
# =====================================================
def gerar_resposta(pergunta_raw: str, perfil: dict) -> str:
    pergunta_l = normalizar(pergunta_raw)

    # 1️⃣ — Saudações diretas
    if any(t in pergunta_l for t in ["ola", "olá", "boas", "bom dia", "boa tarde", "boa noite"]):
        respostas = [
            f"Bom ver-te, {perfil['nome']}! Que nunca falte o café nem o champanhe ☕🍾",
            f"Olá, {perfil['nome']}! Pronto para a festa? 🎉",
            f"Boas, {perfil['nome']}! Preparado para dançar? 💃🕺",
            f"{perfil['nome']}, que bom ler-te! Vai ser épico. 🥳",
        ]
        resposta = random.choice(respostas)
        guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil, contexto="saudacao")
        return resposta

    # 2️⃣ — Consultar Qdrant
    intencao = identificar_intencao(pergunta_l)
    resposta_memoria = procurar_resposta_semelhante(pergunta_l, intencao=intencao, limite_conf=0.6, top_k=3)

    if resposta_memoria:
        guardar_mensagem(perfil["nome"], pergunta_l, resposta_memoria, perfil, contexto=intencao)
        return ajustar_tom(resposta_memoria, intencao, perfil)

    # 3️⃣ — Fallback: perguntas básicas
    if any(t in pergunta_l for t in ["como vais", "tudo bem", "como estás", "esta tudo bem"]):
        respostas = [
            f"Estou ótimo, {perfil['nome']}! A preparar-me para a festa 🥳",
            f"Tudo a bombar, {perfil['nome']}! E contigo? 😄",
            f"Melhor agora que falas comigo, {perfil['nome']} 😏",
            f"Por aqui tudo bem, pronto para o champanhe 🍾",
        ]
        resposta = random.choice(respostas)
        guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil, contexto="saudacao")
        return resposta

    # 4️⃣ — Fallback genérico
    respostas_default = [
        "Vai ser uma noite épica 🎉",
        "Só posso dizer que vai haver surpresas 😉",
        "Não revelo tudo, mas vai ser memorável 🎆",
    ]
    resposta = random.choice(respostas_default)
    guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil)
    return resposta

# =====================================================
# 💬 Histórico + Chat
# =====================================================
if "historico" not in st.session_state:
    st.session_state.historico = []

for msg in st.session_state.historico:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Escreve a tua mensagem…")

if prompt:
    with st.chat_message("user"):
        st.markdown(f"**{nome}:** {prompt}")

    with st.spinner("💭 A pensar..."):
        time.sleep(0.3)
        resposta = gerar_resposta(prompt, perfil)

    with st.chat_message("assistant"):
        st.markdown(f"**Assistente:** {resposta}")

    st.session_state.historico.append({"role": "user", "content": f"**{nome}:** {prompt}"})
    st.session_state.historico.append({"role": "assistant", "content": f"**Assistente:** {resposta}"})
