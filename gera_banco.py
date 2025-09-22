# -*- coding: utf-8 -*-
"""
Gera banco de 200 palavras para o jogo de forca (pt-BR) em JSON.

Campos por item:
- tema
- palavra_exibida
- forma_normalizada (sem acentos/hífens/espaços)
- nivel (A/B/C)
- dica (curta e infantil)
"""
import json
import re
import unicodedata
from pathlib import Path

def normalizar(palavra: str) -> str:
    # Remove acentos e caracteres não A-Z (ex.: espaços, hífens)
    nfkd = unicodedata.normalize("NFKD", palavra)
    s = "".join(c for c in nfkd if not unicodedata.combining(c))
    s = s.upper()
    s = re.sub(r"[^A-Z]", "", s)
    return s

def tem_acento_ou_composto(palavra: str) -> bool:
    # Se a palavra exibida perder algo ao normalizar OU contém hífen/espaço
    return bool(re.search(r"[À-ÿ\- ]", palavra))

def definir_nivel(palavra_exibida: str) -> str:
    base = normalizar(palavra_exibida)
    n = len(base)
    composto = tem_acento_ou_composto(palavra_exibida)
    # Heurística simples e conservadora para 6 anos
    if n <= 4 and not composto:
        return "A"
    if 5 <= n <= 6 and not composto:
        return "A"  # ainda amigável (ex.: LIVRO, MANGA)
    if composto and n <= 6:
        return "B"
    if composto and n > 6:
        return "C"
    if n >= 7:
        return "B"
    return "A"

def dica_padrao(tema: str, palavra: str) -> str:
    t = tema.lower()
    p = palavra.upper()
    if t == "animais":
        return "É um animal conhecido pelas crianças."
    if t == "frutas":
        return "É uma fruta gostosa e colorida."
    if t == "escola":
        return "Objeto ou ideia usada na escola."
    if t == "casa":
        return "Objeto comum que existe em casa."
    if t == "brinquedos":
        return "É um brinquedo para se divertir."
    if t == "natureza":
        return "Algo que vemos na natureza."
    if t == "cores":
        return "É uma cor."
    if t == "corpo":
        return "Parte do corpo."
    return "Palavra do cotidiano infantil."

# =========================
# LISTAS APROVADAS (200)
# =========================

palavras_por_tema = {
    # 100 iniciais
    "animais": [
        "CÃO","GATO","PATO","RATO","SAPO","PEIXE","CAVALO","LEÃO","LOBO","URSO",
        "VACA","GALINHA","PORCO","MACACO","TIGRE","ELEFANTE","COELHO","BORBOLETA","FORMIGA","TARTARUGA"
    ],
    "frutas": [
        "BANANA","MAÇÃ","PERA","UVA","LIMÃO","LARANJA","MELÃO","MELANCIA","ABACAXI","COCO",
        "GOIABA","MANGA","KIWI","MORANGO","CEREJA"
    ],
    "escola": [
        "LIVRO","CADERNO","LÁPIS","CANETA","RÉGUA","BORRACHA","QUADRO","GIZ","MESA","CADEIRA",
        "MOCHILA","PROFESSOR","ESCOLA","PAPEL","TINTA"
    ],
    "casa": [
        "PORTA","JANELA","CAMA","SOFÁ","TELEVISÃO","MESA","CADEIRA","LUZ","COPO","PRATO",
        "FACA","COLHER","GARFO","TAPETE","ESPELHO"
    ],
    "brinquedos": [
        "BOLA","BONECA","PIÃO","URSINHO","CARRINHO","QUEBRA-CABEÇA","AVIÃO","BLOCO","BALÃO","PIPA"  # KITE -> PIPA
    ],
    "natureza": [
        "ÁRVORE","FLOR","SOL","LUA","ESTRELA","CÉU","MAR","PEDRA","RIO","NUVEM"
    ],
    "cores": [
        "AZUL","VERMELHO","VERDE","AMARELO","ROSA"
    ],
    "corpo": [
        "MÃO","PÉ","OLHO","BOCA","NARIZ","ORELHA","CABELO","DENTE","BARRIGA","PERNA"
    ],

    # +50 extras (1º lote)
    "animais_extra1": [
        "CAMELO","ZEBRA","JACARÉ","TUCANO","PINGUIM","GIRAFA","CORUJA","LAGARTO","ARARA","CAVALO-MARINHO"
    ],
    "frutas_extra1": [
        "AMEIXA","FIGO","CAJU","PITANGA","JABUTICABA","MARACUJÁ","FRAMBOESA"
    ],
    "escola_extra1": [
        "TESOURA","COLA","LIVRARIA","LANCHE","QUADRO-NEGRO","GLOBO","MAPA"
    ],
    "casa_extra1": [
        "ARMÁRIO","GELADEIRA","FOGÃO","PANELAS","COZINHA","QUARTO","COBERTOR","ALMOFADA"
    ],
    "brinquedos_extra1": [
        "DOMINÓ","PATINS","SKATE","TRENZINHO","CUBO","CARRINHOS"
    ],
    "natureza_extra1": [
        "VENTO","CHUVA","RELVA","AREIA","MONTANHA","FLORESTA"
    ],
    "corpo_extra1": [
        "BRAÇO","DEDO","UNHA","COSTA","PESCOÇO","JOELHO"
    ],

    # +50 extras (2º lote) com ajustes:
    # - SAPINHO removido (sem reposição dedicada)
    # - GUAVA -> AMEIXA (pode repetir com a já existente)
    # - LIÇÃO -> TAREFA
    # - CARRINHÃO -> CARRINHO-DE-MÃO
    # - ARENITO removido e substituição PEDREGULHO eliminada (ficamos -1 no lote, como combinado)
    "animais_extra2": [
        "POLVO","CAMARÃO","CANGURU","GALO","BEIJA-FLOR","MOSCA","CARACOL","TATU","PAVÃO", "FOCA"  # 9 itens (SAPINHO removido)
    ],
    "frutas_extra2": [
        "TANGERINA","GRAVIOLA","CUPUAÇU","PÊSSEGO","DAMASCO","ACEROLA","AMEIXA"  # GUAVA -> AMEIXA
    ],
    "escola_extra2": [
        "APAGADOR","ESTOJO","TAREFA","GIZ DE CERA","LAPISEIRA","LIVRINHO","APONTADOR"  # LIÇÃO -> TAREFA
    ],
    "casa_extra2": [
        "CHAVE","CORTINA","TRAVESSEIRO","QUADRO","ABANADOR","TELEFONE","BANHEIRO"
    ],
    "brinquedos_extra2": [
        "BAMBOLÊ","CARRINHO-DE-MÃO","JOGO","CARTAS","PATINETE","BICICLETA"  # CARRINHÃO -> CARRINHO-DE-MÃO
    ],
    "natureza_extra2": [
        "TERRA","LAGO","DESERTO","ILHA","CACHOEIRA", "PRAIA"  # ARENITO removido; PEDREGULHO eliminado
    ],
    "corpo_extra2": [
        "OMBRO","COTOVELO","COSTELA","LÁBIO","PULSO","TORNOZELO","CORAÇÃO"
    ],
}

# Unir todas as listas em um único dicionário por tema "final"
mapa_temas = {
    "animais": ["animais", "animais_extra1", "animais_extra2"],
    "frutas": ["frutas", "frutas_extra1", "frutas_extra2"],
    "escola": ["escola", "escola_extra1", "escola_extra2"],
    "casa": ["casa", "casa_extra1", "casa_extra2"],
    "brinquedos": ["brinquedos", "brinquedos_extra1", "brinquedos_extra2"],
    "natureza": ["natureza", "natureza_extra1", "natureza_extra2"],
    "cores": ["cores"],  # sem extras
    "corpo": ["corpo", "corpo_extra1", "corpo_extra2"],
}

# Montar lista final preservando exatamente a contagem acordada (inclui possíveis duplicatas intencionais)
lista_final = []
for tema_final, chaves in mapa_temas.items():
    for chave in chaves:
        for palavra in palavras_por_tema.get(chave, []):
            registro = {
                "tema": tema_final,
                "palavra_exibida": palavra.upper(),
                "forma_normalizada": normalizar(palavra),
                "nivel": definir_nivel(palavra),
                "dica": dica_padrao(tema_final, palavra),
            }
            lista_final.append(registro)

# Conferências
total = len(lista_final)
temas_contagem = {}
for item in lista_final:
    temas_contagem[item["tema"]] = temas_contagem.get(item["tema"], 0) + 1

print("Total de itens:", total)
print("Distribuição por tema:", temas_contagem)

assert total == 200, f"Contagem final diferente de 200 (obtido: {total})"

# Empacotar com metadados
banco = {
    "versao": "1.0.0",
    "idioma": "pt-BR",
    "fonte": "curadoria_interna",
    "palavras": lista_final
}

# Salvar
saida = Path("banco_palavras.json")
saida.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Arquivo salvo em: {saida.resolve()}")
