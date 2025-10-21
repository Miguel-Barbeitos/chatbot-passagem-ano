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
# 💬 Regras fixas (fallback rápido)
# =====================================================
def regras_fallback(pergunta_l: str) -> tuple[str, str] | tuple[None, None]:
    if any(p in pergunta_l for p in ["como te chamas", "quem es tu", "quem és tu", "qual e o teu nome", "te chamas"]):
        return ("Sou o Diácono Remédios, ao vosso serviço 🙏😄", "saudacao")

    if any(p in pergunta_l for p in ["onde", "local", "sitio", "morada", "porto", "fica longe", "localizacao"]):
        return (f"A festa é em **{event.get('local', 'Casa do Miguel, Porto')}**.", "festa")

    if any(p in pergunta_l for p in ["hora", "quando", "que horas", "a que horas", "quando comeca", "quando começa"]):
        return (f"Começa às **{event.get('hora', '21h00')}**.", "hora")

    if any(p in pergunta_l for p in ["wifi", "wi fi", "wi-fi", "internet", "rede"]):
        return (f"A senha do Wi-Fi é **{event.get('wifi', 'CasaDoMiguel2025')}**.", "wifi")

    if any(p in pergunta_l for p in ["dress", "roupa", "vestir", "codigo", "cor", "amarelo", "dress code"]):
        dc = event.get("dress_code", "casual elegante")
        return (f"O dress code é **{dc}** e a cor deste ano é **amarelo 💛**.", "roupa")

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

    # ✅ Prioridade para confirmações pendentes
    ultima_intencao = st.session_state.get("ultimo_contexto", "")
    if ultima_intencao == "confirmacoes" and any(
        t in pergunta_l for t in ["confirmo", "confirmar", "eu confirmo", "vou", "sim vou", "claro que vou", "estarei lá", "lá estarei"]
    ):
        resposta = f"Boa! 🎉 Fico feliz por saber que vais, {perfil['nome']}. Já estás na lista!"
        guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil, contexto="confirmacoes")

        try:
            from learning_qdrant import client, models
            client.upsert(
                collection_name="chatbot_passagem_ano",
                points=[
                    models.PointStruct(
                        id=random.randint(0, 1_000_000_000),
                        vector=[0.0] * 768,
                        payload={
                            "user": perfil["nome"],
                            "resposta": f"{perfil['nome']} confirmou presença 🎉",
                            "contexto": "confirmacoes",
                        },
                    )
                ],
            )
            print(f"✅ {perfil['nome']} registado como confirmado no Qdrant.")
        except Exception as e:
            print(f"⚠️ Erro ao gravar confirmação no Qdrant: {e}")

        st.session_state["ultimo_contexto"] = ""
        return ajustar_tom(resposta, "confirmacoes", perfil)

    # 1️⃣ — Procurar resposta semelhante no Qdrant
    resposta_memoria = procurar_resposta_semelhante(pergunta_l, intencao=intencao, limite_conf=0.55, top_k=3)
    if resposta_memoria:
        guardar_mensagem(perfil["nome"], pergunta_l, resposta_memoria, perfil, contexto=intencao)
        st.session_state["ultimo_contexto"] = intencao
        return ajustar_tom(resposta_memoria, intencao, perfil)

    # 2️⃣ — Regras fixas
    resposta_regra, contexto = regras_fallback(pergunta_l)
    if resposta_regra:
        guardar_mensagem(perfil["nome"], pergunta_l, resposta_regra, perfil, contexto)
        st.session_state["ultimo_contexto"] = contexto
        return ajustar_tom(resposta_regra, contexto, perfil)

    # 3️⃣ — Confirmações (quem vai / quem confirmou)
    if (
        any(p in pergunta_l for p in ["confirmou", "quem vai", "vai à festa", "vai a festa", "quem confirmou"])
        and not any(p in pergunta_l for p in ["ganhar", "jogo", "benfica", "porto", "sporting", "resultado"])
    ):
        try:
            from learning_qdrant import client, models

            resultados = client.scroll(
                collection_name="chatbot_passagem_ano",
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="contexto", match=models.MatchValue(value="confirmacoes"))]
                ),
                limit=200,
            )

            confirmados = set()
            for ponto in resultados[0]:
                if ponto.payload:
                    user_payload = ponto.payload.get("user", "").strip().lower()
                    resposta_payload = ponto.payload.get("resposta", "").lower()
                    for nome_c in ["miguel", "jojo", "catarina", "barbeitos", "rita", "pedro"]:
                        if nome_c in user_payload or nome_c in resposta_payload:
                            confirmados.add(nome_c.capitalize())

            st.session_state["ultimo_contexto"] = "confirmacoes"

            # --- Pergunta genérica
            if any(t in pergunta_l for t in ["quem vai", "quem confirmou", "quantas pessoas", "quem está confirmado"]):
                if confirmados:
                    lista = ", ".join(sorted(confirmados))
                    resposta = f"Até agora confirmaram: {lista} 🎉"
                else:
                    resposta = f"Ainda ninguém confirmou oficialmente 😅 E tu, {perfil['nome']}, já confirmaste?"
                guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil, contexto="confirmacoes")
                return ajustar_tom(resposta, "confirmacoes", perfil)

            # --- Pergunta específica
            for nome_c in ["miguel", "jojo", "catarina", "barbeitos", "rita", "pedro"]:
                if nome_c in pergunta_l:
                    if nome_c.capitalize() in confirmados:
                        resposta = f"Sim! {nome_c.capitalize()} já confirmou e está preparad{'o' if nome_c != 'catarina' else 'a'} para a festa 😄"
                    else:
                        resposta = f"Acho que {nome_c.capitalize()} ainda não confirmou... E tu, {perfil['nome']}, já confirmaste? 😉"
                    guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil, contexto="confirmacoes")
                    return ajustar_tom(resposta, "confirmacoes", perfil)

        except Exception as e:
            print(f"❌ Erro ao verificar confirmações: {e}")

    # 4️⃣ — Saudações
    if any(t in pergunta_l for t in ["olá", "ola", "bom dia", "boa tarde", "boa noite", "como estás", "tudo bem"]):
        respostas = [
            f"Olá, {perfil['nome']}! Pronto para a festa? 🎉",
            f"Bom ver-te, {perfil['nome']}! Já cheira a champanhe 🍾",
            f"Ei, {perfil['nome']}! Está quase na hora do brinde 🥂",
            f"Olá, {perfil['nome']}! O Diácono está pronto 🙏✨",
        ]
        resposta = random.choice(respostas)
        guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil, contexto="saudacao")
        st.session_state["ultimo_contexto"] = "saudacao"
        return ajustar_tom(resposta, "saudacao", perfil)

    # 5️⃣ — Fallback
    respostas_default = [
        "Vai ser uma noite épica 🎉",
        "Só posso dizer que vai haver surpresas 😉",
        "Não revelo tudo, mas vai ser memorável 🎆",
        "A festa promete... mas não posso dar spoilers 😏",
    ]
    resposta = random.choice(respostas_default)
    guardar_mensagem(perfil["nome"], pergunta_l, resposta, perfil)
    st.session_state["ultimo_contexto"] = "geral"
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
