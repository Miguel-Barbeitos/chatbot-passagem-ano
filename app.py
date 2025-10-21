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
def regras_fallback(pergunta_l: str) -> tuple[str, str] | tuple[None, None]:
    # identidade
    if any(p in pergunta_l for p in ["como te chamas", "quem es tu", "quem és tu", "qual e o teu nome", "te chamas"]):
        return ("Sou o Diácono Remédios, ao vosso serviço 🙏😄", "saudacao")

    # localização
    if any(p in pergunta_l for p in ["onde", "local", "sitio", "morada", "porto", "fica longe", "localizacao"]):
        return (f"A festa é em **{event.get('local', 'Casa do Miguel, Porto')}**.", "festa")

    # hora
    if any(p in pergunta_l for p in ["hora", "quando", "que horas", "a que horas", "quando comeca", "quando começa"]):
        return (f"Começa às **{event.get('hora', '21h00')}**.", "hora")

    # wifi
    if any(p in pergunta_l for p in ["wifi", "wi fi", "wi-fi", "internet", "rede"]):
        return (f"A senha do Wi-Fi é **{event.get('wifi', 'CasaDoMiguel2025')}**.", "wifi")

    # dress code
    if any(p in pergunta_l for p in ["dress", "roupa", "vestir", "codigo", "cor", "amarelo", "dress code"]):
        dc = event.get("dress_code", "casual elegante")
        return (f"O dress code é **{dc}** e a cor deste ano é **amarelo 💛**.", "roupa")

    # o que levar
    if any(p in pergunta_l for p in ["o que levar", "o que trazer", "preciso levar", "levar algo"]):
        lista = ", ".join(event.get("trazer", ["boa disposição"]))
        return (f"Podes trazer: {lista}.", "logistica")

    return (None, None)
# =====================================================
# 🧠 Função principal — gerar resposta inteligente
# =====================================================
def gerar_resposta(pergunta: str, perfil: dict):
    pergunta_l = normalizar(pergunta)
    intencao = identificar_intencao(pergunta_l)

    # 1️⃣ — Procurar resposta semelhante no Qdrant
    resposta_memoria = procurar_resposta_semelhante(
        pergunta_l, intencao=intencao, limite_conf=0.55, top_k=3
    )

    if resposta_memoria:
        guardar_mensagem(perfil["nome"], pergunta_l, resposta_memoria, perfil, contexto=intencao)
        return ajustar_tom(resposta_memoria, intencao, perfil)

    # 2️⃣ — Regras fixas (fallback rápido)
    resposta_regra, contexto = regras_fallback(pergunta_l)
    if resposta_regra:
        guardar_mensagem(perfil["nome"], pergunta_l, resposta_regra, perfil, contexto)
        return ajustar_tom(resposta_regra, contexto, perfil)

    # 3️⃣ — Confirmações com memória no Qdrant
    if any(p in pergunta_l for p in ["confirmou", "quem vai", "vai à festa", "vai a festa"]):
        try:
            from learning_qdrant import client, models

            resultados = client.scroll(
                collection_name="chatbot_passagem_ano",
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="contexto", match=models.MatchValue(value="confirmacoes"))]
                ),
                limit=200
            )

            confirmados = []
            for ponto in resultados[0]:
                if ponto.payload and "resposta" in ponto.payload:
                    resposta = ponto.payload["resposta"]
                    for nome_c in ["Miguel", "Jojo", "Catarina", "Barbeitos", "Rita", "Pedro"]:
                        if nome_c.lower() in resposta.lower():
                            confirmados.append(nome_c)

            confirmados = list(set(confirmados))  # remover duplicados

            # --- Caso 1: Pergunta genérica
            if any(t in pergunta_l for t in ["quem vai", "quem confirmou", "quantas pessoas", "quem está confirmado"]):
                if confirmados:
                    lista = ", ".join(confirmados)
                    resposta = f"Até agora confirmaram: {lista} 🎉"
                else:
                    resposta = "Ainda ninguém confirmou oficialmente 😅"
                guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil, contexto="confirmacoes")
                return ajustar_tom(resposta, "confirmacoes", perfil)

            # --- Caso 2: Pergunta específica ("a Jojo confirmou?")
            for nome_c in ["Miguel", "Jojo", "Catarina", "Barbeitos", "Rita", "Pedro"]:
                if nome_c.lower() in pergunta_l:
                    if nome_c in confirmados:
                        resposta = f"Sim! {nome_c} já confirmou e está preparad{'o' if nome_c != 'Catarina' else 'a'} para a festa 😄"
                    else:
                        resposta = f"Acho que {nome_c} ainda não confirmou... E tu, {perfil['nome']}, já confirmaste? 😉"
                    guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil, contexto="confirmacoes")
                    return ajustar_tom(resposta, "confirmacoes", perfil)

        except Exception as e:
            print(f"❌ Erro ao verificar confirmações: {e}")

    # 4️⃣ — Saudações diretas (backup)
    if any(t in pergunta_l for t in ["olá", "ola", "bom dia", "boa tarde", "boa noite", "como estás", "tudo bem"]):
        respostas = [
            f"Olá, {perfil['nome']}! Pronto para a festa? 🎉",
            f"Bom ver-te, {perfil['nome']}! Já cheira a champanhe 🍾",
            f"Ei, {perfil['nome']}! Está quase na hora do brinde 🥂",
            f"Olá, {perfil['nome']}! O Diácono está pronto 🙏✨",
        ]
        resposta = random.choice(respostas)
        guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil, contexto="saudacao")
        return ajustar_tom(resposta, "saudacao", perfil)

    # 5️⃣ — Fallback de conversa geral (último recurso)
    respostas_default = [
        "Vai ser uma noite épica 🎉",
        "Só posso dizer que vai haver surpresas 😉",
        "Não revelo tudo, mas vai ser memorável 🎆",
        "A festa promete... mas não posso dar spoilers 😏",
    ]
    resposta = random.choice(respostas_default)
    guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil)
    return ajustar_tom(resposta, "geral", perfil)


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
