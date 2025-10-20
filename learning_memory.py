import json, os, difflib

MEMORY_PATH = "memory.json"

def carregar_memoria():
    if not os.path.exists(MEMORY_PATH):
        return {}
    with open(MEMORY_PATH, encoding="utf-8") as f:
        return json.load(f)

def guardar_memoria(mem):
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

def atualizar_memoria(pergunta, resposta):
    mem = carregar_memoria()
    chave_similar = encontrar_pergunta_semelhante(pergunta, mem)
    if chave_similar:
        mem[chave_similar]["vezes"] += 1
        if resposta not in mem[chave_similar]["resposta"]:
            mem[chave_similar]["resposta"] = resposta
    else:
        mem[pergunta] = {"perguntas": [pergunta], "resposta": resposta, "vezes": 1}
    guardar_memoria(mem)

def encontrar_pergunta_semelhante(pergunta, mem):
    for key in mem.keys():
        similarity = difflib.SequenceMatcher(None, key, pergunta).ratio()
        if similarity > 0.8:
            return key
    return None

def procurar_resposta_memorizada(pergunta):
    mem = carregar_memoria()
    chave = encontrar_pergunta_semelhante(pergunta, mem)
    if chave:
        return mem[chave]["resposta"]
    return None
