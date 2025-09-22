# -*- coding: utf-8 -*-
import json, random, re, unicodedata, sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

ARQ_BANCO = "banco_palavras.json"
MAX_ERROS = 6

def normalizar(txt: str) -> str:
    nfkd = unicodedata.normalize("NFKD", txt)
    s = "".join(c for c in nfkd if not unicodedata.combining(c))
    s = s.upper()
    s = re.sub(r"[^A-Z]", "", s)  # remove espaço, hífen, pontuação
    return s

class ForcaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jogo da Forca - versão gráfica (educativo 6+)")
        self.geometry("900x640")
        self.minsize(860, 600)

        self.banco_por_tema = self._carregar_banco()
        self.temas = sorted(self.banco_por_tema.keys())
        self.niveis = ["A", "B", "C", "TODOS"]

        # estado da partida
        self.usados = set()  # (tema, palavra_exibida)
        self.item_atual = None
        self.alvo = ""
        self.exibida = ""
        self.reveladas = []
        self.tentadas = set()
        self.erros = 0
        self.dica_mostrada = False

        self._montar_ui()
        self._novo_jogo(auto=True)

    # ===== dados =====
    def _carregar_banco(self):
        p = Path(ARQ_BANCO)
        if not p.exists():
            messagebox.showerror("Erro", f"Arquivo {ARQ_BANCO} não encontrado.")
            self.destroy()
            sys.exit(1)
        dados = json.loads(p.read_text(encoding="utf-8"))
        palavras = dados.get("palavras", [])
        if not palavras:
            messagebox.showerror("Erro", "Banco de palavras está vazio.")
            self.destroy()
            sys.exit(1)
        por_tema = {}
        for it in palavras:
            por_tema.setdefault(it["tema"], []).append(it)
        return por_tema

    def _filtrar(self, tema, nivel):
        base = list(self.banco_por_tema.get(tema, []))
        if nivel != "TODOS":
            base = [x for x in base if x.get("nivel","A") == nivel]
        elegiveis = [x for x in base if (x["tema"], x["palavra_exibida"]) not in self.usados]
        if not elegiveis:  # se esgotar, reinicia rotação daquele filtro
            self.usados = {(t,p) for (t,p) in self.usados if t != tema}
            elegiveis = list(base)
        return elegiveis

    # ===== UI =====
    def _montar_ui(self):
        # top: filtros
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Tema:").pack(side="left")
        self.cb_tema = ttk.Combobox(top, values=self.temas + ["ALEATÓRIO"], state="readonly", width=20)
        self.cb_tema.current(0)
        self.cb_tema.pack(side="left", padx=6)

        ttk.Label(top, text="Nível:").pack(side="left")
        self.cb_nivel = ttk.Combobox(top, values=self.niveis, state="readonly", width=10)
        self.cb_nivel.current(3)  # TODOS
        self.cb_nivel.pack(side="left", padx=6)

        self.bt_novo = ttk.Button(top, text="Nova palavra", command=self._novo_jogo)
        self.bt_novo.pack(side="left", padx=8)

        self.bt_dica = ttk.Button(top, text="Dica", command=self._mostrar_dica)
        self.bt_dica.pack(side="left", padx=8)

        self.bt_chutar = ttk.Button(top, text="Chutar palavra", command=self._chutar_palavra)
        self.bt_chutar.pack(side="left", padx=8)

        # meio: layout com canvas (forca) + painel info
        main = ttk.Frame(self, padding=(10,0,10,10))
        main.pack(fill="both", expand=True)

        # Canvas para desenho
        self.canvas = tk.Canvas(main, bg="#FAFAFA", width=420, height=420, highlightthickness=1, highlightbackground="#DDD")
        self.canvas.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0,10), pady=(0,10))

        # Palavra e info
        info = ttk.Frame(main)
        info.grid(row=0, column=1, sticky="nsew")

        self.lbl_palavra = ttk.Label(info, text="_ _ _ _", font=("Helvetica", 28, "bold"))
        self.lbl_palavra.pack(anchor="w", pady=(0,10))

        self.lbl_dica = ttk.Label(info, text="Dica: —", font=("Helvetica", 12))
        self.lbl_dica.pack(anchor="w", pady=(0,10))

        self.lbl_tentadas = ttk.Label(info, text="Letras tentadas: —", font=("Helvetica", 12))
        self.lbl_tentadas.pack(anchor="w", pady=(0,10))

        self.lbl_status = ttk.Label(info, text="", font=("Helvetica", 12))
        self.lbl_status.pack(anchor="w", pady=(0,10))

        # teclado
        kb = ttk.Frame(main)
        kb.grid(row=1, column=1, sticky="nsew")

        # linhas de botões A-Z
        letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.botoes_letra = {}
        linhas = [letras[:10], letras[10:19], letras[19:]]
        for r, seq in enumerate(linhas):
            fr = ttk.Frame(kb)
            fr.pack(anchor="w", pady=4)
            for ch in seq:
                b = ttk.Button(fr, text=ch, width=3, command=lambda c=ch: self._tentar_letra(c))
                b.pack(side="left", padx=2, pady=2)
                self.botoes_letra[ch] = b

        # rodapé
        rodape = ttk.Frame(self, padding=(10,0,10,10))
        rodape.pack(fill="x")
        self.lbl_rodape = ttk.Label(rodape, text="Jogo da Forca • Educação Infantil • Use as letras ou chute a palavra inteira.")
        self.lbl_rodape.pack(anchor="w")

        # grid weights
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=0)
        main.rowconfigure(1, weight=1)

        # estilo
        style = ttk.Style(self)
        try:
            self.tk.call("source", "sun-valley.tcl")
            style.theme_use("sun-valley")
        except Exception:
            pass

    # ===== lógica da partida =====
    def _novo_jogo(self, auto=False):
        tema = self.cb_tema.get()
        if tema == "" or tema not in self.temas + ["ALEATÓRIO"]:
            tema = self.temas[0]
        if tema == "ALEATÓRIO":
            tema = random.choice(self.temas)
        nivel = self.cb_nivel.get() or "TODOS"

        lista = self._filtrar(tema, nivel)
        if not lista:
            messagebox.showinfo("Atenção", "Não há palavras para esse filtro. Escolha outro tema/nível.")
            return

        self.item_atual = random.choice(lista)
        self.usados.add((self.item_atual["tema"], self.item_atual["palavra_exibida"]))

        self.exibida = self.item_atual["palavra_exibida"].upper()
        self.alvo = normalizar(self.exibida)
        self.reveladas = ["_" if c.isalpha() else c for c in self.exibida]
        self.tentadas = set()
        self.erros = 0
        self.dica_mostrada = False

        self._habilitar_teclado(True)
        self._atualizar_ui()

        if not auto:
            self._info_status("Nova palavra escolhida. Boa sorte!")

    def _tentar_letra(self, ch):
        letra = normalizar(ch)
        if not letra or len(letra) != 1:
            return
        if letra in self.tentadas:
            self._info_status("Você já tentou essa letra.")
            return
        self.tentadas.add(letra)
        self._atualizar_tentadas()

        if letra in self.alvo:
            # revela preservando acentos
            for i, c in enumerate(self.exibida):
                if normalizar(c) == letra:
                    self.reveladas[i] = c
            self._info_status("Boa! Continue assim.")
            self._atualizar_palavra()
            if "_" not in self.reveladas:
                self._vitoria()
        else:
            self.erros += 1
            self._info_status("Não tem essa letra. Tente outra.")
            self._desenhar_forca()
            if self.erros >= MAX_ERROS:
                self._derrota()

        # desabilita botão da letra usada
        btn = self.botoes_letra.get(letra)
        if btn:
            btn.configure(state="disabled")

    def _chutar_palavra(self):
        if not self.item_atual:
            return
        chute = simpledialog.askstring("Chutar palavra", "Digite seu palpite:")
        if chute is None:
            return
        if normalizar(chute) == self.alvo:
            self._vitoria()
        else:
            self.erros += 1
            self._info_status("Quase! Não foi dessa vez.")
            self._desenhar_forca()
            if self.erros >= MAX_ERROS:
                self._derrota()

    def _mostrar_dica(self):
        self.dica_mostrada = True
        self._atualizar_dica(force=True)

    def _vitoria(self):
        self._habilitar_teclado(False)
        self._atualizar_palavra(force_full=True)
        messagebox.showinfo("Parabéns!", f"Você acertou: {self.exibida} 🎉")
        self._info_status("Vitória! Clique em 'Nova palavra' para continuar.")

    def _derrota(self):
        self._habilitar_teclado(False)
        self._atualizar_palavra(force_full=True)
        messagebox.showinfo("Boa tentativa!", f"A palavra era: {self.exibida}")
        self._info_status("Fim das chances. Clique em 'Nova palavra' para tentar outra.")

    # ===== UI helpers =====
    def _habilitar_teclado(self, status: bool):
        for b in self.botoes_letra.values():
            b.configure(state=("normal" if status else "disabled"))
        if status:
            # reabilita todas
            for ch, b in self.botoes_letra.items():
                b.configure(state="normal")

    def _atualizar_ui(self):
        self._atualizar_palavra()
        self._atualizar_dica()
        self._atualizar_tentadas()
        self._desenhar_forca(reset=True)

    def _atualizar_palavra(self, force_full=False):
        if force_full:
            texto = " ".join(list(self.exibida))
        else:
            texto = " ".join(self.reveladas)
        self.lbl_palavra.configure(text=texto)

    def _atualizar_dica(self, force=False):
        if force or self.dica_mostrada or self.erros >= 2:
            self.lbl_dica.configure(text=f"Dica: {self.item_atual.get('dica','—')}")
        else:
            self.lbl_dica.configure(text="Dica: —")

    def _atualizar_tentadas(self):
        if self.tentadas:
            s = " ".join(sorted(self.tentadas))
        else:
            s = "—"
        self.lbl_tentadas.configure(text=f"Letras tentadas: {s}")

    def _info_status(self, msg):
        self.lbl_status.configure(text=msg)

    # ===== desenho da forca =====
    def _desenhar_forca(self, reset=False):
        c = self.canvas
        c.delete("all")
        # base da forca
        c.create_line(40, 380, 200, 380, width=6)
        c.create_line(90, 380, 90, 60, width=6)
        c.create_line(90, 60, 260, 60, width=6)
        c.create_line(260, 60, 260, 100, width=6)  # corda
        if reset:
            return
        e = self.erros
        # 1 cabeça
        if e >= 1:
            c.create_oval(230, 100, 290, 160, width=4)  # cabeça
        # 2 tronco
        if e >= 2:
            c.create_line(260, 160, 260, 240, width=4)  # tronco
        # 3 braço esq
        if e >= 3:
            c.create_line(260, 180, 230, 210, width=4)
        # 4 braço dir
        if e >= 4:
            c.create_line(260, 180, 290, 210, width=4)
        # 5 perna esq
        if e >= 5:
            c.create_line(260, 240, 235, 290, width=4)
        # 6 perna dir
        if e >= 6:
            c.create_line(260, 240, 285, 290, width=4)

if __name__ == "__main__":
    random.seed()
    app = ForcaApp()
    app.mainloop()
