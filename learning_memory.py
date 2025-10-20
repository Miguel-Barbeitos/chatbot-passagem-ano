import json, os, difflib

MEMORY_PATH = "memory.json"

# =====================================================
# 🔧 Funções auxiliares
# =====================================================

def carregar_memoria():
    """Lê o ficheiro de memória local."""
    if not os.path.exists(MEMORY_PATH):
        return {}
    try:
        with open(MEMORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def guardar_memoria(mem):
    """Guarda o dicionário de memória no ficheiro."""
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

def encontrar_pergunta_semelhante(pergunta, mem):
    """Procura se já existe uma pergunta semelhante na memória."""
    for key in mem.keys():
        similarity = difflib.SequenceMatcher(None, key, pergunta).ratio()
        if similarity > 0.8:
            return key
    return None

# =====================================================
# 🧠 Lógica principal
# =====================================================

def atualizar_memoria(pergunta, resposta):
    """
    Atualiza o ficheiro memory.json com novas perguntas e respostas.
    Se uma pergunta semelhante já existir, aumenta o contador.
    """
    mem = carregar_memoria()
    chave_similar = encontrar_pergunta_semelhante(pergunta, mem)

    if chave_similar:
        mem[chave_similar]["vezes"] += 1
        if resposta not in mem[chave_similar]["resposta"]:
            # Mantém a última resposta como referência
            mem[chave_similar]["resposta"] = resposta
        if pergunta not in mem[chave_similar]["perguntas"]:
            mem[chave_similar]["perguntas"].append(pergunta)
    else:
        mem[pergunta] = {
            "perguntas": [pergunta],
            "resposta": resposta,
            "vezes": 1
        }

    guardar_memoria(mem)

def procurar_resposta_memorizada(pergunta):
    """
    Procura se a pergunta tem resposta memorizada.
    Retorna a resposta correspondente se existir.
    """
    mem = carregar_memoria()
    chave = encontrar_pergunta_semelhante(pergunta, mem)
    if chave:
        return mem[chave]["resposta"]
    return None
