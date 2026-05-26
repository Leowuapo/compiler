import io
import os
import re
import sys
import shutil
import subprocess
import webbrowser
from pathlib import Path
from contextlib import redirect_stdout

SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

try:
    import customtkinter as ctk
except ImportError:
    import tkinter as tk
    import tkinter.font as tkfont
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "CustomTkinter no instalado",
        "Esta interfaz necesita CustomTkinter.\n\nInstalación sugerida:\n"
        "pip install customtkinter\n\nOpcional para AST como imagen:\n"
        "pip install Pillow\n\nGraphviz del sistema:\n"
        "brew install graphviz  /  apt install graphviz"
    )
    sys.exit(1)

import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk


try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    Image = None
    ImageTk = None
    PILLOW_AVAILABLE = False

try:
    from deps_checker import check_all, show_gui_warning
    obligatorias_ok, resultados, recomendaciones = check_all()
    GRAPHVIZ_AVAILABLE = resultados.get('graphviz', (False, ''))[0]
    missing_opcionales = [dep for dep, (ok, _) in resultados.items() if not ok and dep != 'tkinter']
    if missing_opcionales:
        # La GUI puede funcionar sin Pillow/Graphviz, pero se avisa al usuario.
        show_gui_warning(missing_opcionales, recomendaciones)
except Exception:
    GRAPHVIZ_AVAILABLE = shutil.which('dot') is not None

import lexer.lector as lector
import parser_sdt.syntax_parser as parser
from parser_sdt.sdt import tabla_simbolos, tabla_funciones, formatear_valor


class CompilerGUI:
    """Interfaz moderna para el compilador Team 05.

    Mantiene el pipeline actual lexer -> parser/SDT/backend y agrega:
    - resaltado de sintaxis tipo C usando el lexer existente,
    - zoom de editor/resultados,
    - tabla de tokens,
    - errores separados,
    - tabla de símbolos y funciones,
    - AST visual generado con Graphviz/SVG,
    - pestañas para TAC, TAC optimizado y código objetivo.
    """

    THEME = {
        'bg': '#0f172a',
        'panel': '#111827',
        'panel_2': '#0b1220',
        'panel_3': '#1e293b',
        'border': '#334155',
        'text': '#e5e7eb',
        'muted': '#94a3b8',
        'accent': '#38bdf8',
        'accent_2': '#2563eb',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'purple': '#a78bfa',
        'orange': '#fb923c',
        'green': '#86efac',
        'ast_edge': '#46637f',
        'ast_outline': '#7dd3fc',
    }

    SAMPLE_CODE = """int main() {
    float y = (2 + 3) * 4;
    int values[3];
    values[0] = 10;

    if (y > values[0]) {
        printf("result = %f", y);
    }

    return 0;
}"""

    def __init__(self, root):
        self.root = root
        self.root.title("Team 05 Compiler")
        self.root.geometry("1500x860")
        self.root.minsize(1180, 720)
        self.code_font_family = self._select_code_font()
        self.ui_font_family = "Segoe UI"

        self.editor_font_size = 12
        self.output_font_size = 11
        self.ast_scale = 1.0
        self.graphviz_scale = 1.0
        self.highlight_after_id = None
        self.last_tokens = []
        self.last_ast = None
        self.ast_photo = None
        self.ast_graphviz_photo = None
        self.current_file_path = None
        self.outputs_root = os.path.join(SRC_ROOT, "outputs")
        self.current_output_dir = None
        self.current_artifacts = {}
        self._set_output_dir(os.path.join(self.outputs_root, "gui_run"))

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._configure_ttk_style()
        self._build_layout()
        self._configure_text_tags()
        self._bind_editor_events()
        self.reset_stage_cards()
        self.code_input.insert("1.0", self.SAMPLE_CODE)
        self.update_line_numbers()
        self.schedule_highlight()
        self.set_placeholder_texts()

    # ---------------------------------------------------------------------
    # Layout
    # ---------------------------------------------------------------------

    def _select_code_font(self):
        preferred_fonts = [
            "JetBrains Mono",
            "Fira Code",
            "Cascadia Code",
            "SF Mono",
            "Menlo",
            "Monaco",
            "Consolas",
            "Courier New",
        ]

        available_fonts = set(tkfont.families())

        for font in preferred_fonts:
            if font in available_fonts:
                return font

        return "TkFixedFont"


    def _configure_ttk_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Compiler.Treeview",
            background=self.THEME['panel_2'],
            foreground=self.THEME['text'],
            fieldbackground=self.THEME['panel_2'],
            rowheight=30,
            bordercolor=self.THEME['border'],
            borderwidth=0,
            font=(self.code_font_family, self.editor_font_size)
        )
        style.configure(
            "Compiler.Treeview.Heading",
            background=self.THEME['panel_3'],
            foreground=self.THEME['text'],
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Compiler.Treeview",
            background=[("selected", self.THEME['accent_2'])],
            foreground=[("selected", "#ffffff")],
        )

    def _build_layout(self):
        self.root.configure(fg_color=self.THEME['bg'])
        self.root.grid_columnconfigure(0, weight=4, uniform="main")
        self.root.grid_columnconfigure(1, weight=7, uniform="main")
        self.root.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.root, fg_color=self.THEME['panel'], corner_radius=18)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w", padx=18, pady=14)
        ctk.CTkLabel(
            title_box,
            text="Team 05 Compiler",
            font=("Segoe UI", 24, "bold"),
            text_color=self.THEME['text'],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Léxico · Sintáctico · Semántico · TAC · Optimización · Target Code",
            font=("Segoe UI", 13),
            text_color=self.THEME['muted'],
        ).pack(anchor="w", pady=(3, 0))

        self.stage_container = ctk.CTkFrame(header, fg_color="transparent")
        self.stage_container.grid(row=0, column=1, sticky="e", padx=18, pady=12)
        self.stage_cards = {}
        for idx, key in enumerate(["lexico", "sintactico", "semantico"]):
            card = ctk.CTkFrame(self.stage_container, fg_color=self.THEME['panel_2'], corner_radius=14)
            card.grid(row=0, column=idx, padx=6)
            label = ctk.CTkLabel(card, text="", width=145, height=44, font=("Segoe UI", 12, "bold"))
            label.pack(padx=6, pady=6)
            self.stage_cards[key] = label

        left = ctk.CTkFrame(self.root, fg_color=self.THEME['panel'], corner_radius=18)
        left.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(8, 16))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        editor_header = ctk.CTkFrame(left, fg_color="transparent")
        editor_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))
        editor_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            editor_header,
            text="Editor de código",
            font=("Segoe UI", 17, "bold"),
            text_color=self.THEME['text'],
        ).grid(row=0, column=0, sticky="w")

        zoom_frame = ctk.CTkFrame(editor_header, fg_color="transparent")
        zoom_frame.grid(row=0, column=1, sticky="e")
        self._small_button(zoom_frame, "A−", self.decrease_font).pack(side="left", padx=3)
        self._small_button(zoom_frame, "A+", self.increase_font).pack(side="left", padx=3)
        self._small_button(zoom_frame, "Reset", self.reset_font).pack(side="left", padx=3)

        buttons = ctk.CTkFrame(left, fg_color="transparent")
        buttons.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        buttons.grid_columnconfigure((0, 1, 2), weight=1)
        self._primary_button(buttons, "Compilar todo", self.compile_code).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=4)
        self._secondary_button(buttons, "Solo léxico", self.run_lexer_only).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        self._secondary_button(buttons, "Parser + SDT", self.run_parser_sdt_only).grid(row=0, column=2, sticky="ew", padx=(6, 0), pady=4)
        self._secondary_button(buttons, "Abrir", self.open_file).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=4)
        self._secondary_button(buttons, "Guardar", self.save_file).grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        self._danger_button(buttons, "Limpiar", self.clear_all).grid(row=1, column=2, sticky="ew", padx=(6, 0), pady=4)

        editor_shell = ctk.CTkFrame(left, fg_color=self.THEME['panel_2'], corner_radius=14)
        editor_shell.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        editor_shell.grid_rowconfigure(0, weight=1)
        editor_shell.grid_columnconfigure(1, weight=1)

        self.line_numbers = tk.Text(
            editor_shell,
            width=5,
            padx=6,
            pady=10,
            borderwidth=0,
            highlightthickness=0,
            bg=self.THEME['panel_2'],
            fg=self.THEME['muted'],
            font=(self.code_font_family, self.editor_font_size),
            state="disabled",
            wrap="none",
        )
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        self.code_input = tk.Text(
            editor_shell,
            undo=True,
            wrap="none",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.THEME['border'],
            highlightcolor=self.THEME['accent'],
            bg=self.THEME['panel_2'],
            fg=self.THEME['text'],
            insertbackground=self.THEME['accent'],
            selectbackground=self.THEME['accent_2'],
            selectforeground="#ffffff",
            font=(self.code_font_family, self.editor_font_size),
            padx=12,
            pady=10,
        )
        self.code_input.grid(row=0, column=1, sticky="nsew")

        yscroll = ctk.CTkScrollbar(editor_shell, orientation="vertical", command=self._editor_yview)
        yscroll.grid(row=0, column=2, sticky="ns")
        xscroll = ctk.CTkScrollbar(editor_shell, orientation="horizontal", command=self.code_input.xview)
        xscroll.grid(row=1, column=1, sticky="ew")
        self.code_input.configure(yscrollcommand=lambda first, last: self._on_editor_scroll(first, last, yscroll), xscrollcommand=xscroll.set)

        right = ctk.CTkFrame(self.root, fg_color=self.THEME['panel'], corner_radius=18)
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=(8, 16))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        result_header = ctk.CTkFrame(right, fg_color="transparent")
        result_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        result_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            result_header,
            text="Resultados del compilador",
            font=("Segoe UI", 17, "bold"),
            text_color=self.THEME['text'],
        ).grid(row=0, column=0, sticky="w")
        self.status_label = ctk.CTkLabel(
            result_header,
            text="Listo",
            font=("Segoe UI", 12, "bold"),
            text_color=self.THEME['success'],
        )
        self.status_label.grid(row=0, column=1, sticky="e")

        self.tabs = ctk.CTkTabview(right, fg_color=self.THEME['panel_2'], segmented_button_fg_color=self.THEME['panel_3'])
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))

        for name in [
            "Output", "Tokens", "Errors", "Symbol Table", "Function Table",
            "AST Tree", "TAC", "TAC Optimized", "Target Code"
        ]:
            self.tabs.add(name)
            self.tabs.tab(name).configure(fg_color=self.THEME['panel_2'])
            self.tabs.tab(name).grid_columnconfigure(0, weight=1)
            self.tabs.tab(name).grid_rowconfigure(0, weight=1)

        self.output_text = self._make_textbox(self.tabs.tab("Output"))
        self.error_text = self._make_textbox(self.tabs.tab("Errors"))
        self.tac_text = self._make_textbox(self.tabs.tab("TAC"))
        self.tac_optimized_text = self._make_textbox(self.tabs.tab("TAC Optimized"))
        self.target_text = self._make_textbox(self.tabs.tab("Target Code"))

        self.token_tree = self._make_tree(self.tabs.tab("Tokens"), ("tipo", "lexema", "linea", "columna"))
        self._heading(self.token_tree, "tipo", "Tipo", 130)
        self._heading(self.token_tree, "lexema", "Lexema", 260)
        self._heading(self.token_tree, "linea", "Línea", 80)
        self._heading(self.token_tree, "columna", "Columna", 90)

        self.symbol_tree = self._make_tree(self.tabs.tab("Symbol Table"), ("nombre", "tipo", "valor", "detalle"))
        self._heading(self.symbol_tree, "nombre", "Nombre", 170)
        self._heading(self.symbol_tree, "tipo", "Tipo", 120)
        self._heading(self.symbol_tree, "valor", "Valor", 260)
        self._heading(self.symbol_tree, "detalle", "Detalle", 170)

        self.function_tree = self._make_tree(self.tabs.tab("Function Table"), ("nombre", "retorno", "parametros"))
        self._heading(self.function_tree, "nombre", "Función", 180)
        self._heading(self.function_tree, "retorno", "Retorno", 120)
        self._heading(self.function_tree, "parametros", "Parámetros", 420)

        self._build_graphviz_tab()

    def _build_ast_canvas_tab(self):
        tab = self.tabs.tab("AST Canvas")
        tab.grid_rowconfigure(1, weight=1)
        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self._small_button(toolbar, "AST −", lambda: self.zoom_ast_canvas(0.85)).pack(side="left", padx=3)
        self._small_button(toolbar, "AST +", lambda: self.zoom_ast_canvas(1.15)).pack(side="left", padx=3)
        self._small_button(toolbar, "Reset", self.reset_ast_canvas_zoom).pack(side="left", padx=3)

        shell = ctk.CTkFrame(tab, fg_color=self.THEME['panel_2'])
        shell.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(0, weight=1)
        self.ast_canvas = tk.Canvas(shell, bg=self.THEME['panel_2'], highlightthickness=0)
        self.ast_canvas.grid(row=0, column=0, sticky="nsew")
        vbar = ctk.CTkScrollbar(shell, orientation="vertical", command=self.ast_canvas.yview)
        hbar = ctk.CTkScrollbar(shell, orientation="horizontal", command=self.ast_canvas.xview)
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        self.ast_canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.ast_canvas.bind("<ButtonPress-1>", lambda e: self.ast_canvas.scan_mark(e.x, e.y))
        self.ast_canvas.bind("<B1-Motion>", lambda e: self.ast_canvas.scan_dragto(e.x, e.y, gain=1))

    def _build_graphviz_tab(self):
        tab = self.tabs.tab("AST Tree")
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

        self._small_button(toolbar, "SVG −", lambda: self.zoom_graphviz(0.85)).pack(side="left", padx=3)
        self._small_button(toolbar, "SVG +", lambda: self.zoom_graphviz(1.15)).pack(side="left", padx=3)
        self._small_button(toolbar, "Fit", self.fit_graphviz_to_view).pack(side="left", padx=3)
        self._small_button(toolbar, "Reset", self.reset_graphviz_zoom).pack(side="left", padx=3)
        self._small_button(toolbar, "Exportar SVG", self.export_graphviz_svg).pack(side="left", padx=3)
        self._small_button(toolbar, "Abrir SVG", self.open_graphviz_svg).pack(side="left", padx=3)

        shell = ctk.CTkFrame(tab, fg_color=self.THEME['panel_2'])
        shell.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        self.graphviz_canvas = tk.Canvas(
            shell,
            bg=self.THEME['panel_2'],
            highlightthickness=0
        )
        self.graphviz_canvas.grid(row=0, column=0, sticky="nsew")

        vbar = ctk.CTkScrollbar(shell, orientation="vertical", command=self.graphviz_canvas.yview)
        hbar = ctk.CTkScrollbar(shell, orientation="horizontal", command=self.graphviz_canvas.xview)

        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")

        self.graphviz_canvas.configure(
            yscrollcommand=vbar.set,
            xscrollcommand=hbar.set
        )

        # Arrastrar imagen con mouse
        self.graphviz_canvas.bind("<ButtonPress-1>", lambda e: self.graphviz_canvas.scan_mark(e.x, e.y))
        self.graphviz_canvas.bind("<B1-Motion>", lambda e: self.graphviz_canvas.scan_dragto(e.x, e.y, gain=1))

        self.graphviz_canvas.create_text(
            30,
            30,
            anchor="nw",
            fill=self.THEME['muted'],
            text="Compila código para generar el AST Tree."
        )

    def _make_textbox(self, parent):
        box = ctk.CTkTextbox(
            parent,
            fg_color=self.THEME['panel_2'],
            text_color=self.THEME['text'],
            border_color=self.THEME['border'],
            border_width=1,
            corner_radius=12,
            font=("Consolas", self.output_font_size),
            wrap="word",
        )
        box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        return box

    def _make_tree(self, parent, columns, tree_column=False):
        frame = ctk.CTkFrame(parent, fg_color=self.THEME['panel_2'], corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        show = "tree headings" if tree_column else "headings"
        tree = ttk.Treeview(frame, columns=columns, show=show, style="Compiler.Treeview")
        tree.grid(row=0, column=0, sticky="nsew")
        ybar = ctk.CTkScrollbar(frame, orientation="vertical", command=tree.yview)
        xbar = ctk.CTkScrollbar(frame, orientation="horizontal", command=tree.xview)
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        return tree

    def _heading(self, tree, column, text, width):
        tree.heading(column, text=text)
        tree.column(column, width=width, stretch=True)

    def _primary_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=12,
                             fg_color=self.THEME['accent_2'], hover_color="#1d4ed8",
                             font=("Segoe UI", 12, "bold"))

    def _secondary_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=12,
                             fg_color=self.THEME['panel_3'], hover_color="#334155",
                             font=("Segoe UI", 12, "bold"))

    def _danger_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=12,
                             fg_color="#7f1d1d", hover_color="#991b1b",
                             font=("Segoe UI", 12, "bold"))

    def _small_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, width=72, height=30, corner_radius=10,
                             fg_color=self.THEME['panel_3'], hover_color="#334155",
                             font=("Segoe UI", 11, "bold"))

    # ---------------------------------------------------------------------
    # Editor, highlighting and zoom
    # ---------------------------------------------------------------------
    def _configure_text_tags(self):
        tag_styles = {
            "keyword": {"foreground": self.THEME['purple']},
            "type": {"foreground": "#60a5fa"},
            "constant": {"foreground": self.THEME['orange']},
            "literal": {"foreground": self.THEME['green']},
            "operator": {"foreground": "#f472b6"},
            "punctuation": {"foreground": "#cbd5e1"},
            "comment": {"foreground": "#64748b", "font": ("Consolas", self.editor_font_size, "italic")},
            "error": {"foreground": self.THEME['error'], "underline": True},
        }
        for tag, opts in tag_styles.items():
            self.code_input.tag_configure(tag, **opts)

    def _bind_editor_events(self):
        self.code_input.bind("<<Modified>>", self._on_text_modified)
        self.code_input.bind("<KeyRelease>", lambda _e: self.schedule_highlight())

        # Scroll sincronizado editor + números de línea
        self.code_input.bind("<MouseWheel>", self._on_mousewheel)
        self.line_numbers.bind("<MouseWheel>", self._on_mousewheel)

        # Compatibilidad Linux
        self.code_input.bind("<Button-4>", self._on_mousewheel)
        self.code_input.bind("<Button-5>", self._on_mousewheel)
        self.line_numbers.bind("<Button-4>", self._on_mousewheel)
        self.line_numbers.bind("<Button-5>", self._on_mousewheel)

        self.code_input.bind("<ButtonRelease-1>", lambda _e: self.update_line_numbers())

    def _on_mousewheel(self, event):
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            # macOS/Windows
            delta = -1 if event.delta > 0 else 1

        self.code_input.yview_scroll(delta, "units")
        self.line_numbers.yview_moveto(self.code_input.yview()[0])

        return "break"

    def _on_text_modified(self, _event=None):
        if self.code_input.edit_modified():
            self.code_input.edit_modified(False)
            self.update_line_numbers()
            self.schedule_highlight()

    def _editor_yview(self, *args):
        self.code_input.yview(*args)
        self.line_numbers.yview_moveto(self.code_input.yview()[0])

    def _on_editor_scroll(self, first, last, scrollbar):
        scrollbar.set(first, last)
        self.line_numbers.yview_moveto(first)

    def update_line_numbers(self):
        line_count = int(self.code_input.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i).rjust(3) for i in range(1, line_count + 1))
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", numbers)
        self.line_numbers.configure(state="disabled")

    def schedule_highlight(self):
        if self.highlight_after_id is not None:
            self.root.after_cancel(self.highlight_after_id)
        self.highlight_after_id = self.root.after(120, self.highlight_syntax)

    def highlight_syntax(self):
        self.highlight_after_id = None
        code = self.get_code()
        for tag in ("keyword", "type", "constant", "literal", "operator", "punctuation", "comment", "error"):
            self.code_input.tag_remove(tag, "1.0", tk.END)

        type_words = {'int', 'float', 'double', 'char', 'void', 'bool', 'long', 'short', 'unsigned'}

        # Comentarios: el lexer los ignora, por eso se colorean con regex primero.
        for match in re.finditer(r"//.*|/\*[\s\S]*?\*/", code):
            self._tag_offset("comment", match.start(), match.end())

        try:
            with redirect_stdout(io.StringIO()):
                tokens = lector.analizeterminal(code)
        except Exception:
            tokens = None

        if not tokens:
            return

        for tipo, valor, linea, columna in tokens:
            start = f"{linea}.{columna - 1}"
            end = f"{linea}.{columna - 1 + len(valor)}"
            if tipo == "keyword" and valor in type_words:
                tag = "type"
            elif tipo == "keyword":
                tag = "keyword"
            elif tipo in {"constant", "literal", "operator", "punctuation"}:
                tag = tipo
            elif tipo == "special_character":
                tag = "error"
            else:
                continue
            self.code_input.tag_add(tag, start, end)

    def _tag_offset(self, tag, start_offset, end_offset):
        start = f"1.0+{start_offset}c"
        end = f"1.0+{end_offset}c"
        self.code_input.tag_add(tag, start, end)

    def get_code(self):
        return self.code_input.get("1.0", "end-1c")

    def increase_font(self):
        self.editor_font_size = min(self.editor_font_size + 1, 24)
        self.output_font_size = min(self.output_font_size + 1, 22)
        self.apply_fonts()

    def decrease_font(self):
        self.editor_font_size = max(self.editor_font_size - 1, 8)
        self.output_font_size = max(self.output_font_size - 1, 8)
        self.apply_fonts()

    def reset_font(self):
        self.editor_font_size = 12
        self.output_font_size = 11
        self.apply_fonts()

    def apply_fonts(self):
        self.code_input.configure(font=(self.code_font_family, self.editor_font_size))
        self.line_numbers.configure(font=(self.code_font_family, self.editor_font_size))
        self.code_input.tag_configure(
            "comment",
            font=(self.code_font_family, self.editor_font_size, "italic")
        )
        for box in [self.output_text, self.error_text, self.tac_text,
                    self.tac_optimized_text, self.target_text]:
            box.configure(font=(self.code_font_family, self.output_font_size))
        style = ttk.Style()
        style.configure(
            "Compiler.Treeview",
            font=(self.code_font_family, max(9, self.output_font_size - 1)),
            rowheight=max(28, self.output_font_size + 18)
        )
        self.update_line_numbers()
        self.schedule_highlight()

    # ---------------------------------------------------------------------
    # Output/artifact organization
    # ---------------------------------------------------------------------
    def _safe_run_name(self, source_path):
        if source_path and source_path != "<editor>":
            base = os.path.splitext(os.path.basename(source_path))[0]
        else:
            base = "gui_run"

        base = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("._-")
        return base or "gui_run"

    def _set_output_dir(self, output_dir):
        self.current_output_dir = os.path.abspath(output_dir)
        self.ast_output_base = os.path.join(self.current_output_dir, "ast")
        self.ast_png_path = self.ast_output_base + ".png"
        self.ast_dot_path = self.ast_output_base + ".dot"
        self.ast_modern_dot_path = os.path.join(self.current_output_dir, "ast_modern.dot")
        self.ast_modern_svg_path = os.path.join(self.current_output_dir, "ast_modern.svg")
        self.ast_graphviz_preview_png_path = os.path.join(
            self.current_output_dir,
            ".gui_cache",
            "ast_modern_preview.png",
        )
        self.ast_modern_png_path = self.ast_graphviz_preview_png_path
        self.current_artifacts = {
            "ast_dot": self.ast_dot_path,
            "ast_png": self.ast_png_path,
            "ast_modern_dot": self.ast_modern_dot_path,
            "ast_modern_svg": self.ast_modern_svg_path,
            "tac": os.path.join(self.current_output_dir, "tac.ir"),
            "tac_optimized": os.path.join(self.current_output_dir, "tac_optimized.ir"),
            "target_code": os.path.join(self.current_output_dir, "target_code.asm"),
        }

    def _prepare_output_dir(self, source_path):
        run_name = self._safe_run_name(source_path)
        output_dir = os.path.join(self.outputs_root, run_name)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, ".gui_cache"), exist_ok=True)
        self._set_output_dir(output_dir)
        return output_dir

    def _get_parser_result(self):
        getter = getattr(parser, "obtener_ultimo_resultado", None)
        if callable(getter):
            return getter() or {}
        return getattr(parser, "ultimo_resultado", None) or {}

    def _append_success_summary(self, resultado, parser_output):
        artifacts = dict(self.current_artifacts)
        artifacts.update((resultado or {}).get("artifacts") or {})
        artifacts["ast_modern_svg"] = self.ast_modern_svg_path

        vm_resultado = (resultado or {}).get("vm_resultado")
        vm_executed = (resultado or {}).get("vm_executed", vm_resultado is not None)

        self.append_output("Status: OK\n\n")
        self.append_output("Phases:\n")
        self.append_output("[OK] Lexer\n")
        self.append_output("[OK] Parser\n")
        self.append_output("[OK] Semantic analysis\n")
        self.append_output("[OK] AST Tree generated\n")
        self.append_output("[OK] TAC generated\n")
        self.append_output("[OK] TAC optimized generated\n")
        self.append_output("[OK] Target code generated\n")
        self.append_output("[OK] VM execution\n" if vm_executed else "[SKIP] VM execution: main function not found\n")
        self.append_output("\nArtifacts:\n")
        self.append_output(f"- {artifacts.get('ast_modern_svg', self.ast_modern_svg_path)}\n")
        self.append_output(f"- {artifacts.get('tac', self.current_artifacts['tac'])}\n")
        self.append_output(f"- {artifacts.get('tac_optimized', self.current_artifacts['tac_optimized'])}\n")
        self.append_output(f"- {artifacts.get('target_code', self.current_artifacts['target_code'])}\n")

        if vm_executed and vm_resultado is not None:
            self.append_output("\nVM Output:\n")
            output = vm_resultado.get("output") or []
            if output:
                for line in output:
                    self.append_output(str(line) + "\n")
            else:
                self.append_output("(no output)\n")
            self.append_output(f"\nVM Return Value: {vm_resultado.get('return_value')}\n")
        elif parser_output.strip():
            self.append_output("\nParser messages:\n")
            self.append_output(parser_output.strip() + "\n")

    def load_generated_artifacts(self, resultado=None):
        artifacts = dict(self.current_artifacts)
        artifacts.update((resultado or {}).get("artifacts") or {})
        self._load_file_into_textbox(self.tac_text, artifacts.get("tac"), "TAC no disponible.")
        self._load_file_into_textbox(
            self.tac_optimized_text,
            artifacts.get("tac_optimized"),
            "TAC optimizado no disponible.",
        )
        self._load_file_into_textbox(
            self.target_text,
            artifacts.get("target_code"),
            "Target code no disponible.",
        )

    def _load_file_into_textbox(self, textbox, path, fallback):
        textbox.delete("1.0", tk.END)
        if not path or not os.path.exists(path):
            textbox.insert("1.0", fallback)
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                textbox.insert("1.0", f.read())
        except Exception as exc:
            textbox.insert("1.0", f"{fallback}\nError: {exc}")

    # ---------------------------------------------------------------------
    # Compilation workflow
    # ---------------------------------------------------------------------
    def compile_code(self):
        self._run_pipeline(mode="all")

    def run_lexer_only(self):
        self._run_pipeline(mode="lexer")

    def run_parser_sdt_only(self):
        self._run_pipeline(mode="parser")

    def _run_pipeline(self, mode="all"):
        self.reset_outputs(keep_code=True)
        self.reset_stage_cards()
        code = self.get_code().strip()
        if not code:
            self.append_output("[ERROR] No hay código para compilar.\n")
            self.append_error("No hay código para compilar.")
            self.update_status("Sin código", "error")
            return

        source_label = self.current_file_path or "<editor>"
        self._prepare_output_dir(source_label)

        self.append_output("=" * 72 + "\n")
        self.append_output("COMPILER RUN\n")
        self.append_output("=" * 72 + "\n")
        self.append_output(f"Input: {source_label}\n")
        self.append_output(f"Output directory: {self.current_output_dir}\n\n")

        lexer_stdout = io.StringIO()
        with redirect_stdout(lexer_stdout):
            tokens = lector.analizeterminal(code)
        lexer_messages = lexer_stdout.getvalue().strip()

        if lexer_messages:
            self.append_output(lexer_messages + "\n")

        if tokens is None:
            self.set_stage("lexico", "error")
            self.append_output("[ERROR] Falló el análisis léxico.\n")
            self.append_error(lexer_messages or "Error léxico: símbolo no reconocido.")
            self.update_status("Error léxico", "error")
            self.tabs.set("Errors")
            return

        self.last_tokens = tokens
        self.set_stage("lexico", "success")
        self.append_output(f"[OK] Análisis léxico correcto. Tokens generados: {len(tokens)}\n")
        self.load_tokens(tokens)
        self.highlight_syntax()

        if mode == "lexer":
            self.set_stage("sintactico", "pending")
            self.set_stage("semantico", "pending")
            self.update_status("Léxico correcto", "success")
            self.tabs.set("Tokens")
            return

        self.append_output("\n" + "=" * 72 + "\n")
        self.append_output("PARSER + SDT\n")
        self.append_output("=" * 72 + "\n")

        parser_stdout = io.StringIO()
        result = False
        try:
            with redirect_stdout(parser_stdout):
                try:
                    result = parser.analizar(
                        tokens,
                        ast_base_path=self.ast_output_base,
                        output_dir=self.current_output_dir,
                        verbose=False,
                        source_path=source_label,
                    )
                except TypeError:
                    # Compatibilidad con el parser original sin parámetro ast_base_path.
                    result = parser.analizar(tokens, ast_base_path=self.ast_output_base)
        except Exception as exc:
            parser_stdout.write(f"Error interno: {exc}\n")
            result = False

        parser_output = parser_stdout.getvalue()
        self.extract_and_show_errors(parser_output)

        if result:
            self.set_stage("sintactico", "success")
            self.set_stage("semantico", "success")
            self.update_status("Compilación correcta", "success")
            self.load_symbol_table()
            self.load_function_table()
            self.last_ast = getattr(parser, "ultimo_ast", None)
            if self.last_ast is not None:
                self.export_ast_graphviz_modern(self.last_ast)
                self.load_graphviz_image()
            else:
                self.load_graphviz_image()

            resultado_detallado = self._get_parser_result()
            self._append_success_summary(resultado_detallado, parser_output)
            self.load_generated_artifacts(resultado_detallado)
            self.tabs.set("Output")
        else:
            self.append_output(parser_output)
            if "Syntax error" in parser_output:
                self.set_stage("sintactico", "error")
                self.set_stage("semantico", "pending")
                self.update_status("Error sintáctico", "error")
            elif "SDT error" in parser_output or "Semantic error" in parser_output:
                self.set_stage("sintactico", "success")
                self.set_stage("semantico", "error")
                self.update_status("Error semántico", "error")
            else:
                self.set_stage("sintactico", "error")
                self.set_stage("semantico", "error")
                self.update_status("Compilación fallida", "error")
            self.tabs.set("Errors")

    def extract_ast_text(self, output):
        if not hasattr(self, "ast_text"):
            return
        self.ast_text.delete("1.0", tk.END)
        if "Parse/AST tree:" not in output:
            return
        ast_part = output.split("Parse/AST tree:", 1)[1]
        ast_part = ast_part.split("AST DOT generated", 1)[0]
        ast_part = ast_part.split("AST image generated", 1)[0]
        self.ast_text.insert("1.0", ast_part.strip())

    def extract_and_show_errors(self, output):
        self.error_text.delete("1.0", tk.END)
        error_lines = []
        for line in output.splitlines():
            lower = line.lower()
            if any(word in lower for word in ["error", "unexpected", "expected", "failed", "falló"]):
                error_lines.append(line)
        if error_lines:
            self.error_text.insert("1.0", "\n".join(error_lines))
        else:
            self.error_text.insert("1.0", "Sin errores detectados en la última ejecución.")

    # ---------------------------------------------------------------------
    # Tables
    # ---------------------------------------------------------------------
    def load_tokens(self, tokens):
        self._clear_tree(self.token_tree)
        for tipo, valor, linea, columna in tokens:
            self.token_tree.insert("", tk.END, values=(tipo, valor, linea, columna))

    def load_symbol_table(self):
        self._clear_tree(self.symbol_tree)
        if not tabla_simbolos.simbolos:
            self.symbol_tree.insert("", tk.END, values=("(vacía)", "-", "-", "-"))
            return
        for name, data in tabla_simbolos.simbolos.items():
            es_array = data.get('es_array', False)
            if es_array:
                value = "[" + ", ".join(str(formatear_valor(v)) for v in data.get('valor', [])) + "]"
                detail = f"array[{data.get('tamano', '?')}]"
            else:
                value = formatear_valor(data.get('valor'))
                detail = "variable"
            self.symbol_tree.insert("", tk.END, values=(name, data.get('tipo', 'unknown'), value, detail))

    def load_function_table(self):
        self._clear_tree(self.function_tree)
        if not tabla_funciones.funciones:
            self.function_tree.insert("", tk.END, values=("(vacía)", "-", "-"))
            return
        for name, data in tabla_funciones.funciones.items():
            params = ", ".join(f"{p.get('tipo')} {p.get('nombre')}" for p in data.get('parametros', []))
            self.function_tree.insert("", tk.END, values=(name, data.get('tipo_retorno', '-'), params or "sin parámetros"))

    def load_parse_table(self):
        if not hasattr(self, "parse_table_text"):
            return
        try:
            from parser_sdt.parsertable import tabla_action, tabla_goto
        except Exception as exc:
            self.parse_table_text.delete("1.0", tk.END)
            self.parse_table_text.insert("1.0", f"No se pudo cargar la tabla LALR: {exc}")
            return

        self.parse_table_text.delete("1.0", tk.END)
        self.parse_table_text.insert(tk.END, "TABLA ACTION (primeros 60 estados)\n")
        self.parse_table_text.insert(tk.END, "=" * 72 + "\n")
        for state, actions in list(tabla_action.items())[:60]:
            self.parse_table_text.insert(tk.END, f"Estado {state}: {actions}\n")
        if len(tabla_action) > 60:
            self.parse_table_text.insert(tk.END, f"\n... y {len(tabla_action) - 60} estados más\n")
        self.parse_table_text.insert(tk.END, "\nTABLA GOTO (primeros 60 estados)\n")
        self.parse_table_text.insert(tk.END, "=" * 72 + "\n")
        for state, gotos in list(tabla_goto.items())[:60]:
            self.parse_table_text.insert(tk.END, f"Estado {state}: {gotos}\n")

    def _clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    # ---------------------------------------------------------------------
    # AST Treeview and Canvas
    # ---------------------------------------------------------------------
    def populate_ast_tree(self, ast):
        if not hasattr(self, "ast_tree"):
            return
        self._clear_tree(self.ast_tree)

        def add_node(parent, node):
            value = self._node_value(node)
            pos = self._node_pos(node)
            item = self.ast_tree.insert(parent, tk.END, text=node.tipo, values=(value, pos), open=True)
            for child in getattr(node, 'hijos', []) or []:
                add_node(item, child)

        if ast is None:
            self.ast_tree.insert("", tk.END, text="Sin AST", values=("-", "-"))
            return
        add_node("", ast)

    def populate_ast_tree_from_text(self):
        if not hasattr(self, "ast_tree") or not hasattr(self, "ast_text"):
            return
        self._clear_tree(self.ast_tree)
        content = self.ast_text.get("1.0", "end-1c")
        if not content.strip():
            self.ast_tree.insert("", tk.END, text="Sin AST", values=("-", "-"))
            return
        stack = []
        for raw_line in content.splitlines():
            if not raw_line.strip():
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            level = indent // 2
            label = raw_line.strip()
            parent = stack[level - 1] if level > 0 and len(stack) >= level else ""
            item = self.ast_tree.insert(parent, tk.END, text=label, values=("", ""), open=True)
            if len(stack) <= level:
                stack.append(item)
            else:
                stack[level] = item

    def draw_ast_canvas(self, ast):
        if not hasattr(self, "ast_canvas"):
            return
        self.ast_canvas.delete("all")

        if ast is None:
            self.draw_ast_placeholder("Sin AST disponible.")
            return

        scale = self.ast_scale

        font_size = max(8, int(10 * scale))
        font = tkfont.Font(family="Menlo", size=font_size, weight="bold")

        level_gap = 105 * scale
        sibling_gap = 34 * scale
        subtree_gap = 42 * scale
        margin_x = 80 * scale
        margin_y = 70 * scale

        node_sizes = {}
        subtree_widths = {}
        positions = {}

        def get_children(node):
            return getattr(node, "hijos", []) or []

        def measure_node(node):
            label = self._node_label(node)
            lines = label.split("\n")

            text_width = max(font.measure(line) for line in lines) if lines else 60
            line_height = font.metrics("linespace")

            padding_x = int(28 * scale)
            padding_y = int(16 * scale)

            width = text_width + padding_x
            height = len(lines) * line_height + padding_y

            width = max(int(82 * scale), min(width, int(190 * scale)))
            height = max(int(42 * scale), height)

            node_sizes[id(node)] = (width, height)
            return width, height

        def measure_subtree(node):
            node_w, _ = measure_node(node)
            children = get_children(node)

            if not children:
                subtree_widths[id(node)] = node_w
                return node_w

            children_width = 0

            for i, child in enumerate(children):
                children_width += measure_subtree(child)
                if i < len(children) - 1:
                    children_width += sibling_gap

            width = max(node_w, children_width)
            subtree_widths[id(node)] = width
            return width

        def layout(node, left, depth):
            subtree_w = subtree_widths[id(node)]
            node_w, _ = node_sizes[id(node)]

            x = left + subtree_w / 2
            y = margin_y + depth * level_gap

            positions[id(node)] = (x, y)

            children = get_children(node)
            if not children:
                return

            children_total = sum(subtree_widths[id(child)] for child in children)
            children_total += sibling_gap * (len(children) - 1)

            child_left = left + (subtree_w - children_total) / 2

            for child in children:
                layout(child, child_left, depth + 1)
                child_left += subtree_widths[id(child)] + sibling_gap

        def max_depth(node):
            children = get_children(node)

            if not children:
                return 0

            return 1 + max(max_depth(child) for child in children)

        total_width = measure_subtree(ast) + margin_x * 2
        layout(ast, margin_x, 0)

        def draw_edges(node):
            x, y = positions[id(node)]
            node_w, node_h = node_sizes[id(node)]

            for child in get_children(node):
                cx, cy = positions[id(child)]
                child_w, child_h = node_sizes[id(child)]

                self.ast_canvas.create_line(
                    x,
                    y + node_h / 2 + 4 * scale,
                    cx,
                    cy - child_h / 2 - 4 * scale,
                    fill=self.THEME.get("ast_edge", "#38546f"),
                    width=max(1, int(2 * scale)),
                )

                draw_edges(child)

        def draw_nodes(node):
            x, y = positions[id(node)]
            width, height = node_sizes[id(node)]

            label = self._node_label(node)
            fill = self._ast_color(getattr(node, "tipo", ""))
            outline = self.THEME.get("ast_outline", "#60a5fa")

            # Rectángulo limpio. En Tkinter se ve mejor que un borde redondeado mal suavizado.
            self.ast_canvas.create_rectangle(
                x - width / 2,
                y - height / 2,
                x + width / 2,
                y + height / 2,
                fill=fill,
                outline=outline,
                width=max(1, int(2 * scale)),
            )

            self.ast_canvas.create_text(
                x,
                y,
                text=label,
                fill="#f8fafc",
                font=("Menlo", font_size, "bold"),
                justify="center",
            )

            for child in get_children(node):
                draw_nodes(child)

        draw_edges(ast)
        draw_nodes(ast)

        total_height = margin_y * 2 + (max_depth(ast) + 1) * level_gap

        self.ast_canvas.configure(
            scrollregion=(
                0,
                0,
                max(total_width, self.ast_canvas.winfo_width()),
                max(total_height, self.ast_canvas.winfo_height()),
            )
        )

    def _node_box_size(self, node):
        label = self._node_label(node)

        font_size = max(8, int(10 * self.ast_scale))
        font = tkfont.Font(family="Consolas", size=font_size, weight="bold")

        lines = label.split("\n")

        text_width = max(font.measure(line) for line in lines) if lines else 80
        line_height = font.metrics("linespace")

        padding_x = int(28 * self.ast_scale)
        padding_y = int(18 * self.ast_scale)

        width = text_width + padding_x
        height = len(lines) * line_height + padding_y

        min_width = int(88 * self.ast_scale)
        max_width = int(260 * self.ast_scale)
        min_height = int(44 * self.ast_scale)

        width = max(min_width, min(width, max_width))
        height = max(min_height, height)

        return width, height

    def draw_ast_placeholder(self, message):
        if not hasattr(self, "ast_canvas"):
            return
        self.ast_canvas.delete("all")
        self.ast_canvas.create_text(30, 30, anchor="nw", fill=self.THEME['muted'], text=message, font=("Segoe UI", 13))
        self.ast_canvas.configure(scrollregion=(0, 0, 900, 500))

    def zoom_ast_canvas(self, factor):
        self.ast_scale = max(0.45, min(2.5, self.ast_scale * factor))
        if self.last_ast is not None:
            self.draw_ast_canvas(self.last_ast)

    def reset_ast_canvas_zoom(self):
        self.ast_scale = 1.0
        if self.last_ast is not None:
            self.draw_ast_canvas(self.last_ast)

    def _node_label(self, node):
        tipo = str(getattr(node, "tipo", "NODE"))
        valor = self._node_value(node)

        tipo = self._short_node_text(tipo, 20)

        if valor not in {None, "", "None"}:
            valor = self._short_node_text(str(valor), 22)
            return f"{tipo}\n'{valor}'"

        return tipo
    
    def _short_node_text(self, text, limit=28):
        text = str(text)

        if len(text) <= limit:
            return text

        return text[: limit - 1] + "…"

    def _node_value(self, node):
        value = getattr(node, 'valor', None)
        if value is None:
            return ""
        try:
            return str(formatear_valor(value))
        except Exception:
            return str(value)

    def _node_pos(self, node):
        line = getattr(node, 'linea', None)
        col = getattr(node, 'columna', None)
        if line is None:
            return "-"
        return f"{line}:{col}"

    def _ast_color(self, node_type):
        node_type = str(node_type).upper()

        if node_type in {"PROGRAM", "STMT_LIST", "BLOCK"}:
            return "#0f2742"

        if node_type in {"FUNCTION", "FUNCTION_DECL", "FUNCTION_HEADER", "CALL"}:
            return "#0e3a5b"

        if node_type in {
            "DECL",
            "DECL_LIST",
            "DECL_ARRAY",
            "DECL_ARRAY_ITEM",
            "TYPE",
            "PARAM",
            "PARAMS",
            "PARAM_LIST",
            "RETURN_TYPE",
        }:
            return "#164e63"

        if node_type in {
            "ASSIGN",
            "ASSIGN_ARRAY",
            "ARRAY_ASSIGN",
            "RETURN",
            "PRINT",
            "PRINTF",
            "IF",
            "ELSE",
            "WHILE",
            "FOR",
            "SWITCH",
            "CASE",
            "DEFAULT",
            "BREAK",
            "CONTINUE",
        }:
            return "#075985"

        if node_type in {
            "+",
            "-",
            "*",
            "/",
            "%",
            "&&",
            "||",
            "==",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
            "NEG",
            "POS",
            "!",
        }:
            return "#1d4ed8"

        if node_type in {"CONST", "ID", "ARRAY_ACCESS"}:
            return "#1e3a5f"

        return "#1e293b"

    def _round_rect(self, canvas, x1, y1, x2, y2, radius=12, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    # ---------------------------------------------------------------------
    # Modern Graphviz export / viewer
    # ---------------------------------------------------------------------
    def export_ast_graphviz_modern(self, ast):
        """
        Genera ast_modern.dot y ast_modern.svg en la carpeta outputs/<run>.
        Para previsualizar dentro de Tkinter se usa una imagen temporal en .gui_cache.
        """
        if ast is None:
            return

        if not GRAPHVIZ_AVAILABLE:
            self.append_output("\n[WARN] Graphviz no está disponible. Instala con: brew install graphviz\n")
            return

        os.makedirs(self.current_output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.ast_graphviz_preview_png_path), exist_ok=True)

        counter = [0]

        lines = [
            "digraph AST {",
            "    graph [",
            "        bgcolor=\"#0f172a\",",
            "        pad=\"0.45\",",
            "        nodesep=\"0.42\",",
            "        ranksep=\"0.72\",",
            "        splines=\"line\",",
            "        outputorder=\"edgesfirst\"",
            "    ];",
            "",
            "    node [",
            "        shape=box,",
            "        style=\"rounded,filled\",",
            "        fontname=\"Menlo\",",
            "        fontsize=12,",
            "        margin=\"0.16,0.09\",",
            "        color=\"#7dd3fc\",",
            "        penwidth=1.6,",
            "        fontcolor=\"#f8fafc\"",
            "    ];",
            "",
            "    edge [",
            "        color=\"#46637f\",",
            "        penwidth=1.25,",
            "        arrowsize=0.65",
            "    ];",
            "",
        ]

        def esc(text):
            return (
                str(text)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
            )

        def short_text(text, limit=28):
            text = str(text)
            if len(text) <= limit:
                return text
            return text[: limit - 1] + "…"

        def node_label(node):
            tipo = short_text(getattr(node, "tipo", "NODE"), 26)
            value = self._node_value(node)

            if value not in {None, "", "None"}:
                value = short_text(value, 30)
                return f"{tipo}\n'{value}'"

            return tipo

        def rec(node):
            node_id = f"n{counter[0]}"
            counter[0] += 1

            label = node_label(node)
            fill = self._ast_color(getattr(node, "tipo", ""))

            lines.append(
                f'    {node_id} [label="{esc(label)}", fillcolor="{fill}"];'
            )

            for child in getattr(node, "hijos", []) or []:
                child_id = rec(child)
                lines.append(f"    {node_id} -> {child_id};")

            return node_id

        rec(ast)
        lines.append("}")

        with open(self.ast_modern_dot_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        try:
            # SVG vectorial: este es el archivo de máxima calidad.
            subprocess.run(
                [
                    "dot",
                    "-Tsvg",
                    self.ast_modern_dot_path,
                    "-o",
                    self.ast_modern_svg_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # PNG para mostrar dentro de Tkinter.
            self._render_graphviz_preview_png()

        except Exception as exc:
            self.append_output(f"\n[WARN] No se pudo generar AST SVG con Graphviz: {exc}\n")


    def _render_graphviz_preview_png(self):
        """
        Regenera el PNG de vista previa desde el DOT.
        No escala una imagen vieja; Graphviz vuelve a renderizar con DPI nuevo.
        """
        if not GRAPHVIZ_AVAILABLE:
            return

        if not os.path.exists(self.ast_modern_dot_path):
            return

        # 120 dpi base se ve nítido. El zoom modifica el DPI.
        dpi = max(120, min(400, int(220 * self.graphviz_scale)))

        try:
            subprocess.run(
                [
                    "dot",
                    "-Tpng",
                    f"-Gdpi={dpi}",
                    self.ast_modern_dot_path,
                    "-o",
                    self.ast_graphviz_preview_png_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception as exc:
            self.append_output(f"\n[WARN] No se pudo renderizar preview PNG del AST: {exc}\n")


    def load_graphviz_image(self):
        self.graphviz_canvas.delete("all")

        path = self.ast_graphviz_preview_png_path

        if not os.path.exists(path):
            self.graphviz_canvas.create_text(
                30,
                30,
                anchor="nw",
                fill=self.THEME['muted'],
                text="No hay AST Tree disponible.\nCompila código para generar ast_modern.svg."
            )
            return

        if not PILLOW_AVAILABLE:
            self.graphviz_canvas.create_text(
                30,
                30,
                anchor="nw",
                fill=self.THEME['warning'],
                text="No se puede previsualizar el SVG dentro de Tkinter.\nInstala Pillow o usa Abrir SVG."
            )
            return

        try:
            image = Image.open(path)

            self.ast_graphviz_photo = ImageTk.PhotoImage(image)

            self.graphviz_canvas.create_image(
                20,
                20,
                image=self.ast_graphviz_photo,
                anchor="nw"
            )

            self.graphviz_canvas.configure(
                scrollregion=(0, 0, image.width + 40, image.height + 40)
            )

        except Exception as exc:
            self.graphviz_canvas.create_text(
                30,
                30,
                anchor="nw",
                fill=self.THEME['error'],
                text=f"Error cargando AST Graphviz:\n{exc}"
            )


    def zoom_graphviz(self, factor):
        self.graphviz_scale = max(0.30, min(2.20, self.graphviz_scale * factor))

        if self.last_ast is not None:
            self._render_graphviz_preview_png()

        self.load_graphviz_image()


    def reset_graphviz_zoom(self):
        self.graphviz_scale = 1.0

        if self.last_ast is not None:
            self._render_graphviz_preview_png()

        self.load_graphviz_image()


    def fit_graphviz_to_view(self):
        """
        Ajusta el AST al tamaño visible del canvas.
        Usa una imagen base a escala 1.0 para calcular el factor.
        """
        if self.last_ast is None:
            return

        old_scale = self.graphviz_scale
        self.graphviz_scale = 1.0
        self._render_graphviz_preview_png()

        if not os.path.exists(self.ast_graphviz_preview_png_path) or not PILLOW_AVAILABLE:
            self.graphviz_scale = old_scale
            self.load_graphviz_image()
            return

        try:
            image = Image.open(self.ast_graphviz_preview_png_path)

            canvas_w = max(300, self.graphviz_canvas.winfo_width() - 60)
            canvas_h = max(250, self.graphviz_canvas.winfo_height() - 60)

            scale_x = canvas_w / max(1, image.width)
            scale_y = canvas_h / max(1, image.height)

            self.graphviz_scale = max(0.30, min(2.20, min(scale_x, scale_y)))
            self._render_graphviz_preview_png()
            self.load_graphviz_image()

        except Exception:
            self.graphviz_scale = old_scale
            self.load_graphviz_image()


    def open_graphviz_svg(self):
        if not os.path.exists(self.ast_modern_svg_path):
            messagebox.showinfo("Abrir AST SVG", "Todavía no hay SVG de AST para abrir.")
            return

        svg_path = os.path.abspath(self.ast_modern_svg_path)

        if sys.platform == "darwin":  # macOS
            browsers = [
                "Google Chrome",
                "Safari",
                "Firefox",
                "Microsoft Edge",
                "Brave Browser",
                "Arc",
            ]

            for browser in browsers:
                try:
                    subprocess.run(
                        ["open", "-a", browser, svg_path],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
                except Exception:
                    pass

            messagebox.showwarning(
                "Abrir AST SVG",
                "No encontré un navegador compatible instalado. "
                "Se intentará abrir con la aplicación predeterminada."
            )

        webbrowser.open_new_tab(Path(svg_path).resolve().as_uri())


    def export_graphviz_svg(self):
        if not os.path.exists(self.ast_modern_svg_path):
            messagebox.showinfo("Exportar AST SVG", "Todavía no hay SVG de AST para exportar.")
            return

        destination = filedialog.asksaveasfilename(
            title="Guardar AST como SVG",
            defaultextension=".svg",
            filetypes=[
                ("SVG", "*.svg"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if destination:
            shutil.copyfile(self.ast_modern_svg_path, destination)
            messagebox.showinfo("Exportar AST SVG", f"AST SVG exportado en:\n{destination}")


    def export_graphviz_image(self):
        if not os.path.exists(self.ast_graphviz_preview_png_path):
            messagebox.showinfo("Exportar AST PNG", "Todavía no hay imagen de AST para exportar.")
            return

        destination = filedialog.asksaveasfilename(
            title="Guardar AST como PNG",
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if destination:
            shutil.copyfile(self.ast_graphviz_preview_png_path, destination)
            messagebox.showinfo("Exportar AST PNG", f"AST PNG exportado en:\n{destination}")

    # ---------------------------------------------------------------------
    # Status and output helpers
    # ---------------------------------------------------------------------
    def reset_stage_cards(self):
        self.set_stage("lexico", "idle")
        self.set_stage("sintactico", "idle")
        self.set_stage("semantico", "idle")

    def set_stage(self, stage, state):
        names = {"lexico": "Léxico", "sintactico": "Sintáctico", "semantico": "Semántico"}
        icons = {"idle": "○", "pending": "…", "success": "✓", "error": "✕"}
        colors = {
            "idle": self.THEME['muted'],
            "pending": self.THEME['warning'],
            "success": self.THEME['success'],
            "error": self.THEME['error'],
        }
        label = self.stage_cards[stage]
        label.configure(text=f"{icons[state]} {names[stage]}", text_color=colors[state])

    def update_status(self, message, status_type="normal"):
        colors = {"success": self.THEME['success'], "error": self.THEME['error'], "warning": self.THEME['warning'], "normal": self.THEME['muted']}
        self.status_label.configure(text=message, text_color=colors.get(status_type, self.THEME['muted']))

    def append_output(self, text):
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)

    def append_error(self, text):
        self.error_text.insert(tk.END, text + "\n")
        self.error_text.see(tk.END)

    def reset_outputs(self, keep_code=True):
        for box in [self.output_text, self.error_text, self.tac_text,
                    self.tac_optimized_text, self.target_text]:
            box.delete("1.0", tk.END)
        self._clear_tree(self.token_tree)
        self._clear_tree(self.symbol_tree)
        self._clear_tree(self.function_tree)
        self.graphviz_canvas.delete("all")
        self.update_status("Listo", "success")
        if not keep_code:
            self.code_input.delete("1.0", tk.END)
            self.current_file_path = None
            self.update_line_numbers()
            self.schedule_highlight()
        self.set_placeholder_texts()

    def clear_all(self):
        self.reset_outputs(keep_code=False)
        self.reset_stage_cards()
        self.tabs.set("Output")

    def set_placeholder_texts(self):
        placeholders = {
            self.tac_text: "Compila código para generar TAC.",
            self.tac_optimized_text: "Compila código para generar TAC optimizado.",
            self.target_text: "Compila código para generar target code.",
        }
        for box, message in placeholders.items():
            box.delete("1.0", tk.END)
            box.insert("1.0", message)

        if hasattr(self, "graphviz_canvas"):
            self.graphviz_canvas.delete("all")
            self.graphviz_canvas.create_text(
                30,
                30,
                anchor="nw",
                fill=self.THEME['muted'],
                text="Compila código para generar el AST Tree."
            )

    # ---------------------------------------------------------------------
    # File operations
    # ---------------------------------------------------------------------
    def open_file(self):
        path = filedialog.askopenfilename(
            title="Abrir archivo de código",
            filetypes=[("Código C / texto", "*.c *.h *.txt"), ("Todos los archivos", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()
        self.current_file_path = path
        self.code_input.delete("1.0", tk.END)
        self.code_input.insert("1.0", content)
        self.update_line_numbers()
        self.schedule_highlight()
        self.update_status(f"Archivo cargado: {os.path.basename(path)}", "success")

    def save_file(self):
        path = filedialog.asksaveasfilename(
            title="Guardar código",
            defaultextension=".c",
            filetypes=[("Código C", "*.c"), ("Texto", "*.txt"), ("Todos los archivos", "*.*")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.get_code())
        self.current_file_path = path
        self.update_status(f"Código guardado: {os.path.basename(path)}", "success")


def main():
    root = ctk.CTk()
    app = CompilerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
