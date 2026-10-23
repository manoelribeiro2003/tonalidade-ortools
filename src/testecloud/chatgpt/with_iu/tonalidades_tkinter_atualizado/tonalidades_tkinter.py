"""Interface Tkinter para o otimizador divisao_tonalidades_ergonomico.py.

Deixe este arquivo na mesma pasta de divisao_tonalidades_ergonomico.py.
Dependência: pip install ortools
Execução: python tonalidades_tkinter.py
"""
from __future__ import annotations
import contextlib
import importlib.util
import io
import json
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter

BASE_DIR = Path(__file__).resolve().parent
ALGORITHM_PATH = BASE_DIR / "divisao_tonalidades_ergonomico.py"
spec = importlib.util.spec_from_file_location("algoritmo_tonalidades", ALGORITHM_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Não foi possível carregar {ALGORITHM_PATH}")
alg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alg)

COLS_DEMANDA = ("tamanho", "pares")
COLS_NAV = ("componente", "tamanho", "largura1", "comprimento1", "largura2", "comprimento2", "pares")
COLS_TOM = ("tom", "metros")
WORK_VERSION = 1

class TonalidadesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tonalidades — Planejamento de corte")
        self.geometry("1180x790")
        self.minsize(980, 650)
        self._build_ui()
        self._populate_example_rows()

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Hint.TLabel", foreground="#555555")
        style.configure("Treeview", rowheight=25)

        top = ttk.Frame(self, padding=(14, 12, 14, 8))
        top.pack(fill="x")
        ttk.Label(top, text="Planejamento de tonalidades", style="Title.TLabel").pack(anchor="w")
        ttk.Label(top, text="Informe a demanda, as dimensões das navalhas e o estoque. O cálculo usa o algoritmo ergonômico existente.", style="Hint.TLabel", wraplength=1080).pack(anchor="w", pady=(4, 0))

        settings = ttk.LabelFrame(self, text="Parâmetros de corte", padding=10)
        settings.pack(fill="x", padx=14, pady=(0, 8))
        self.width_var = tk.StringVar(value="139")
        self.margin_var = tk.StringVar(value="1")
        self.loss_var = tk.StringVar(value="1")
        self.gap_var = tk.StringVar(value="0")
        self.extra_int_var = tk.StringVar(value="0.3")
        self.extra_ext_var = tk.StringVar(value="0.3")
        fields = [
            ("Largura da mesa (cm)", self.width_var),
            ("Margem de segurança (cm)", self.margin_var),
            ("Perda por trocas (%)", self.loss_var),
            ("Folga entre navalhas (cm)", self.gap_var),
            ("Acréscimo interna (cm)", self.extra_int_var),
            ("Acréscimo externa (cm)", self.extra_ext_var),
        ]
        for i, (label, var) in enumerate(fields):
            col = i % 4
            row = i // 4
            cell = ttk.Frame(settings)
            cell.grid(row=row, column=col, sticky="ew", padx=(0, 12), pady=3)
            ttk.Label(cell, text=label).pack(anchor="w")
            ttk.Entry(cell, textvariable=var, width=14).pack(anchor="w", pady=(2, 0))
            settings.columnconfigure(col, weight=1)

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=5)
        self.demand_tab = ttk.Frame(self.tabs, padding=8)
        self.nav_tab = ttk.Frame(self.tabs, padding=8)
        self.stock_tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(self.demand_tab, text="Demanda por tamanho")
        self.tabs.add(self.nav_tab, text="Navalhas")
        self.tabs.add(self.stock_tab, text="Estoque do almoxarifado")
        self.demand_tree = self._make_table(self.demand_tab, COLS_DEMANDA, {"tamanho":"Tamanho", "pares":"Pares a produzir"}, {"tamanho":180, "pares":180})
        self.nav_tree = self._make_table(self.nav_tab, COLS_NAV, {"componente":"Componente", "tamanho":"Tamanho", "largura1":"Largura 1 (cm)", "comprimento1":"Comprimento 1 (cm)", "largura2":"Largura 2 (cm)", "comprimento2":"Comprimento 2 (cm)", "pares":"Pares por batida"}, {"componente":170, "tamanho":85, "largura1":115, "comprimento1":135, "largura2":115, "comprimento2":135, "pares":130})
        self.stock_tree = self._make_table(self.stock_tab, COLS_TOM, {"tom":"Tonalidade", "metros":"Estoque (m)"}, {"tom":220, "metros":220})
        self._table_controls(self.demand_tab, self.demand_tree, "tamanho")
        self._table_controls(self.nav_tab, self.nav_tree, "componente")
        self._table_controls(self.stock_tab, self.stock_tree, "tom")
        ttk.Label(self.nav_tab, text="Informe Largura 1 e Comprimento 1. Para encaixe transversal, preencha também Largura 2 (menor ou igual à Largura 1) em todos os tamanhos daquele componente. Comprimento 2 é opcional e só deve ser preenchido quando o modelo longitudinal de encaixe for aplicável. Cada componente/tamanho precisa de uma navalha cadastrada.", style="Hint.TLabel", wraplength=1000).pack(anchor="w", pady=(8, 0))

        bottom = ttk.Frame(self, padding=(14, 8, 14, 14))
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Restaurar trabalho", command=self._restore_work).pack(side="left")
        ttk.Button(bottom, text="Salvar trabalho", command=self._save_work).pack(side="left", padx=8)
        ttk.Button(bottom, text="Exportar resultado JSON", command=self._export_json).pack(side="left")
        ttk.Button(bottom, text="Exportar planilha Excel", command=self._export_excel).pack(side="left", padx=8)
        ttk.Button(bottom, text="Executar otimização", command=self._solve).pack(side="right")
        self.status_var = tk.StringVar(value="Pronto para receber os dados.")
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=(8, 4)).pack(fill="x", side="bottom")
        self.result = None
        self.last_config = None

    def _make_table(self, parent, columns, headings, widths):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
        vs = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hs = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], minwidth=80, anchor="w")
        tree.bind("<Double-1>", lambda event, tr=tree: self._edit_cell(event, tr))
        # A tecla Delete exclui apenas as linhas selecionadas nesta tabela.
        tree.bind("<Delete>", lambda event, tr=tree: self._delete_rows_from_key(event, tr))
        # Ctrl+V cola dados copiados do Excel sempre no final, sem sobrescrever.
        tree.bind("<Control-v>", lambda event, tr=tree: self._paste_rows_from_clipboard(event, tr))
        tree.bind("<Control-V>", lambda event, tr=tree: self._paste_rows_from_clipboard(event, tr))
        tree.bind("<Shift-Insert>", lambda event, tr=tree: self._paste_rows_from_clipboard(event, tr))
        return tree

    def _table_controls(self, parent, tree, keycol):
        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=(8, 0))
        ttk.Button(controls, text="Adicionar linha", command=lambda: self._add_row(tree)).pack(side="left")
        ttk.Button(controls, text="Excluir selecionada(s)", command=lambda: self._delete_rows(tree)).pack(side="left", padx=8)
        ttk.Label(controls, text="Dica: duplo clique edita; Ctrl+V cola do Excel no final da tabela.", style="Hint.TLabel").pack(side="right")

    def _edit_cell(self, event, tree):
        item = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)
        if not item or not col_id:
            return
        idx = int(col_id[1:]) - 1
        col = tree["columns"][idx]
        box = tree.bbox(item, col_id)
        if not box:
            return
        x, y, w, h = box
        old = tree.set(item, col)
        editor = ttk.Entry(tree)
        editor.place(x=x, y=y, width=w, height=h)
        editor.insert(0, old)
        editor.select_range(0, "end")
        editor.focus_set()
        def save(_event=None):
            value = editor.get().strip()
            vals = list(tree.item(item, "values"))
            vals[idx] = value
            tree.item(item, values=vals)
            editor.destroy()
        editor.bind("<Return>", save)
        editor.bind("<FocusOut>", save)
        editor.bind("<Escape>", lambda _e: editor.destroy())

    def _add_row(self, tree):
        """Adiciona uma linha vazia para preenchimento manual."""
        tree.insert("", "end", values=("",) * len(tree["columns"]))
        self.status_var.set("Linha adicionada. Dê duplo clique nas células para preencher os valores.")

    def _paste_rows_from_clipboard(self, event, tree):
        """Acrescenta ao final da tabela os dados tabulares copiados para a área de transferência."""
        try:
            clipboard = self.clipboard_get()
        except tk.TclError:
            self.status_var.set("A área de transferência está vazia ou não contém texto.")
            return "break"

        # O Excel usa tabulações entre colunas e quebras de linha entre registros.
        clipboard = clipboard.replace("\r\n", "\n").replace("\r", "\n")
        rows = clipboard.split("\n")
        # Ignora apenas as linhas vazias finais que o Excel pode incluir ao copiar.
        while rows and not rows[-1].strip():
            rows.pop()
        if not rows:
            self.status_var.set("Nenhuma linha preenchida foi encontrada para colar.")
            return "break"

        columns_count = len(tree["columns"])
        parsed_rows = [row.split("\t") for row in rows]
        if any(len(row) > columns_count for row in parsed_rows):
            messagebox.showwarning(
                "Colagem não realizada",
                f"Os dados copiados têm mais de {columns_count} colunas, mas esta tabela possui {columns_count}.\n"
                "Copie apenas as colunas correspondentes a esta tabela.",
                parent=self,
            )
            return "break"

        # Colar nunca substitui linhas existentes: cada registro é acrescentado abaixo do último.
        inserted = 0
        for row in parsed_rows:
            values = [value.strip() for value in row]
            values.extend([""] * (columns_count - len(values)))
            if not any(values):
                continue
            tree.insert("", "end", values=tuple(values))
            inserted += 1

        if inserted:
            self.status_var.set(f"{inserted} linha(s) colada(s) no final da tabela. Os dados existentes foram mantidos.")
        else:
            self.status_var.set("Nenhuma linha preenchida foi encontrada para colar.")
        return "break"

    def _populate_example_rows(self):
        """Preenche a interface com exemplos didáticos, sem ler arquivos externos."""
        for tree in (self.demand_tree, self.nav_tree, self.stock_tree):
            tree.delete(*tree.get_children())

        # Uma linha ilustrativa por tabela, definida no próprio código.
        # O usuário deve substituir ou excluir os valores conforme seu corte.
        self.demand_tree.insert("", "end", values=("38", "20"))
        self.nav_tree.insert("", "end", values=("gaspea_interna", "38", "25.0", "17.0", "", "", "1"))
        self.stock_tree.insert("", "end", values=("tom 1", "20"))

        self.width_var.set("139")
        self.margin_var.set("1")
        self.loss_var.set("1")
        self.gap_var.set("0")
        self.extra_int_var.set("0.3")
        self.extra_ext_var.set("0.3")
        self.result = None
        self.last_config = None
        self.status_var.set("Exemplos ilustrativos na tela — substitua-os pelos dados reais antes de otimizar. Nenhum JSON de exemplo é necessário.")

    def _delete_rows(self, tree):
        selecionadas = tree.selection()
        for item in selecionadas:
            tree.delete(item)
        if selecionadas:
            self.status_var.set(f"{len(selecionadas)} linha(s) excluída(s).")

    def _delete_rows_from_key(self, event, tree):
        """Permite excluir as linhas selecionadas com Delete na tabela em foco."""
        if tree.selection():
            self._delete_rows(tree)
        # Impede que o evento seja tratado por outro binding do Tkinter.
        return "break"

    def _current_snapshot(self):
        """Captura as entradas, os parâmetros usados e o resultado, se houver."""
        try:
            configuracao_atual = self._read_inputs()
        except Exception:
            # Se já existe uma otimização válida, ainda permitimos salvar
            # exatamente o trabalho calculado, mesmo que a tela tenha sido
            # parcialmente editada depois da execução.
            if not (self.result and isinstance(self.last_config, dict)):
                raise
            configuracao_atual = self.last_config

        configuracao_otimizada = self.last_config if self.result else None
        return {
            "formato": "tonalidades-trabalho",
            "versao": WORK_VERSION,
            "configuracao_atual": configuracao_atual,
            "configuracao_otimizada": configuracao_otimizada,
            "resultado": self.result,
        }

    def _save_work(self):
        """Salva entradas, parâmetros e resultado da otimização em um único JSON."""
        try:
            snapshot = self._current_snapshot()
        except Exception as exc:
            messagebox.showerror("Não foi possível salvar", f"Confira os dados antes de salvar o trabalho.\n\n{exc}", parent=self)
            return

        path = filedialog.asksaveasfilename(
            parent=self,
            title="Salvar trabalho do Tonalidades",
            defaultextension=".json",
            filetypes=[("Trabalho Tonalidades (JSON)", "*.json")],
            initialfile="trabalho_tonalidades.json",
        )
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("Trabalho salvo", f"Dados de entrada, parâmetros e resultado foram salvos em:\n{path}", parent=self)
            self.status_var.set(f"Trabalho salvo: {Path(path).name}")
        except Exception as exc:
            messagebox.showerror("Erro ao salvar", f"Não foi possível salvar o trabalho:\n{exc}", parent=self)

    def _restore_work(self):
        """Restaura um arquivo de trabalho salvo anteriormente."""
        path = filedialog.askopenfilename(
            parent=self,
            title="Restaurar trabalho do Tonalidades",
            filetypes=[("Trabalho Tonalidades (JSON)", "*.json"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        try:
            snapshot = json.loads(Path(path).read_text(encoding="utf-8"))
            if snapshot.get("formato") != "tonalidades-trabalho":
                raise ValueError("Este arquivo não é um trabalho salvo pelo Tonalidades. Selecione um arquivo criado pelo botão 'Salvar trabalho'.")
            config_atual = snapshot.get("configuracao_atual") or snapshot.get("configuracao")
            config_otimizada = snapshot.get("configuracao_otimizada")
            resultado = snapshot.get("resultado")
            if not isinstance(config_atual, dict):
                raise ValueError("O arquivo não contém uma configuração válida.")
            if resultado and isinstance(config_otimizada, dict):
                # Ao restaurar um resultado, mostramos os dados exatos usados
                # para produzi-lo, evitando misturar entradas editadas depois.
                self._apply_config(config_otimizada)
                self.last_config = config_otimizada
            else:
                self._apply_config(config_atual)
                self.last_config = None
            self.result = resultado
            if self.result:
                total = self.result.get("metros_totais")
                if isinstance(total, (int, float)):
                    self.status_var.set(f"Trabalho restaurado — resultado disponível; consumo total: {total:.2f} m")
                else:
                    self.status_var.set("Trabalho restaurado — resultado da otimização disponível.")
                messagebox.showinfo("Trabalho restaurado", "Os dados, parâmetros e resultado salvos foram restaurados.", parent=self)
            else:
                self.status_var.set("Trabalho restaurado — entradas carregadas; ainda não há resultado salvo.")
                messagebox.showinfo("Trabalho restaurado", "Os dados e parâmetros foram restaurados. Este arquivo não contém um resultado de otimização.", parent=self)
        except Exception as exc:
            messagebox.showerror("Erro ao restaurar", f"Não foi possível restaurar o trabalho:\n{exc}", parent=self)

    def _apply_config(self, config):
        """Aplica os dados de uma configuração às tabelas e parâmetros da tela."""
        for tree in (self.demand_tree, self.nav_tree, self.stock_tree):
            tree.delete(*tree.get_children())
        for size, qty in config.get("demanda", {}).items():
            self.demand_tree.insert("", "end", values=(size, qty))
        for nav in config.get("navalhas", []):
            self.nav_tree.insert("", "end", values=(
                nav.get("componente", ""), nav.get("tamanho", ""),
                nav.get("largura_cm", nav.get("largura1_cm", "")), nav.get("comprimento_cm", nav.get("comprimento1_cm", "")),
                nav.get("largura2_cm", ""), nav.get("comprimento2_cm", ""),
                nav.get("pares_por_batida", ""),
            ))
        for tone, meters in config.get("estoque_tons_metros", {}).items():
            self.stock_tree.insert("", "end", values=(tone, meters))
        self.width_var.set(str(config.get("largura_mesa_cm", 139)))
        self.margin_var.set(str(config.get("margem_seguranca_cm", 1)))
        self.loss_var.set(str(config.get("perda_trocas_percentual", 1)))
        self.gap_var.set(str(config.get("folga_entre_navalhas_cm", 0)))
        extras = config.get("acrescimo_comprimento_cm", {})
        self.extra_int_var.set(str(extras.get("gaspea_interna", 0.3)))
        self.extra_ext_var.set(str(extras.get("gaspea_externa", 0.3)))

    @staticmethod
    def _number(value, label):
        try:
            return float(str(value).strip().replace(",", "."))
        except ValueError:
            raise ValueError(f"Valor inválido em {label}: {value!r}")

    def _read_inputs(self):
        demand = {}
        for row in self.demand_tree.get_children():
            size, qty = self.demand_tree.item(row, "values")
            size = str(size).strip()
            if not size or size in demand:
                raise ValueError(f"Tamanho vazio ou repetido na demanda: {size!r}")
            q = self._number(qty, f"demanda do tamanho {size}")
            if q <= 0 or not q.is_integer():
                raise ValueError(f"A demanda de {size} deve ser um inteiro maior que zero.")
            demand[size] = int(q)
        if not demand:
            raise ValueError("Informe pelo menos um tamanho e sua demanda.")

        navs = {}
        components = set()
        for row in self.nav_tree.get_children():
            component, size, width1, length1, width2, length2, pairs = self.nav_tree.item(row, "values")
            component, size = str(component).strip(), str(size).strip()
            if not component or not size:
                raise ValueError("Componente e tamanho são obrigatórios em cada navalha.")
            if size not in demand:
                continue  # permite manter navalhas cadastradas para tamanhos não solicitados
            key = (component, size)
            if key in navs:
                raise ValueError(f"Navalha duplicada: {component} / {size}")
            w1 = self._number(width1, f"largura 1 {component}/{size}")
            l1 = self._number(length1, f"comprimento 1 {component}/{size}")
            p = self._number(pairs, f"pares por batida {component}/{size}")
            w2_text = str(width2).strip()
            l2_text = str(length2).strip()
            w2 = self._number(w2_text, f"largura 2 {component}/{size}") if w2_text else None
            l2 = self._number(l2_text, f"comprimento 2 {component}/{size}") if l2_text else None
            if min(w1, l1, p) <= 0 or (w2 is not None and w2 <= 0) or (l2 is not None and l2 <= 0):
                raise ValueError(f"As medidas preenchidas e os pares devem ser positivos ({component}/{size}).")
            if w2 is not None and w2 > w1:
                raise ValueError(f"A Largura 2 deve ser menor ou igual à Largura 1 ({component}/{size}).")
            navs[key] = (w1, l1, w2, l2, p)
            components.add(component)

        # O motor define o encaixe por componente; por isso todos os tamanhos
        # de um componente devem usar duas larguras ou todos devem usar largura simples.
        for component in components:
            modes = {navs[(c, s)][2] is not None for (c, s) in navs if c == component}
            if len(modes) > 1:
                raise ValueError(
                    f"O componente {component!r} mistura navalhas simples e com encaixe. "
                    "Preencha Largura 2 para todos os tamanhos desse componente, ou deixe-a vazia em todos."
                )
        if len(components) < 1:
            raise ValueError("Cadastre navalhas para os tamanhos solicitados.")
        missing = [(c, s) for c in components for s in demand if (c, s) not in navs]
        if missing:
            preview = ", ".join(f"{c}/{s}" for c, s in missing[:8])
            raise ValueError("Faltam navalhas para estes componentes/tamanhos: " + preview)

        tones = {}
        for row in self.stock_tree.get_children():
            tone, meters = self.stock_tree.item(row, "values")
            tone = str(tone).strip()
            if not tone or tone in tones:
                raise ValueError(f"Tonalidade vazia ou repetida: {tone!r}")
            m = self._number(meters, f"estoque {tone}")
            if m < 0:
                raise ValueError(f"O estoque de {tone} não pode ser negativo.")
            tones[tone] = m
        if not tones or not any(v > 0 for v in tones.values()):
            raise ValueError("Informe pelo menos uma tonalidade com estoque maior que zero.")

        width = self._number(self.width_var.get(), "largura da mesa")
        margin = self._number(self.margin_var.get(), "margem de segurança")
        loss = self._number(self.loss_var.get(), "perda por trocas")
        gap = self._number(self.gap_var.get(), "folga entre navalhas")
        extra_i = self._number(self.extra_int_var.get(), "acréscimo gaspea interna")
        extra_e = self._number(self.extra_ext_var.get(), "acréscimo gaspea externa")
        if width <= 0 or margin < 0 or margin >= width:
            raise ValueError("A largura da mesa deve ser positiva e a margem deve ser entre zero e menor que a largura.")
        if not 0 <= loss < 100:
            raise ValueError("A perda por trocas deve ser maior ou igual a 0 e menor que 100%.")
        if gap < 0 or extra_i < 0 or extra_e < 0:
            raise ValueError("Folga e acréscimos não podem ser negativos.")
        if abs(loss - round(loss)) > 1e-9:
            raise ValueError("A perda por trocas deve ser um percentual inteiro (ex.: 1 ou 2).")
        extras = {}
        for component in components:
            if component == "gaspea_interna":
                extras[component] = extra_i
            elif component == "gaspea_externa":
                extras[component] = extra_e
            else:
                extras[component] = 0.3
        return {
            "demanda": demand,
            "navalhas": [
                {
                    "componente": c, "tamanho": s,
                    "largura_cm": w1, "comprimento_cm": l1,
                    "largura2_cm": w2, "comprimento2_cm": l2,
                    "encaixe": w2 is not None,
                    "pares_por_batida": p,
                }
                for (c, s), (w1, l1, w2, l2, p) in navs.items()
            ],
            "estoque_tons_metros": tones,
            "largura_mesa_cm": width,
            "margem_seguranca_cm": margin,
            "perda_trocas_percentual": loss,
            "folga_entre_navalhas_cm": gap,
            "acrescimo_comprimento_cm": extras,
            "max_tamanhos_por_fileira": 2,
            "tempo_limite_segundos": 60,
        }

    def _solve(self):
        try:
            configuracao = self._read_inputs()
        except Exception as exc:
            messagebox.showerror("Verifique os dados", str(exc), parent=self)
            return
        self.last_config = configuracao
        self.result = None
        self.status_var.set("Otimizando... aguarde.")
        self.configure(cursor="watch")
        self.update_idletasks()
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                self.result = alg.resolver(configuracao)
                if self.result:
                    alg.imprimir(self.result)
            log = output.getvalue()
            self.configure(cursor="")
            if not self.result:
                self.status_var.set("Não foi encontrada solução viável.")
                self._show_output(log or "Sem solução viável. Revise estoque, demanda, largura e dimensões das navalhas.")
                return
            self.status_var.set(f"Concluído — consumo total: {self.result['metros_totais']:.2f} m")
            self._show_output(log)
        except Exception as exc:
            self.configure(cursor="")
            self.status_var.set("Erro durante a otimização.")
            messagebox.showerror("Erro na otimização", f"{exc}\n\n{output.getvalue()}", parent=self)

    def _show_output(self, content):
        win = tk.Toplevel(self)
        win.title("Resultado da otimização")
        win.geometry("1000x680")
        head = ttk.Frame(win, padding=10)
        head.pack(fill="x")
        ttk.Label(head, text="Resultado do cálculo", style="Title.TLabel").pack(side="left")
        ttk.Button(head, text="Salvar relatório TXT", command=lambda: self._save_text(content)).pack(side="right")
        text_frame = ttk.Frame(win, padding=(10, 0, 10, 10))
        text_frame.pack(fill="both", expand=True)
        box = tk.Text(text_frame, wrap="none", font=("Consolas", 10), undo=False)
        ys = ttk.Scrollbar(text_frame, orient="vertical", command=box.yview)
        xs = ttk.Scrollbar(text_frame, orient="horizontal", command=box.xview)
        box.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        box.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        box.insert("1.0", content)
        box.configure(state="disabled")

    def _save_text(self, content):
        path = filedialog.asksaveasfilename(parent=self, title="Salvar relatório", defaultextension=".txt", filetypes=[("Texto", "*.txt"), ("Todos os arquivos", "*.*")])
        if path:
            Path(path).write_text(content, encoding="utf-8")
            messagebox.showinfo("Salvo", f"Relatório salvo em:\n{path}", parent=self)


    def _export_json(self):
        """Exporta somente o resultado da otimização em JSON."""
        if not self.result:
            messagebox.showwarning("Sem resultado", "Execute a otimização antes de exportar o resultado.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar resultado da otimização",
            defaultextension=".json",
            filetypes=[("Arquivo JSON", "*.json")],
            initialfile="resultado_tonalidades.json",
        )
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(self.result, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("Resultado exportado", f"Resultado salvo em:\n{path}", parent=self)
            self.status_var.set(f"Resultado exportado: {Path(path).name}")
        except Exception as exc:
            messagebox.showerror("Erro ao exportar", f"Não foi possível exportar o resultado:\n{exc}", parent=self)

    def _export_excel(self):
        """Exporta os padrões de corte no formato da tabela física de produção."""
        if not self.result:
            messagebox.showwarning("Sem resultado", "Execute a otimização antes de exportar.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar sequência de corte para Excel",
            defaultextension=".xlsx",
            filetypes=[("Planilha Excel", "*.xlsx")],
            initialfile="sequencia_corte_tonalidades.xlsx",
        )
        if not path:
            return
        try:
            wb = Workbook()
            ws_inicial = wb.active
            ws_inicial.title = "Base_Navalhas"
            ws_base = ws_inicial
            ws_base.append(["Componente", "Tamanho", "Largura 1 (cm)", "Largura 2 (cm)"])
            navalhas_config = (self.last_config or {}).get("navalhas", [])
            for navalha in navalhas_config:
                ws_base.append([
                    str(navalha.get("componente", "")),
                    str(navalha.get("tamanho", "")),
                    float(navalha.get("largura_cm", 0)),
                    float(navalha.get("largura2_cm") if navalha.get("largura2_cm") not in (None, "") else navalha.get("largura_cm", 0)),
                ])
            ws_base.sheet_state = "hidden"
            # Solicita ao Excel recalcular as fórmulas ao abrir o arquivo.
            wb.calculation.fullCalcOnLoad = True
            wb.calculation.forceFullCalc = True
            wb.calculation.calcMode = "auto"
            thin_gray = Side(style="thin", color="808080")
            medium_black = Side(style="medium", color="202020")
            header_fill = PatternFill("solid", fgColor="D9E2F3")
            title_fill = PatternFill("solid", fgColor="B4C6E7")
            title_font = Font(name="Arial", size=12, bold=True)
            header_font = Font(name="Arial", size=10, bold=True)
            body_font = Font(name="Arial", size=10)
            usable_width = None
            if self.last_config:
                usable_width = float(self.last_config["largura_mesa_cm"])
            gap_cm = float((self.last_config or {}).get("folga_entre_navalhas_cm", 0))
            base_last_row = max(2, ws_base.max_row)
            base_component_range = f"'Base_Navalhas'!$A$2:$A${base_last_row}"
            base_size_range = f"'Base_Navalhas'!$B$2:$B${base_last_row}"
            base_width1_range = f"'Base_Navalhas'!$C$2:$C${base_last_row}"
            base_width2_range = f"'Base_Navalhas'!$D$2:$D${base_last_row}"

            sheet_count = 0
            for tone, tone_data in self.result.get("tons", {}).items():
                campaigns_by_component = {}
                for campaign in tone_data.get("campanhas", []):
                    campaigns_by_component.setdefault(campaign["componente"], []).append(campaign)
                for component, campaigns in campaigns_by_component.items():
                    stages = [stage for campaign in campaigns for stage in campaign.get("etapas", [])]
                    if not stages:
                        continue
                    max_slots = max((len(stage.get("contagem", {})) for stage in stages), default=1)
                    max_slots = max(1, max_slots)
                    headers = ["SEQU."]
                    for _ in range(max_slots):
                        headers.extend(["BAT.", "NÚM.", "POS."])
                    headers.append("MED.")
                    col_count = len(headers)
                    sheet_count += 1
                    raw_name = f"{tone}_{component}"
                    sheet_name = "".join(ch if ch not in '[]:*?/\\' else "_" for ch in raw_name)[:31] or f"Corte_{sheet_count}"
                    # Excel exige nomes de planilha únicos.
                    base_name, suffix = sheet_name, 2
                    while sheet_name in wb.sheetnames:
                        tail = f"_{suffix}"
                        sheet_name = base_name[:31-len(tail)] + tail
                        suffix += 1
                    ws = wb.create_sheet(sheet_name)
                    title_width = f"{usable_width:.0f}" if usable_width is not None else "configurada"
                    title = f"SISTEMA DE CORTE PARA MATERIAL COM LARGURA ATÉ {title_width} CM (1º FAIXA)"
                    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=col_count)
                    cell = ws.cell(1, 1, title)
                    cell.font = title_font
                    cell.fill = title_fill
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    for col in range(1, col_count + 1):
                        ws.cell(1, col).fill = title_fill
                        ws.cell(1, col).border = Border(top=medium_black, bottom=medium_black)
                    ws.row_dimensions[1].height = 28
                    ws.cell(2, 1, f"TONALIDADE: {tone} | COMPONENTE: {component}")
                    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=col_count)
                    ws.cell(2, 1).font = Font(name="Arial", size=10, bold=True)
                    ws.cell(2, 1).alignment = Alignment(horizontal="left")
                    for col, heading in enumerate(headers, 1):
                        cell = ws.cell(3, col, heading)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                        cell.border = Border(left=thin_gray, right=thin_gray, top=medium_black, bottom=medium_black)
                    ws.row_dimensions[3].height = 22

                    # Cada linha representa um padrão transversal de navalhas.
                    # BAT. é a quantidade de navalhas daquele tamanho no padrão;
                    # as repetições longitudinais do padrão ficam registradas em comentário.
                    for row_idx in range(4, max(14, 4 + len(stages))):
                        seq_index = row_idx - 3
                        stage = stages[seq_index - 1] if seq_index - 1 < len(stages) else None
                        values = [f"{seq_index:02d}"]
                        if stage:
                            counts = stage.get("contagem", {})
                            left_size = stage.get("posicao_esquerda")
                            for size, count in counts.items():
                                position = "L" if left_size is None or str(size) == str(left_size) else "R"
                                values.extend([count, size, position])
                            while len(values) < col_count - 1:
                                values.extend([None, None, None])
                            # A coluna MED. usa uma fórmula Excel real, reproduzindo
                            # largura = soma(qtd. navalhas × largura individual)
                            #          + (total de navalhas - 1) × folga.
                            count_cells = [get_column_letter(2 + slot * 3) + str(row_idx) for slot in range(max_slots)]
                            size_cells = [get_column_letter(3 + slot * 3) + str(row_idx) for slot in range(max_slots)]
                            terms = []
                            component_criteria = str(component).replace('"', '""')
                            for slot, (count_cell, size_cell) in enumerate(zip(count_cells, size_cells)):
                                pos_cell = get_column_letter(4 + slot * 3) + str(row_idx)
                                lookup_criteria = f'{base_component_range},"{component_criteria}",{base_size_range},{size_cell}'
                                width2 = f'SUMIFS({base_width2_range},{lookup_criteria})'
                                width1 = f'SUMIFS({base_width1_range},{lookup_criteria})'
                                # Cada navalha contribui com Largura 2; somente a navalha
                                # na posição L recebe o ajuste (Largura 1 - Largura 2).
                                terms.append(f'{count_cell}*{width2}+IF({pos_cell}="L",{width1}-{width2},0)')
                            total_count = ",".join(count_cells)
                            width_formula = (
                                f'=IF(COUNTA({total_count})=0,"",'
                                + "+".join(terms)
                                + f'+MAX(0,(SUM({total_count})-1)*{gap_cm}))'
                            )
                            values.append(width_formula)
                        else:
                            values.extend([None] * (col_count - 1))
                        for col, value in enumerate(values, 1):
                            cell = ws.cell(row_idx, col, value)
                            cell.font = body_font
                            cell.alignment = Alignment(horizontal="center", vertical="center")
                            cell.border = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=thin_gray)
                        if stage:
                            ws.cell(row_idx, col_count).number_format = "0.0"
                            counts_for_note = stage.get("contagem", {})
                            nav_widths = {
                                str(n.get("tamanho", "")): (
                                    float(n.get("largura_cm", 0)),
                                    float(n.get("largura2_cm") if n.get("largura2_cm") not in (None, "") else n.get("largura_cm", 0)),
                                )
                                for n in navalhas_config
                                if str(n.get("componente", "")) == str(component)
                            }
                            left_size = stage.get("posicao_esquerda")
                            width_terms = []
                            for size, count in counts_for_note.items():
                                w1, w2 = nav_widths.get(str(size), (0, 0))
                                term = f"{count} × {w2:g} cm (Largura 2)"
                                if left_size is not None and str(size) == str(left_size):
                                    term += f" + ({w1:g} - {w2:g}) cm de ajuste da posição esquerda"
                                width_terms.append(term)
                            total_knives = sum(float(v) for v in counts_for_note.values())
                            width_expression = " + ".join(width_terms) or "0"
                            width_expression += f" + ({total_knives:g} - 1) × {gap_cm:g} cm de folga"
                            ws.cell(row_idx, col_count).comment = Comment(
                                "Fórmula Excel: soma(qtd. navalhas × Largura 2) + ajuste (Largura 1 - Largura 2) da navalha na posição L + "
                                "(quantidade total de navalhas - 1) × folga.\n"
                                f"Exemplo deste padrão: {width_expression}\n"
                                f"Largura calculada pelo otimizador: {float(stage.get('largura_cm', 0)):.2f} cm\n"
                                f"Padrão: {stage.get('sequencia', '')}\n"
                                f"Repetições longitudinais: {stage.get('batidas', 0)}\n"
                                f"Comprimento por batida: {float(stage.get('comprimento_batida_cm', 0)):.2f} cm\n"
                                f"Consumo do padrão: {float(stage.get('metros', 0)):.2f} m",
                                "Tonalidades",
                            )
                    widths = [9]
                    for _ in range(max_slots):
                        widths.extend([9, 10, 9])
                    widths.append(11)
                    for col, width in enumerate(widths, 1):
                        ws.column_dimensions[get_column_letter(col)].width = width
                    ws.freeze_panes = "B4"
                    ws.sheet_view.showGridLines = False
                    ws.auto_filter.ref = f"A3:{get_column_letter(col_count)}{max(13, 3 + len(stages))}"
                    ws.page_setup.orientation = "landscape"
                    ws.page_setup.paperSize = ws.PAPERSIZE_A4
                    ws.page_setup.fitToWidth = 1
                    ws.page_setup.fitToHeight = 0
                    ws.sheet_properties.pageSetUpPr.fitToPage = True
                    ws.print_title_rows = "1:3"
                    ws.print_area = f"A1:{get_column_letter(col_count)}{max(13, 3 + len(stages))}"

            if not sheet_count:
                raise ValueError("O resultado não contém padrões de corte para exportar.")
            wb.save(path)
            messagebox.showinfo("Exportado", f"Planilha Excel salva em:\n{path}", parent=self)
            self.status_var.set("Planilha Excel exportada.")
        except Exception as exc:
            messagebox.showerror("Erro na exportação", f"Não foi possível gerar a planilha Excel:\n{exc}", parent=self)


if __name__ == "__main__":
    app = TonalidadesApp()
    app.mainloop()
