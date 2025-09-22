# -*- coding: utf-8 -*-
import json, random, unicodedata, re, sys
from pathlib import Path

BANCO_ARQUIVO = "banco_palavras.json"
MAX_ERROS = 6  # cabeça, tronco, braço esq, braço dir, perna esq, perna dir

FORCA_FASES = [
    # 0 erros
    r"""
     +---+
     |   |
         |
         |
         |
         |
   =========
""",
    # 1 erro
    r"""
     +---+
     |   |
     O   |
         |
         |
         |
   =========
""",
    # 2 erros
    r"""
     +---+
     |   |
     O   |
     |   |
         |
         |
   =========
""",
    # 3 erros
    r"""
     +---+
     |   |
     O   |
    /|   |
         |
         |
   =========
""",
    # 4 erros
    r"""
     +---+
     |   |
     O   |
    /|\  |
         |
         |
   =========
""",
    # 5 erros
    r"""
     +---+
     |   |
     O   |
    /|\  |
    /    |
         |
   =========
""",
    # 6 erros (fim)
    r"""
     +---+
     |   |
     O   |
    /|\  |
    / \  |
         |
   =========
""",
]

def normalizar(txt: str) -> str:
    nfkd = unicodedata.normalize("NFKD", txt)
    s = "".join(c for c in nfkd if not unicodedata.combining(c))
    s = s.upper()
    s = re.sub(r"[^A-Z]", "", s)  # remove espaços, hífens, etc.
    return s

def carregar_banco(caminho=BANCO_ARQUIVO):
    p = Path(caminho)
    if not p.exists():
        print(f"[ERRO] Arquivo {caminho} não encontrado.")
        sys.exit(1)
    dados = json.loads(p.read_text(encoding="utf-8"))
    palavras = dados.get("palavras", [])
    # sanity check
    if not palavras:
        print("[ERRO] Banco vazio.")
        sys.exit(1)
    # agrupar por tema
    por_tema = {}
    for item in palavras:
        tema = item["tema"]
        por_tema.setdefault(tema, []).append(item)
    return por_tema

def escolher_opcao(titulo, opcoes):
    print(f"\n== {titulo} ==")
    for i, o in enumerate(opcoes, 1):
        print(f"{i}. {o}")
    while True:
        escolha = input("Escolha um número: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            return opcoes[int(escolha) - 1]
        print("Ops! Digite um número válido.")

def filtrar_nivel(lista, nivel_escolhido):
    if nivel_escolhido == "TODOS":
        return list(lista)
    return [x for x in lista if x.get("nivel", "A") == nivel_escolhido]

def sortear_palavra(lista, usados_ids):
    elegiveis = [x for x in lista if (x.get("tema",""), x.get("palavra_exibida","")) not in usados_ids]
    if not elegiveis:  # reset se esgotar
        elegiveis = list(lista)
        usados_ids.clear()
    return random.choice(elegiveis)

def mostrar_estado(palavra_exibida, reveladas, erros, tentadas, dica=None):
    print(FORCA_FASES[erros])
    print("Palavra:", " ".join(reveladas))
    print("Tentadas:", " ".join(sorted(tentadas)) if tentadas else "—")
    if dica:
        print("Dica:", dica)
    print("Comandos: '?' para dica | '!' para chutar a palavra inteira | 'sair' para encerrar")

def jogar_partida(item):
    exibida = item["palavra_exibida"].upper()
    alvo = normalizar(item["palavra_exibida"])
    reveladas = ["_" if c.isalpha() else c for c in exibida]
    tentadas = set()
    erros = 0
    dica_mostrada = False

    while True:
        # mostra dica automática após 2 erros
        dica_texto = item.get("dica") if (erros >= 2 or dica_mostrada) else None
        mostrar_estado(exibida, reveladas, erros, tentadas, dica_texto)

        palpite = input("Letra ou comando: ").strip()
        if palpite.lower() == "sair":
            return "sair"
        if palpite == "?":
            dica_mostrada = True
            continue
        if palpite == "!":
            chute = input("Digite seu palpite para a palavra: ").strip()
            if normalizar(chute) == alvo:
                return True
            else:
                print("Quase! Não foi dessa vez.")
                erros += 1
        else:
            if not palpite:
                print("Digite uma letra.")
                continue
            letra = normalizar(palpite)
            if len(letra) != 1:
                print("Digite apenas UMA letra (ou use '!' para chutar a palavra).")
                continue
            if letra in tentadas:
                print("Você já tentou essa letra.")
                continue
            tentadas.add(letra)

            if letra in alvo:
                # revelar posições respeitando acentos na exibida
                for i, ch in enumerate(exibida):
                    if normalizar(ch) == letra:
                        reveladas[i] = ch
                if "_" not in reveladas:
                    return True
                else:
                    print("Boa! Continue assim.")
            else:
                erros += 1
                print("Não tem essa letra. Tente outra.")

        if erros >= MAX_ERROS:
            print(FORCA_FASES[erros])
            print("Puxa! Acabaram as chances.")
            print(f"A palavra era: {exibida}")
            return False

def loop_jogo():
    banco_por_tema = carregar_banco()
    temas = sorted(banco_por_tema.keys())
    usados = set()  # (tema, palavra_exibida)

    print("\n🎉 Bem-vindo ao Jogo da Forca! (versão educativa 6+)")
    while True:
        tema = escolher_opcao("Escolha um tema", temas + ["ALEATÓRIO", "SAIR"])
        if tema == "SAIR":
            print("Até logo! 👋")
            break
        if tema == "ALEATÓRIO":
            tema = random.choice(temas)

        niveis = ["A", "B", "C", "TODOS"]
        nivel = escolher_opcao("Escolha o nível", niveis)

        lista_base = filtrar_nivel(banco_por_tema[tema], nivel)
        if not lista_base:
            print("Não há palavras para esse filtro. Tente outra combinação.")
            continue

        item = sortear_palavra(lista_base, usados)
        resultado = jogar_partida(item)

        if resultado == "sair":
            print("Jogo encerrado. Até a próxima! 👋")
            break

        if resultado is True:
            print(f"Parabéns! Você acertou: {item['palavra_exibida']} 🎉")
        else:
            print("Boa tentativa! Vamos para a próxima. 💪")

        usados.add((item["tema"], item["palavra_exibida"]))

        de_novo = escolher_opcao("Jogar outra?", ["SIM", "NÃO"])
        if de_novo == "NÃO":
            print("Obrigado por jogar! 👋")
            break

if __name__ == "__main__":
    random.seed()  # semente do sistema
    loop_jogo()
