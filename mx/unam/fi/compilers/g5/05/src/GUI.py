# PENTA Compiler - documentación interna
# Interfaz gráfica de PENTA Compiler: concentra la experiencia visual, la ejecución del pipeline y la consulta de artefactos generados.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

import io
import html
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


# Agrupa toda la interfaz: editor, botones, pestañas de resultados, temas y acciones de compilación.
class CompilerGUI:
    """Interfaz principal de PENTA Compiler.

    Reúne el editor de código, los controles de compilación, las pestañas
    de resultados y los visores de artefactos. Su papel es presentar el
    flujo completo del compilador de forma accesible sin esconder las fases
    internas que se generan en cada ejecución.
    """

    THEMES = {
        "dark": {
            'name': 'Dark',
            'appearance': 'dark',
            'bg': '#0f172a',
            'panel': '#111827',
            'panel_2': '#0b1220',
            'panel_3': '#1e293b',
            'border': '#334155',
            'text': '#e5e7eb',
            'muted': '#94a3b8',
            'accent': '#38bdf8',
            'accent_2': '#2563eb',
            'accent_hover': '#1d4ed8',
            'button_hover': '#334155',
            'danger': '#7f1d1d',
            'danger_hover': '#991b1b',
            'vm_bg': '#020617',
            'success': '#22c55e',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'purple': '#a78bfa',
            'orange': '#fb923c',
            'green': '#86efac',
            'type': '#60a5fa',
            'operator': '#f472b6',
            'punctuation': '#cbd5e1',
            'comment': '#64748b',
            'ast_edge': '#46637f',
            'ast_outline': '#7dd3fc',
            'ast_palette': {
                'program': '#0f2742', 'function': '#0e3a5b',
                'declaration': '#164e63', 'control': '#075985',
                'operator': '#1d4ed8', 'leaf': '#1e3a5f', 'default': '#1e293b'
            },
            'tag_function': '#93c5fd', 'tag_label': '#facc15',
            'tag_jump': '#fb923c', 'tag_call': '#c084fc',
            'tag_return': '#86efac', 'tag_memory': '#fde68a',
            'tag_arithmetic': '#60a5fa', 'tag_logic': '#38bdf8',
            'tag_assign': '#e5e7eb', 'tag_io': '#67e8f9',
        },
        "light": {
            'name': 'Light',
            'appearance': 'light',
            'bg': '#f8fafc',
            'panel': '#ffffff',
            'panel_2': '#f1f5f9',
            'panel_3': '#e2e8f0',
            'border': '#cbd5e1',
            'text': '#0f172a',
            'muted': '#475569',
            'accent': '#0284c7',
            'accent_2': '#2563eb',
            'accent_hover': '#1d4ed8',
            'button_hover': '#cbd5e1',
            'danger': '#dc2626',
            'danger_hover': '#b91c1c',
            'vm_bg': '#ffffff',
            'success': '#16a34a',
            'warning': '#d97706',
            'error': '#dc2626',
            'purple': '#7c3aed',
            'orange': '#ea580c',
            'green': '#15803d',
            'type': '#2563eb',
            'operator': '#be185d',
            'punctuation': '#334155',
            'comment': '#64748b',
            'ast_edge': '#64748b',
            'ast_outline': '#0284c7',
            'ast_palette': {
                'program': '#dbeafe', 'function': '#bae6fd',
                'declaration': '#ccfbf1', 'control': '#bfdbfe',
                'operator': '#c7d2fe', 'leaf': '#e0f2fe', 'default': '#f1f5f9'
            },
            'tag_function': '#1d4ed8', 'tag_label': '#b45309',
            'tag_jump': '#c2410c', 'tag_call': '#7c3aed',
            'tag_return': '#15803d', 'tag_memory': '#92400e',
            'tag_arithmetic': '#2563eb', 'tag_logic': '#0891b2',
            'tag_assign': '#0f172a', 'tag_io': '#0e7490',
        },
        "neutral": {
            'name': 'Neutral',
            'appearance': 'dark',
            'bg': '#18181b',
            'panel': '#27272a',
            'panel_2': '#1f1f23',
            'panel_3': '#3f3f46',
            'border': '#52525b',
            'text': '#e4e4e7',
            'muted': '#a1a1aa',
            'accent': '#d4d4d8',
            'accent_2': '#71717a',
            'accent_hover': '#52525b',
            'button_hover': '#52525b',
            'danger': '#7f1d1d',
            'danger_hover': '#991b1b',
            'vm_bg': '#111113',
            'success': '#22c55e',
            'warning': '#eab308',
            'error': '#ef4444',
            'purple': '#c4b5fd',
            'orange': '#fdba74',
            'green': '#86efac',
            'type': '#a5b4fc',
            'operator': '#f0abfc',
            'punctuation': '#d4d4d8',
            'comment': '#71717a',
            'ast_edge': '#71717a',
            'ast_outline': '#d4d4d8',
            'ast_palette': {
                'program': '#27272a', 'function': '#3f3f46',
                'declaration': '#52525b', 'control': '#3f3f46',
                'operator': '#71717a', 'leaf': '#27272a', 'default': '#1f1f23'
            },
            'tag_function': '#d4d4d8', 'tag_label': '#eab308',
            'tag_jump': '#fdba74', 'tag_call': '#c4b5fd',
            'tag_return': '#86efac', 'tag_memory': '#fef08a',
            'tag_arithmetic': '#a5b4fc', 'tag_logic': '#67e8f9',
            'tag_assign': '#e4e4e7', 'tag_io': '#a7f3d0',
        },
    }

    THEME = THEMES["dark"]

    SAMPLE_CODE = """int main() {
    float y = (2 + 3) * 4;
    int values[3];
    values[0] = 10;

    if (y > values[0]) {
        printf("result = %f", y);
    }

    return 0;
}"""

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def __init__(self, root):
        self.root = root
        self.root.title("PENTA Compiler")
        self.root.geometry("1500x860")
        self.root.minsize(1180, 720)
        self.code_font_family = self._select_code_font()
        self.ui_font_family = "Segoe UI"
        self.theme_name = "dark"
        self.THEME = dict(self.THEMES[self.theme_name])
        self.stage_states = {"lexico": "idle", "sintactico": "idle", "semantico": "idle"}
        self.status_text = "Ready"
        self.status_type = "success"

        self.editor_font_size = 12
        self.output_font_size = 11
        self.ast_scale = 1.0
        self.graphviz_scale = 1.0
        self.highlight_after_id = None
        self.last_tokens = []
        self.last_ast = None
        self.ast_photo = None
        self.ast_graphviz_photo = None
        self.team_logo_photo = None
        self.team_logo_source_path = None
        self.current_file_path = None
        self.outputs_root = os.path.join(SRC_ROOT, "outputs")
        self.current_output_dir = None
        self.current_artifacts = {}
        self._set_output_dir(os.path.join(self.outputs_root, "gui_run"))
        self._ensure_grammar_viewer(silent=True)

        ctk.set_appearance_mode(self.THEME.get("appearance", "dark"))
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _get_team_logo_path(self):
        """Selecciona el logo más adecuado para el tema visual activo."""
        assets_dir = os.path.join(SRC_ROOT, "assets")
        candidates = [
            os.path.join(assets_dir, f"logo_{self.theme_name}.png"),
            os.path.join(assets_dir, "logo.png"),
        ]

        for path in candidates:
            if os.path.exists(path):
                return path

        return None

    # Carga información externa y la adapta para mostrarla o procesarla.
    def _load_team_logo(self, max_size=(96, 96)):
        if not PILLOW_AVAILABLE:
            return None

        logo_path = self._get_team_logo_path()
        if not logo_path:
            self.team_logo_source_path = None
            return None

        try:
            image = Image.open(logo_path)
            image.thumbnail(max_size)
            self.team_logo_photo = ImageTk.PhotoImage(image)
            self.team_logo_source_path = logo_path
            return self.team_logo_photo
        except Exception:
            self.team_logo_source_path = None
            return None


    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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


    # Ajusta estilos, eventos o parámetros visuales antes de usar la interfaz.
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

    # Construye una estructura o grupo de rutas a partir del estado actual.
    def _build_layout(self):
        self.root.configure(fg_color=self.THEME['bg'])
        self.root.grid_columnconfigure(0, weight=4, uniform="main")
        self.root.grid_columnconfigure(1, weight=7, uniform="main")
        self.root.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.root, fg_color=self.THEME['panel'], corner_radius=18)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)

        logo = self._load_team_logo()
        if logo is not None:
            logo_label = tk.Label(
                header,
                image=logo,
                bg=self.THEME['panel'],
                borderwidth=0,
                highlightthickness=0,
            )
            logo_label.grid(row=0, column=0, sticky="w", padx=(18, 10), pady=10)
        else:
            ctk.CTkLabel(
                header,
                text="PENTA\ncode",
                font=("Arial", 20, "bold"),
                text_color=self.THEME['accent'],
            ).grid(row=0, column=0, sticky="w", padx=(18, 10), pady=10)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w", padx=8, pady=14)
        ctk.CTkLabel(
            title_box,
            text="PENTA Compiler",
            font=("Segoe UI", 24, "bold"),
            text_color=self.THEME['text'],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Lexical · Syntax · Semantic · TAC · Optimization · Target Code",
            font=("Segoe UI", 13),
            text_color=self.THEME['muted'],
        ).pack(anchor="w", pady=(3, 0))

        self.stage_container = ctk.CTkFrame(header, fg_color="transparent")
        self.stage_container.grid(row=0, column=2, sticky="e", padx=18, pady=12)
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
            text="Code editor",
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
        self._primary_button(buttons, "Compile All", self.compile_code).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=4)
        self._secondary_button(buttons, "Lexical Only", self.run_lexer_only).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        self._secondary_button(buttons, "Parser + SDT", self.run_parser_sdt_only).grid(row=0, column=2, sticky="ew", padx=(6, 0), pady=4)
        self._secondary_button(buttons, "Open file", self.open_file).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=4)
        self._secondary_button(buttons, "Save", self.save_file).grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        self._danger_button(buttons, "Clear", self.clear_all).grid(row=1, column=2, sticky="ew", padx=(6, 0), pady=4)

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
        result_header.grid_columnconfigure(1, weight=0)
        result_header.grid_columnconfigure(2, weight=0)
        result_header.grid_columnconfigure(3, weight=0)

        ctk.CTkLabel(
            result_header,
            text="Results of compilation",
            font=("Segoe UI", 17, "bold"),
            text_color=self.THEME['text'],
        ).grid(row=0, column=0, sticky="w")

        theme_frame = ctk.CTkFrame(result_header, fg_color="transparent")
        theme_frame.grid(row=0, column=1, sticky="e", padx=(0, 8))
        self._theme_button(theme_frame, "Dark", "dark").pack(side="left", padx=2)
        self._theme_button(theme_frame, "Light", "light").pack(side="left", padx=2)
        self._theme_button(theme_frame, "Neutral", "neutral").pack(side="left", padx=2)

        self.grammar_button = self._secondary_button(
            result_header,
            "Grammar",
            self.show_grammar_window,
        )
        self.grammar_button.grid(row=0, column=2, sticky="e", padx=(0, 8))

        self.status_label = ctk.CTkLabel(
            result_header,
            text=self.status_text,
            font=("Segoe UI", 12, "bold"),
            text_color=self.THEME['success'],
        )
        self.status_label.grid(row=0, column=3, sticky="e")

        self.tabs = ctk.CTkTabview(right, fg_color=self.THEME['panel_2'], segmented_button_fg_color=self.THEME['panel_3'])
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))

        for name in [
            "Output", "Tokens", "Errors", "Symbol Table", "Function Table",
            "AST Tree", "TAC", "TAC Optimized", "Target Code", "VM Output"
        ]:
            self.tabs.add(name)
            self.tabs.tab(name).configure(fg_color=self.THEME['panel_2'])
            self.tabs.tab(name).grid_columnconfigure(0, weight=1)
            self.tabs.tab(name).grid_rowconfigure(0, weight=1)

        self.output_text = self._make_textbox(self.tabs.tab("Output"))
        self.error_text = self._make_textbox(self.tabs.tab("Errors"))

        self.tac_summary_label, self.tac_tree = self._make_instruction_view(
            self.tabs.tab("TAC"),
            "Compile code to generate TAC."
        )
        self.tac_optimized_summary_label, self.tac_optimized_tree = self._make_instruction_view(
            self.tabs.tab("TAC Optimized"),
            "Compile code to generate optimized TAC."
        )
        self.target_summary_label, self.target_tree = self._make_instruction_view(
            self.tabs.tab("Target Code"),
            "Compile code to generate target code."
        )

        self.vm_summary_label, self.vm_output_text = self._make_vm_output_view(
            self.tabs.tab("VM Output")
        )

        self.token_tree = self._make_tree(self.tabs.tab("Tokens"), ("tipo", "lexema", "linea", "columna"))
        self._heading(self.token_tree, "tipo", "Type", 130)
        self._heading(self.token_tree, "lexema", "Lexeme", 260)
        self._heading(self.token_tree, "linea", "Line", 80)
        self._heading(self.token_tree, "columna", "Column", 90)

        self.symbol_tree = self._make_tree(self.tabs.tab("Symbol Table"), ("nombre", "tipo", "valor", "detalle"))
        self._heading(self.symbol_tree, "nombre", "Name", 170)
        self._heading(self.symbol_tree, "tipo", "Type", 120)
        self._heading(self.symbol_tree, "valor", "Value", 260)
        self._heading(self.symbol_tree, "detalle", "Detail", 170)

        self.function_tree = self._make_tree(self.tabs.tab("Function Table"), ("nombre", "retorno", "parametros"))
        self._heading(self.function_tree, "nombre", "Function", 180)
        self._heading(self.function_tree, "retorno", "Return", 120)
        self._heading(self.function_tree, "parametros", "Parameters", 420)

        self._build_graphviz_tab()

    # Construye una estructura o grupo de rutas a partir del estado actual.
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

    # Construye una estructura o grupo de rutas a partir del estado actual.
    def _build_graphviz_tab(self):
        tab = self.tabs.tab("AST Tree")
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

        self._small_button(toolbar, "Open SVG Viewer", self.open_graphviz_svg).pack(side="left", padx=3)
        self._small_button(toolbar, "Export SVG", self.export_graphviz_svg).pack(side="left", padx=3)
        self._small_button(toolbar, "Export PNG", self.export_graphviz_image).pack(side="left", padx=3)
        self._small_button(toolbar, "Open AST folder", self.open_ast_folder).pack(side="left", padx=3)

        self.ast_info_text = ctk.CTkTextbox(
            tab,
            fg_color=self.THEME['panel_2'],
            text_color=self.THEME['text'],
            border_color=self.THEME['border'],
            border_width=1,
            corner_radius=12,
            font=(self.code_font_family, self.output_font_size),
            wrap="word",
        )
        self.ast_info_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.ast_info_text.insert(
            "1.0",
            "Compile code to generate the AST files.\n\n"
            "This tab no longer embeds a PNG preview. Use Open SVG Viewer to see the complete tree in your browser."
        )
        self.ast_info_text.configure(state="disabled")


    # Crea componentes visuales reutilizables dentro de la interfaz.
    def _make_textbox(self, parent):
        box = ctk.CTkTextbox(
            parent,
            fg_color=self.THEME['panel_2'],
            text_color=self.THEME['text'],
            border_color=self.THEME['border'],
            border_width=1,
            corner_radius=12,
            font=(self.code_font_family, self.output_font_size),
            wrap="word",
        )
        box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        return box

    # Crea componentes visuales reutilizables dentro de la interfaz.
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _heading(self, tree, column, text, width):
        tree.heading(column, text=text)
        tree.column(column, width=width, stretch=True)

    # Crea componentes visuales reutilizables dentro de la interfaz.
    def _make_instruction_view(self, parent, placeholder):
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        summary_frame = ctk.CTkFrame(parent, fg_color=self.THEME['panel_2'], corner_radius=10)
        summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        summary_frame.grid_columnconfigure(0, weight=1)

        summary = tk.Text(
            summary_frame,
            height=1,
            wrap="none",
            borderwidth=0,
            highlightthickness=0,
            bg=self.THEME['panel_2'],
            fg=self.THEME['muted'],
            insertbackground=self.THEME['accent'],
            selectbackground=self.THEME['accent_2'],
            selectforeground="#ffffff",
            font=(self.code_font_family, max(9, self.output_font_size)),
            padx=8,
            pady=6,
        )
        summary.grid(row=0, column=0, sticky="ew")
        summary_xbar = ctk.CTkScrollbar(summary_frame, orientation="horizontal", command=summary.xview)
        summary_xbar.grid(row=1, column=0, sticky="ew")
        summary.configure(xscrollcommand=summary_xbar.set)
        summary.configure(state="disabled")
        self._set_instruction_summary(summary, placeholder, self.THEME['muted'])

        frame = ctk.CTkFrame(parent, fg_color=self.THEME['panel_2'], corner_radius=12)
        frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        columns = ("num", "op", "arg1", "arg2", "result", "raw")
        tree = ttk.Treeview(frame, columns=columns, show="headings", style="Compiler.Treeview")
        tree.grid(row=0, column=0, sticky="nsew")

        headings = {
            "num": ("#", 54, False, "center"),
            "op": ("Op", 100, False, "center"),
            "arg1": ("Arg 1", 135, True, "w"),
            "arg2": ("Arg 2", 135, True, "w"),
            "result": ("Result / Dest", 145, True, "w"),
            "raw": ("Raw", 560, True, "w"),
        }
        for column, (title, width, stretch, anchor) in headings.items():
            tree.heading(column, text=title, anchor="center")
            tree.column(
                column,
                width=width,
                minwidth=45 if column == "num" else 75,
                stretch=stretch,
                anchor=anchor,
            )

        ybar = ctk.CTkScrollbar(frame, orientation="vertical", command=tree.yview)
        xbar = ctk.CTkScrollbar(frame, orientation="horizontal", command=tree.xview)
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)

        tag_colors = {
            "function": self.THEME.get('tag_function', self.THEME['accent']),
            "label": self.THEME.get('tag_label', self.THEME['warning']),
            "jump": self.THEME.get('tag_jump', self.THEME['orange']),
            "call": self.THEME.get('tag_call', self.THEME['purple']),
            "return": self.THEME.get('tag_return', self.THEME['green']),
            "memory": self.THEME.get('tag_memory', self.THEME['warning']),
            "arithmetic": self.THEME.get('tag_arithmetic', self.THEME['accent']),
            "logic": self.THEME.get('tag_logic', self.THEME['accent']),
            "assign": self.THEME.get('tag_assign', self.THEME['text']),
            "io": self.THEME.get('tag_io', self.THEME['accent']),
            "placeholder": self.THEME['muted'],
            "other": self.THEME['text'],
        }
        for tag, color in tag_colors.items():
            tree.tag_configure(tag, foreground=color)

        return summary, tree

    # Crea componentes visuales reutilizables dentro de la interfaz.
    def _make_vm_output_view(self, parent):
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        summary_frame = ctk.CTkFrame(parent, fg_color=self.THEME['panel_2'], corner_radius=10)
        summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        summary_frame.grid_columnconfigure(0, weight=1)

        summary = tk.Text(
            summary_frame,
            height=1,
            wrap="none",
            borderwidth=0,
            highlightthickness=0,
            bg=self.THEME['panel_2'],
            fg=self.THEME['muted'],
            insertbackground=self.THEME['accent'],
            selectbackground=self.THEME['accent_2'],
            selectforeground="#ffffff",
            font=(self.code_font_family, max(9, self.output_font_size)),
            padx=8,
            pady=6,
        )
        summary.grid(row=0, column=0, sticky="ew")
        summary_xbar = ctk.CTkScrollbar(summary_frame, orientation="horizontal", command=summary.xview)
        summary_xbar.grid(row=1, column=0, sticky="ew")
        summary.configure(xscrollcommand=summary_xbar.set)
        summary.configure(state="disabled")

        output = ctk.CTkTextbox(
            parent,
            fg_color=self.THEME.get('vm_bg', self.THEME['panel_2']),
            text_color=self.THEME['text'],
            border_color=self.THEME['border'],
            border_width=1,
            corner_radius=12,
            font=(self.code_font_family, self.output_font_size),
            wrap="none",
        )
        output.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        output.tag_config("success", foreground=self.THEME['success'])
        output.tag_config("warning", foreground=self.THEME['warning'])
        output.tag_config("error", foreground=self.THEME['error'])
        output.tag_config("muted", foreground=self.THEME['muted'])
        output.tag_config("accent", foreground=self.THEME['accent'])
        output.tag_config("prompt", foreground=self.THEME['green'])

        self._set_vm_summary(summary, "VM Output: compile code to run the VM.", self.THEME['muted'])
        output.insert("1.0", "Compile code to see the explicit output of the VM here.")
        output.configure(state="disabled")

        return summary, output

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _set_vm_summary(self, widget, text, color=None):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(fg=color or self.THEME['text'])
        widget.configure(state="disabled")
        widget.xview_moveto(0)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _set_instruction_summary(self, widget, text, color=None):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(fg=color or self.THEME['text'])
        widget.configure(state="disabled")
        widget.xview_moveto(0)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _autosize_instruction_columns(self, tree, rows):
        if not rows:
            return

        font = tkfont.Font(family=self.code_font_family, size=max(9, self.output_font_size - 1))
        specs = {
            "num": (54, 72),
            "op": (90, 135),
            "arg1": (110, 260),
            "arg2": (110, 260),
            "result": (125, 300),
            "raw": (430, 1250),
        }
        titles = {
            "num": "#",
            "op": "Op",
            "arg1": "Arg 1",
            "arg2": "Arg 2",
            "result": "Result / Dest",
            "raw": "Raw",
        }

        for column, (min_width, max_width) in specs.items():
            values = [str(row.get(column, "")) for row in rows]
            values.append(titles[column])
            widest = max(font.measure(value) for value in values) + 28
            width = max(min_width, min(max_width, widest))
            tree.column(column, width=width)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _theme_button(self, parent, text, theme_name):
        is_active = theme_name == self.theme_name
        fg = self.THEME['accent_2'] if is_active else self.THEME['panel_3']
        hover = self.THEME.get('accent_hover') if is_active else self.THEME.get('button_hover')
        return ctk.CTkButton(
            parent,
            text=text,
            command=lambda name=theme_name: self.set_theme(name),
            width=76,
            height=30,
            corner_radius=10,
            fg_color=fg,
            hover_color=hover,
            text_color="#ffffff" if is_active else self.THEME['text'],
            font=("Segoe UI", 11, "bold"),
        )

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def set_theme(self, theme_name):
        if theme_name not in self.THEMES:
            return

        if theme_name == self.theme_name:
            return

        state = self._capture_ui_state()
        self.theme_name = theme_name
        self.THEME = dict(self.THEMES[self.theme_name])
        ctk.set_appearance_mode(self.THEME.get('appearance', 'dark'))
        self._rebuild_interface(state)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _capture_ui_state(self):
        def get_text(widget):
            try:
                return widget.get("1.0", "end-1c")
            except Exception:
                return ""

        active_tab = None
        try:
            active_tab = self.tabs.get()
        except Exception:
            pass

        return {
            "code": get_text(getattr(self, "code_input", None)),
            "output": get_text(getattr(self, "output_text", None)),
            "errors": get_text(getattr(self, "error_text", None)),
            "active_tab": active_tab,
            "stage_states": dict(getattr(self, "stage_states", {})),
            "status_text": getattr(self, "status_text", "Ready"),
            "status_type": getattr(self, "status_type", "success"),
        }

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _rebuild_interface(self, state):
        if self.highlight_after_id is not None:
            try:
                self.root.after_cancel(self.highlight_after_id)
            except Exception:
                pass
            self.highlight_after_id = None

        for child in self.root.winfo_children():
            child.destroy()

        self._configure_ttk_style()
        self._build_layout()
        self._configure_text_tags()
        self._bind_editor_events()

        code = state.get("code") or self.SAMPLE_CODE
        self.code_input.delete("1.0", tk.END)
        self.code_input.insert("1.0", code)
        self.update_line_numbers()
        self.schedule_highlight()

        self.output_text.delete("1.0", tk.END)
        if state.get("output"):
            self.output_text.insert("1.0", state["output"])

        self.error_text.delete("1.0", tk.END)
        if state.get("errors"):
            self.error_text.insert("1.0", state["errors"])

        self.set_placeholder_texts()
        if self.last_tokens:
            self.load_tokens(self.last_tokens)

        try:
            self.load_symbol_table()
            self.load_function_table()
        except Exception:
            pass

        resultado = self._get_parser_result()
        try:
            self.load_generated_artifacts(resultado)
            self.load_vm_output(resultado)
        except Exception:
            pass

        if self.last_ast is not None:
            try:
                self.export_ast_graphviz_modern(self.last_ast)
                self.load_graphviz_image()
            except Exception:
                pass

        self.stage_states = state.get("stage_states") or {"lexico": "idle", "sintactico": "idle", "semantico": "idle"}
        for stage, status in self.stage_states.items():
            if stage in self.stage_cards:
                self.set_stage(stage, status)

        self.update_status(state.get("status_text", "Ready"), state.get("status_type", "success"))

        active_tab = state.get("active_tab")
        if active_tab:
            try:
                self.tabs.set(active_tab)
            except Exception:
                pass

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _primary_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=12,
                             fg_color=self.THEME['accent_2'], hover_color=self.THEME.get('accent_hover'),
                             text_color=self.THEME.get('primary_button_text', '#ffffff'),
                             font=("Segoe UI", 12, "bold"))


    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _secondary_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=12,
                             fg_color=self.THEME['panel_3'], hover_color=self.THEME.get('button_hover'),
                             text_color=self.THEME.get('button_text', self.THEME['text']),
                             font=("Segoe UI", 12, "bold"))


    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _danger_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=12,
                             fg_color=self.THEME.get('danger'), hover_color=self.THEME.get('danger_hover'),
                             text_color=self.THEME.get('danger_button_text', '#ffffff'),
                             font=("Segoe UI", 12, "bold"))


    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _small_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, width=112, height=30, corner_radius=10,
                             fg_color=self.THEME['panel_3'], hover_color=self.THEME.get('button_hover'),
                             text_color=self.THEME.get('button_text', self.THEME['text']),
                             font=("Segoe UI", 11, "bold"))


    # Ajusta estilos, eventos o parámetros visuales antes de usar la interfaz.
    def _configure_text_tags(self):
        tag_styles = {
            "keyword": {"foreground": self.THEME['purple']},
            "type": {"foreground": self.THEME.get('type', self.THEME['accent'])},
            "constant": {"foreground": self.THEME['orange']},
            "literal": {"foreground": self.THEME['green']},
            "operator": {"foreground": self.THEME.get('operator', self.THEME['purple'])},
            "punctuation": {"foreground": self.THEME.get('punctuation', self.THEME['text'])},
            "comment": {"foreground": self.THEME.get('comment', self.THEME['muted']), "font": (self.code_font_family, self.editor_font_size, "italic")},
            "error": {"foreground": self.THEME['error'], "underline": True},
        }
        for tag, opts in tag_styles.items():
            self.code_input.tag_configure(tag, **opts)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _on_text_modified(self, _event=None):
        if self.code_input.edit_modified():
            self.code_input.edit_modified(False)
            self.update_line_numbers()
            self.schedule_highlight()

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _editor_yview(self, *args):
        self.code_input.yview(*args)
        self.line_numbers.yview_moveto(self.code_input.yview()[0])

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _on_editor_scroll(self, first, last, scrollbar):
        scrollbar.set(first, last)
        self.line_numbers.yview_moveto(first)

    # Actualiza la interfaz o el estado interno después de un cambio relevante.
    def update_line_numbers(self):
        line_count = int(self.code_input.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i).rjust(3) for i in range(1, line_count + 1))
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", numbers)
        self.line_numbers.configure(state="disabled")

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def schedule_highlight(self):
        if self.highlight_after_id is not None:
            self.root.after_cancel(self.highlight_after_id)
        self.highlight_after_id = self.root.after(120, self.highlight_syntax)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _tag_offset(self, tag, start_offset, end_offset):
        start = f"1.0+{start_offset}c"
        end = f"1.0+{end_offset}c"
        self.code_input.tag_add(tag, start, end)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def get_code(self):
        return self.code_input.get("1.0", "end-1c")

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def increase_font(self):
        self.editor_font_size = min(self.editor_font_size + 1, 24)
        self.output_font_size = min(self.output_font_size + 1, 22)
        self.apply_fonts()

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def decrease_font(self):
        self.editor_font_size = max(self.editor_font_size - 1, 8)
        self.output_font_size = max(self.output_font_size - 1, 8)
        self.apply_fonts()

    # Devuelve esta parte del estado a sus valores iniciales seguros.
    def reset_font(self):
        self.editor_font_size = 12
        self.output_font_size = 11
        self.apply_fonts()

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def apply_fonts(self):
        self.code_input.configure(font=(self.code_font_family, self.editor_font_size))
        self.line_numbers.configure(font=(self.code_font_family, self.editor_font_size))
        self.code_input.tag_configure(
            "comment",
            font=(self.code_font_family, self.editor_font_size, "italic")
        )
        for box in [self.output_text, self.error_text, self.vm_output_text]:
            box.configure(font=(self.code_font_family, self.output_font_size))
        style = ttk.Style()
        for summary in [self.tac_summary_label, self.tac_optimized_summary_label, self.target_summary_label, self.vm_summary_label]:
            summary.configure(font=(self.code_font_family, max(9, self.output_font_size)))
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
    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _safe_run_name(self, source_path):
        if source_path and source_path != "<editor>":
            base = os.path.splitext(os.path.basename(source_path))[0]
        else:
            base = "gui_run"

        base = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("._-")
        return base or "gui_run"

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _set_output_dir(self, output_dir):
        self.current_output_dir = os.path.abspath(output_dir)
        self.current_run_name = self._safe_run_name(output_dir)

        self.ast_dir = os.path.join(self.current_output_dir, "ast")
        self.ir_dir = os.path.join(self.current_output_dir, "ir")
        self.target_dir = os.path.join(self.current_output_dir, "target")

        self.ast_output_base = os.path.join(self.ast_dir, f"ast_{self.current_run_name}")
        self.ast_dot_path = self.ast_output_base + ".dot"
        self.ast_png_path = self.ast_output_base + ".png"
        self.ast_modern_dot_path = self.ast_dot_path
        self.ast_modern_svg_path = self.ast_output_base + ".svg"
        self.ast_svg_viewer_path = self.ast_output_base + "_viewer.html"
        self.ast_graphviz_preview_png_path = self.ast_png_path
        self.ast_modern_png_path = self.ast_png_path

        self.current_artifacts = {
            "ast_dot": self.ast_dot_path,
            "ast_png": self.ast_png_path,
            "ast_modern_dot": self.ast_modern_dot_path,
            "ast_modern_svg": self.ast_modern_svg_path,
            "ast_svg_viewer": self.ast_svg_viewer_path,
            "tac": os.path.join(self.ir_dir, f"tac_{self.current_run_name}.ir"),
            "tac_optimized": os.path.join(self.ir_dir, f"tac_optimized_{self.current_run_name}.ir"),
            "target_code": os.path.join(self.target_dir, f"target_code_{self.current_run_name}.asm"),
        }


    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _prepare_output_dir(self, source_path):
        run_name = self._safe_run_name(source_path)
        output_dir = os.path.join(self.outputs_root, run_name)
        os.makedirs(output_dir, exist_ok=True)
        self._set_output_dir(output_dir)
        for folder in (self.ast_dir, self.ir_dir, self.target_dir):
            os.makedirs(folder, exist_ok=True)
        return output_dir


    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _get_parser_result(self):
        getter = getattr(parser, "obtener_ultimo_resultado", None)
        if callable(getter):
            return getter() or {}
        return getattr(parser, "ultimo_resultado", None) or {}

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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
        self.append_output(f"- AST DOT: {artifacts.get('ast_dot', self.ast_dot_path)}\n")
        self.append_output(f"- AST SVG: {artifacts.get('ast_modern_svg', self.ast_modern_svg_path)}\n")
        self.append_output(f"- AST PNG: {artifacts.get('ast_png', self.ast_png_path)}\n")
        self.append_output(f"- TAC: {artifacts.get('tac', self.current_artifacts['tac'])}\n")
        self.append_output(f"- Optimized TAC: {artifacts.get('tac_optimized', self.current_artifacts['tac_optimized'])}\n")
        self.append_output(f"- Target Code: {artifacts.get('target_code', self.current_artifacts['target_code'])}\n")

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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def load_generated_artifacts(self, resultado=None):
        artifacts = dict(self.current_artifacts)
        artifacts.update((resultado or {}).get("artifacts") or {})

        tac_rows = self._load_instruction_file(
            self.tac_tree,
            self.tac_summary_label,
            artifacts.get("tac"),
            "TAC",
            "TAC no disponible.",
        )
        opt_rows = self._load_instruction_file(
            self.tac_optimized_tree,
            self.tac_optimized_summary_label,
            artifacts.get("tac_optimized"),
            "TAC Optimized",
            "TAC optimizado no disponible.",
            compare_rows=tac_rows,
        )
        self._load_instruction_file(
            self.target_tree,
            self.target_summary_label,
            artifacts.get("target_code"),
            "Target Code",
            "Target code no disponible.",
        )
        return tac_rows, opt_rows

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def load_vm_output(self, resultado=None):
        resultado = resultado or {}
        vm_resultado = resultado.get("vm_resultado")
        vm_executed = resultado.get("vm_executed", vm_resultado is not None)

        self.vm_output_text.configure(state="normal")
        self.vm_output_text.delete("1.0", tk.END)

        if not vm_executed:
            message = "VM Output: skipped · main not found"
            self._set_vm_summary(self.vm_summary_label, message, self.THEME['warning'])
            self.vm_output_text.insert(tk.END, "VM Execution\n", "accent")
            self.vm_output_text.insert(tk.END, "============\n\n", "muted")
            self.vm_output_text.insert(tk.END, "Status: SKIPPED\n", "warning")
            self.vm_output_text.insert(tk.END, "Reason: main function not found.\n")
            self.vm_output_text.configure(state="disabled")
            return

        if vm_resultado is None:
            message = "VM Output: no result available"
            self._set_vm_summary(self.vm_summary_label, message, self.THEME['warning'])
            self.vm_output_text.insert(tk.END, "VM Execution\n", "accent")
            self.vm_output_text.insert(tk.END, "============\n\n", "muted")
            self.vm_output_text.insert(tk.END, "Status: UNKNOWN\n", "warning")
            self.vm_output_text.insert(tk.END, "No VM result was returned by the parser.\n")
            self.vm_output_text.configure(state="disabled")
            return

        output_lines = [str(line) for line in (vm_resultado.get("output") or [])]
        return_value = vm_resultado.get("return_value")
        entry_point = resultado.get("entry_point", "main")

        summary = (
            f"VM Output: OK · entry={entry_point} · "
            f"return={return_value} · output lines={len(output_lines)}"
        )
        self._set_vm_summary(self.vm_summary_label, summary, self.THEME['text'])

        self.vm_output_text.insert(tk.END, "VM Execution\n", "accent")
        self.vm_output_text.insert(tk.END, "============\n\n", "muted")
        self.vm_output_text.insert(tk.END, "Status: ", "muted")
        self.vm_output_text.insert(tk.END, "OK\n", "success")
        self.vm_output_text.insert(tk.END, f"Entry point: {entry_point}\n")
        self.vm_output_text.insert(tk.END, "Return value: ", "muted")
        self.vm_output_text.insert(tk.END, f"{return_value}\n", "success")
        self.vm_output_text.insert(tk.END, f"Output lines: {len(output_lines)}\n\n")

        self.vm_output_text.insert(tk.END, "Program Output\n", "accent")
        self.vm_output_text.insert(tk.END, "--------------\n", "muted")

        if output_lines:
            for index, line in enumerate(output_lines, start=1):
                self.vm_output_text.insert(tk.END, f"[{index:02d}] ", "prompt")
                self.vm_output_text.insert(tk.END, line + "\n")
        else:
            self.vm_output_text.insert(tk.END, "(no output)\n", "muted")

        self.vm_output_text.configure(state="disabled")

    # Carga información externa y la adapta para mostrarla o procesarla.
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

    # Carga información externa y la adapta para mostrarla o procesarla.
    def _load_instruction_file(self, tree, summary_label, path, title, fallback, compare_rows=None):
        self._clear_tree(tree)

        if not path or not os.path.exists(path):
            self._set_instruction_summary(summary_label, f"{title}: {fallback}", self.THEME['warning'])
            self._insert_instruction_placeholder(tree, fallback)
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except Exception as exc:
            message = f"{fallback} Error: {exc}"
            self._set_instruction_summary(summary_label, f"{title}: {message}", self.THEME['error'])
            self._insert_instruction_placeholder(tree, message)
            return []

        rows = []
        for fallback_num, line in enumerate(line for line in lines if line.strip()):
            row = self._parse_instruction_line(line, fallback_num=fallback_num)
            if row is not None:
                rows.append(row)

        if not rows:
            self._set_instruction_summary(summary_label, f"{title}: empty file", self.THEME['warning'])
            self._insert_instruction_placeholder(tree, "Empty file.")
            return []

        for row in rows:
            tree.insert(
                "",
                tk.END,
                values=(
                    row["num"],
                    row["op"],
                    row["arg1"],
                    row["arg2"],
                    row["result"],
                    row["raw"],
                ),
                tags=(row["category"],),
            )

        summary = self._instruction_summary(title, rows, compare_rows)
        self._set_instruction_summary(summary_label, summary, self.THEME['text'])
        self._autosize_instruction_columns(tree, rows)
        return rows

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _insert_instruction_placeholder(self, tree, message):
        self._clear_tree(tree)
        tree.insert(
            "",
            tk.END,
            values=("-", "-", "-", "-", "-", message),
            tags=("placeholder",),
        )
        self._autosize_instruction_columns(
            tree,
            [{"num": "-", "op": "-", "arg1": "-", "arg2": "-", "result": "-", "raw": message}],
        )

    # Interpreta texto o instrucciones y las convierte a una estructura más útil.
    def _parse_instruction_line(self, line, fallback_num=None):
        raw = line.rstrip()
        stripped = raw.strip()

        match = re.match(r"^(\d+)\s*:\s*(.*)$", stripped)
        if match:
            num = match.group(1)
            body = match.group(2).strip()
        else:
            num = f"{fallback_num:04d}" if fallback_num is not None else ""
            body = stripped

        if not body:
            return None

        parsed = self._parse_tac_instruction(body)
        if parsed is None:
            parsed = self._parse_target_instruction(body)
        if parsed is None:
            parsed = {"op": self._detect_generic_op(body), "arg1": "", "arg2": "", "result": ""}

        op = parsed.get("op", "") or ""
        return {
            "num": num,
            "op": op,
            "arg1": parsed.get("arg1", "") or "",
            "arg2": parsed.get("arg2", "") or "",
            "result": parsed.get("result", "") or "",
            "raw": body,
            "category": self._instruction_category(op, body),
        }

    # Interpreta texto o instrucciones y las convierte a una estructura más útil.
    def _parse_tac_instruction(self, body):
        lower = body.lower()

        if lower.startswith("func ") and body.endswith(":"):
            return {"op": "FUNC", "result": body[5:-1].strip()}

        if lower.startswith("end func "):
            return {"op": "END_FUNC", "result": body[9:].strip()}

        if lower.startswith("param "):
            return {"op": "PARAM", "result": body[6:].strip()}

        if lower.startswith("arg "):
            return {"op": "ARG", "result": body[4:].strip()}

        if lower.startswith("return"):
            return {"op": "RETURN", "result": body[6:].strip()}

        match = re.match(r"^ifFalse\s+(.+?)\s+goto\s+(.+)$", body)
        if match:
            return {"op": "IF_FALSE", "arg1": match.group(1).strip(), "result": match.group(2).strip()}

        match = re.match(r"^if\s+(.+?)\s+goto\s+(.+)$", body)
        if match:
            return {"op": "IF_TRUE", "arg1": match.group(1).strip(), "result": match.group(2).strip()}

        if lower.startswith("goto "):
            return {"op": "GOTO", "result": body[5:].strip()}

        if lower.startswith("printf "):
            parts = self._split_operands(body[7:].strip())
            return {
                "op": "PRINTF",
                "arg1": parts[0] if parts else "",
                "arg2": ", ".join(parts[1:]) if len(parts) > 1 else "",
            }

        if lower.startswith("print "):
            return {"op": "PRINT", "result": body[6:].strip()}

        if lower.startswith("call "):
            parts = self._split_operands(body[5:].strip())
            return {
                "op": "CALL",
                "arg1": parts[0] if parts else "",
                "arg2": parts[1] if len(parts) > 1 else "",
            }

        if body.endswith(":") and " " not in body:
            return {"op": "LABEL", "result": body[:-1]}

        if " = " not in body:
            return None

        left, right = body.split(" = ", 1)
        left = left.strip()
        right = right.strip()

        match = re.match(r"^call\s+(.+?)\s*,\s*(.+)$", right)
        if match:
            return {"op": "CALL", "arg1": match.group(1).strip(), "arg2": match.group(2).strip(), "result": left}

        match = re.match(r"^(.+)\[(.+)\]\[(.+)\]$", right)
        if match:
            return {
                "op": "LOAD_MATRIX",
                "arg1": match.group(1).strip(),
                "arg2": f"{match.group(2).strip()}, {match.group(3).strip()}",
                "result": left,
            }

        match = re.match(r"^(.+)\[(.+)\]$", right)
        if match:
            return {"op": "LOAD_ARRAY", "arg1": match.group(1).strip(), "arg2": match.group(2).strip(), "result": left}

        match = re.match(r"^(.+)\[(.+)\]\[(.+)\]$", left)
        if match:
            return {
                "op": "STORE_MATRIX",
                "arg1": right,
                "arg2": f"{match.group(2).strip()}, {match.group(3).strip()}",
                "result": match.group(1).strip(),
            }

        match = re.match(r"^(.+)\[(.+)\]$", left)
        if match:
            return {"op": "STORE_ARRAY", "arg1": right, "arg2": match.group(2).strip(), "result": match.group(1).strip()}

        bin_match = re.match(r"^(.+?)\s*(==|!=|<=|>=|&&|\|\||[+\-*/%<>])\s*(.+)$", right)
        if bin_match:
            return {
                "op": bin_match.group(2),
                "arg1": bin_match.group(1).strip(),
                "arg2": bin_match.group(3).strip(),
                "result": left,
            }

        unary_match = re.match(r"^(!|-|\+)\s*(.+)$", right)
        if unary_match:
            op_map = {"-": "NEG", "+": "POS", "!": "!"}
            return {"op": op_map[unary_match.group(1)], "arg1": unary_match.group(2).strip(), "result": left}

        return {"op": "ASSIGN", "arg1": right, "result": left}

    # Interpreta texto o instrucciones y las convierte a una estructura más útil.
    def _parse_target_instruction(self, body):
        if body.endswith(":") and " " not in body:
            return {"op": "LABEL", "result": body[:-1]}

        parts = body.split(maxsplit=1)
        if not parts:
            return None

        op = parts[0].upper()
        rest = parts[1].strip() if len(parts) > 1 else ""
        operands = self._split_operands(rest)

        if op in {"FUNC", "END_FUNC", "PARAM", "JMP", "RET", "PRINT"}:
            return {"op": op, "result": operands[0] if operands else ""}

        if op == "MOV":
            return {
                "op": op,
                "arg1": operands[1] if len(operands) > 1 else "",
                "result": operands[0] if operands else "",
            }

        if op in {"ADD", "SUB", "MUL", "DIV", "MOD", "EQ", "NE", "LT", "GT", "LE", "GE", "AND", "OR"}:
            return {
                "op": op,
                "arg1": operands[1] if len(operands) > 1 else "",
                "arg2": operands[2] if len(operands) > 2 else "",
                "result": operands[0] if operands else "",
            }

        if op in {"NEG", "POS", "NOT"}:
            return {
                "op": op,
                "arg1": operands[1] if len(operands) > 1 else "",
                "result": operands[0] if operands else "",
            }

        if op in {"JZ", "JNZ"}:
            return {
                "op": op,
                "arg1": operands[0] if operands else "",
                "result": operands[1] if len(operands) > 1 else "",
            }

        if op == "ARG":
            return {"op": op, "result": operands[0] if operands else ""}

        if op == "CALL":
            if len(operands) == 3:
                return {"op": op, "arg1": operands[1], "arg2": operands[2], "result": operands[0]}
            return {"op": op, "arg1": operands[0] if operands else "", "arg2": operands[1] if len(operands) > 1 else ""}

        if op == "PRINTF":
            return {
                "op": op,
                "arg1": operands[0] if operands else "",
                "arg2": ", ".join(operands[1:]) if len(operands) > 1 else "",
            }

        if op == "LOAD_ARRAY":
            return {
                "op": op,
                "arg1": operands[1] if len(operands) > 1 else "",
                "arg2": operands[2] if len(operands) > 2 else "",
                "result": operands[0] if operands else "",
            }

        if op == "STORE_ARRAY":
            return {
                "op": op,
                "arg1": operands[2] if len(operands) > 2 else "",
                "arg2": operands[1] if len(operands) > 1 else "",
                "result": operands[0] if operands else "",
            }

        if op == "LOAD_MATRIX":
            return {
                "op": op,
                "arg1": operands[1] if len(operands) > 1 else "",
                "arg2": ", ".join(operands[2:4]) if len(operands) > 3 else "",
                "result": operands[0] if operands else "",
            }

        if op == "STORE_MATRIX":
            return {
                "op": op,
                "arg1": operands[3] if len(operands) > 3 else "",
                "arg2": ", ".join(operands[1:3]) if len(operands) > 2 else "",
                "result": operands[0] if operands else "",
            }

        return {"op": op, "arg1": operands[0] if operands else "", "arg2": operands[1] if len(operands) > 1 else "", "result": operands[2] if len(operands) > 2 else ""}

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _split_operands(self, text):
        operands = []
        current = []
        quote = None
        escape = False

        for ch in text:
            if escape:
                current.append(ch)
                escape = False
                continue

            if ch == "\\" and quote:
                current.append(ch)
                escape = True
                continue

            if ch in {'"', "'"}:
                current.append(ch)
                if quote == ch:
                    quote = None
                elif quote is None:
                    quote = ch
                continue

            if ch == "," and quote is None:
                value = "".join(current).strip()
                if value:
                    operands.append(value)
                current = []
                continue

            current.append(ch)

        value = "".join(current).strip()
        if value:
            operands.append(value)

        return operands

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _detect_generic_op(self, body):
        if body.endswith(":"):
            return "LABEL"
        return body.split(maxsplit=1)[0].upper() if body else ""

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _instruction_category(self, op, raw=""):
        op_upper = str(op).upper()
        op_raw = str(op)

        if op_upper in {"FUNC", "END_FUNC", "PARAM"}:
            return "function"
        if op_upper == "LABEL":
            return "label"
        if op_upper in {"GOTO", "IF_FALSE", "IF_TRUE", "JMP", "JZ", "JNZ"}:
            return "jump"
        if op_upper in {"CALL", "ARG"}:
            return "call"
        if op_upper in {"RETURN", "RET"}:
            return "return"
        if op_upper in {"LOAD_ARRAY", "STORE_ARRAY", "LOAD_MATRIX", "STORE_MATRIX"}:
            return "memory"
        if op_upper in {"ADD", "SUB", "MUL", "DIV", "MOD", "NEG", "POS"} or op_raw in {"+", "-", "*", "/", "%", "NEG", "POS"}:
            return "arithmetic"
        if op_upper in {"EQ", "NE", "LT", "GT", "LE", "GE", "AND", "OR", "NOT"} or op_raw in {"==", "!=", "<", ">", "<=", ">=", "&&", "||", "!"}:
            return "logic"
        if op_upper in {"ASSIGN", "MOV"}:
            return "assign"
        if op_upper in {"PRINT", "PRINTF"}:
            return "io"
        return "other"

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _instruction_summary(self, title, rows, compare_rows=None):
        total = len(rows)
        functions = sum(1 for row in rows if row["op"].upper() == "FUNC")
        labels = sum(1 for row in rows if row["category"] == "label")
        calls = sum(1 for row in rows if row["category"] == "call" and row["op"].upper() == "CALL")
        jumps = sum(1 for row in rows if row["category"] == "jump")
        memory = sum(1 for row in rows if row["category"] == "memory")
        arithmetic = sum(1 for row in rows if row["category"] == "arithmetic")

        parts = [
            f"{title}",
            f"Instructions: {total}",
            f"Functions: {functions}",
            f"Labels: {labels}",
            f"Calls: {calls}",
            f"Jumps: {jumps}",
            f"Memory: {memory}",
            f"Arithmetic: {arithmetic}",
        ]

        if compare_rows is not None:
            original = len(compare_rows)
            removed = max(0, original - total)
            reduction = (removed / original * 100) if original else 0
            parts.extend([
                f"Original: {original}",
                f"Removed: {removed}",
                f"Reduction: {reduction:.2f}%",
            ])

        return "    |    ".join(parts)

    # ---------------------------------------------------------------------
    # Compilation workflow
    # ---------------------------------------------------------------------
    # Ejecuta una compilación y sincroniza los resultados con la salida correspondiente.
    def compile_code(self):
        self._run_pipeline(mode="all")

    # Ejecuta una fase o verificación concreta del flujo del compilador.
    def run_lexer_only(self):
        self._run_pipeline(mode="lexer")

    # Ejecuta una fase o verificación concreta del flujo del compilador.
    def run_parser_sdt_only(self):
        self._run_pipeline(mode="parser")

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _run_pipeline(self, mode="all"):
        self.reset_outputs(keep_code=True)
        self.reset_stage_cards()
        code = self.get_code().strip()
        if not code:
            self.append_output("[ERROR] No code to compile.\n")
            self.append_error("No code to compile.")
            self.update_status("No code", "error")
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
            self.append_output("[ERROR] Lexical analysis failed.\n")
            self.append_error(lexer_messages or "Lexical error: unrecognized symbol.")
            self.update_status("Lexical error", "error")
            self.tabs.set("Errors")
            return

        self.last_tokens = tokens
        self.set_stage("lexico", "success")
        self.append_output(f"[OK] Lexical analysis OK. Tokens generated: {len(tokens)}\n")
        self.load_tokens(tokens)
        self.highlight_syntax()

        if mode == "lexer":
            self.set_stage("sintactico", "pending")
            self.set_stage("semantico", "pending")
            self.update_status("Lexical analysis OK", "success")
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
            self.update_status("Compilation successful", "success")
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
            self.load_vm_output(resultado_detallado)
            self.tabs.set("Output")
        else:
            self.append_output(parser_output)
            if "Syntax error" in parser_output:
                self.set_stage("sintactico", "error")
                self.set_stage("semantico", "pending")
                self.update_status("Syntax error", "error")
            elif "SDT error" in parser_output or "Semantic error" in parser_output:
                self.set_stage("sintactico", "success")
                self.set_stage("semantico", "error")
                self.update_status("Semantic error", "error")
            else:
                self.set_stage("sintactico", "error")
                self.set_stage("semantico", "error")
                self.update_status("Compilation failed", "error")
            self.tabs.set("Errors")

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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
            self.error_text.insert("1.0", "No errors detected in the last run.")

    # ---------------------------------------------------------------------
    # Tables
    # ---------------------------------------------------------------------
    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def load_tokens(self, tokens):
        self._clear_tree(self.token_tree)
        for tipo, valor, linea, columna in tokens:
            self.token_tree.insert("", tk.END, values=(tipo, valor, linea, columna))

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def load_symbol_table(self):
        self._clear_tree(self.symbol_tree)
        if not tabla_simbolos.simbolos:
            self.symbol_tree.insert("", tk.END, values=("(empty)", "-", "-", "-"))
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def load_function_table(self):
        self._clear_tree(self.function_tree)
        if not tabla_funciones.funciones:
            self.function_tree.insert("", tk.END, values=("(empty)", "-", "-"))
            return
        for name, data in tabla_funciones.funciones.items():
            params = ", ".join(f"{p.get('tipo')} {p.get('nombre')}" for p in data.get('parametros', []))
            self.function_tree.insert("", tk.END, values=(name, data.get('tipo_retorno', '-'), params or "no parameters"))

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    # ---------------------------------------------------------------------
    # AST Treeview and Canvas
    # ---------------------------------------------------------------------
    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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
            self.ast_tree.insert("", tk.END, text="No AST", values=("-", "-"))
            return
        add_node("", ast)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def populate_ast_tree_from_text(self):
        if not hasattr(self, "ast_tree") or not hasattr(self, "ast_text"):
            return
        self._clear_tree(self.ast_tree)
        content = self.ast_text.get("1.0", "end-1c")
        if not content.strip():
            self.ast_tree.insert("", tk.END, text="No AST", values=("-", "-"))
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def draw_ast_canvas(self, ast):
        if not hasattr(self, "ast_canvas"):
            return
        self.ast_canvas.delete("all")

        if ast is None:
            self.draw_ast_placeholder("No AST available.")
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
                fill=self.THEME['text'],
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def draw_ast_placeholder(self, message):
        if not hasattr(self, "ast_canvas"):
            return
        self.ast_canvas.delete("all")
        self.ast_canvas.create_text(30, 30, anchor="nw", fill=self.THEME['muted'], text=message, font=("Segoe UI", 13))
        self.ast_canvas.configure(scrollregion=(0, 0, 900, 500))

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def zoom_ast_canvas(self, factor):
        self.ast_scale = max(0.45, min(2.5, self.ast_scale * factor))
        if self.last_ast is not None:
            self.draw_ast_canvas(self.last_ast)

    # Devuelve esta parte del estado a sus valores iniciales seguros.
    def reset_ast_canvas_zoom(self):
        self.ast_scale = 1.0
        if self.last_ast is not None:
            self.draw_ast_canvas(self.last_ast)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _node_label(self, node):
        tipo = str(getattr(node, "tipo", "NODE"))
        valor = self._node_value(node)

        tipo = self._short_node_text(tipo, 20)

        if valor not in {None, "", "None"}:
            valor = self._short_node_text(str(valor), 22)
            return f"{tipo}\n'{valor}'"

        return tipo
    
    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _short_node_text(self, text, limit=28):
        text = str(text)

        if len(text) <= limit:
            return text

        return text[: limit - 1] + "…"

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _node_value(self, node):
        value = getattr(node, 'valor', None)
        if value is None:
            return ""
        try:
            return str(formatear_valor(value))
        except Exception:
            return str(value)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _node_pos(self, node):
        line = getattr(node, 'linea', None)
        col = getattr(node, 'columna', None)
        if line is None:
            return "-"
        return f"{line}:{col}"

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _ast_color(self, node_type):
        node_type = str(node_type).upper()
        palette = self.THEME.get('ast_palette', {})

        if node_type in {"PROGRAM", "STMT_LIST", "BLOCK"}:
            return palette.get('program', self.THEME['panel_3'])

        if node_type in {"FUNCTION", "FUNCTION_DECL", "FUNCTION_HEADER", "CALL"}:
            return palette.get('function', self.THEME['panel_3'])

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
            return palette.get('declaration', self.THEME['panel_3'])

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
            return palette.get('control', self.THEME['panel_3'])

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
            return palette.get('operator', self.THEME['accent_2'])

        if node_type in {"CONST", "ID", "ARRAY_ACCESS"}:
            return palette.get('leaf', self.THEME['panel_2'])

        return palette.get('default', self.THEME['panel_2'])

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
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
    # Exporta el artefacto indicado para que pueda revisarse fuera de la GUI.
    def export_ast_graphviz_modern(self, ast):
        """
        Generates one DOT file and renders both SVG and PNG from that same DOT.
        The GUI no longer uses the PNG as an embedded preview; it is saved only as an artifact.
        """
        if ast is None:
            return

        if not GRAPHVIZ_AVAILABLE:
            self.append_output("\n[WARN] Graphviz is not available. Install it with: brew install graphviz / apt install graphviz / choco install graphviz\n")
            return

        for folder in (self.ast_dir, self.ir_dir, self.target_dir):
            os.makedirs(folder, exist_ok=True)

        counter = [0]
        bg = "transparent"
        text = self.THEME.get('text', '#f8fafc')
        edge = self.THEME.get('ast_edge', '#46637f')
        outline = self.THEME.get('ast_outline', '#7dd3fc')

        lines = [
            "digraph AST {",
            "    graph [",
            f"        bgcolor=\"{bg}\",",
            "        pad=\"0.55\",",
            "        nodesep=\"0.46\",",
            "        ranksep=\"0.78\",",
            "        splines=\"line\",",
            "        outputorder=\"edgesfirst\",",
            "        margin=\"0.05\"",
            "    ];",
            "",
            "    node [",
            "        shape=box,",
            "        style=\"rounded,filled\",",
            "        fontname=\"Menlo\",",
            "        fontsize=12,",
            "        margin=\"0.16,0.09\",",
            f"        color=\"{outline}\",",
            "        penwidth=1.6,",
            f"        fontcolor=\"{text}\"",
            "    ];",
            "",
            "    edge [",
            f"        color=\"{edge}\",",
            "        penwidth=1.25,",
            "        arrowsize=0.65",
            "    ];",
            "",
        ]

        def esc(value):
            return (
                str(value)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
            )

        def short_text(value, limit=34):
            value = str(value)
            return value if len(value) <= limit else value[: limit - 1] + "…"

        def node_label(node):
            tipo = short_text(getattr(node, "tipo", "NODE"), 28)
            value = self._node_value(node)
            if value not in {None, "", "None"}:
                return f"{tipo}\n'{short_text(value, 34)}'"
            return tipo

        def rec(node):
            node_id = f"n{counter[0]}"
            counter[0] += 1
            fill = self._ast_color(getattr(node, "tipo", ""))
            lines.append(f'    {node_id} [label="{esc(node_label(node))}", fillcolor="{fill}"];')
            for child in getattr(node, "hijos", []) or []:
                child_id = rec(child)
                lines.append(f"    {node_id} -> {child_id};")
            return node_id

        rec(ast)
        lines.append("}")

        with open(self.ast_modern_dot_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        try:
            subprocess.run(["dot", "-Tsvg", self.ast_modern_dot_path, "-o", self.ast_modern_svg_path], check=True, capture_output=True, text=True)
            subprocess.run(["dot", "-Tpng", "-Gdpi=180", self.ast_modern_dot_path, "-o", self.ast_png_path], check=True, capture_output=True, text=True)
            self._write_ast_svg_viewer()
        except Exception as exc:
            self.append_output(f"\n[WARN] Could not render AST artifacts with Graphviz: {exc}\n")

    # Convierte datos internos en una presentación visual o textual.
    def _render_graphviz_preview_png(self):
        """Compatibility wrapper: the PNG is generated from the DOT as a saved artifact."""
        if not GRAPHVIZ_AVAILABLE or not os.path.exists(self.ast_modern_dot_path):
            return
        try:
            subprocess.run(
                ["dot", "-Tpng", "-Gdpi=180", self.ast_modern_dot_path, "-o", self.ast_png_path],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception as exc:
            self.append_output(f"\n[WARN] Could not render AST PNG: {exc}\n")

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def load_graphviz_image(self):
        """Updates the AST tab with links/instructions instead of embedding a PNG preview."""
        if not hasattr(self, "ast_info_text"):
            return

        self.ast_info_text.configure(state="normal")
        self.ast_info_text.delete("1.0", tk.END)

        if not os.path.exists(self.ast_modern_svg_path):
            self.ast_info_text.insert(
                "1.0",
                "No AST Tree available yet.\n\n"
                "Compile code to generate the AST files. The browser viewer will show the full tree fitted on screen."
            )
            self.ast_info_text.configure(state="disabled")
            return

        files = [
            ("DOT", self.ast_modern_dot_path),
            ("SVG", self.ast_modern_svg_path),
            ("PNG", self.ast_png_path),
            ("Browser viewer", self.ast_svg_viewer_path),
        ]

        self.ast_info_text.insert("1.0", "AST Tree generated successfully.\n\n")
        self.ast_info_text.insert(tk.END, "Generated files:\n")
        for label, path in files:
            status = "OK" if os.path.exists(path) else "missing"
            self.ast_info_text.insert(tk.END, f"- {label}: {path} [{status}]\n")

        self.ast_info_text.configure(state="disabled")

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def zoom_graphviz(self, factor):
        # PNG preview zoom was removed; keep method for backward compatibility.
        self.load_graphviz_image()

    # Devuelve esta parte del estado a sus valores iniciales seguros.
    def reset_graphviz_zoom(self):
        # PNG preview zoom was removed; keep method for backward compatibility.
        self.load_graphviz_image()

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def fit_graphviz_to_view(self):
        # The browser viewer handles fit-to-screen for the SVG.
        self.open_graphviz_svg()

    # Abre el recurso solicitado usando la herramienta disponible del sistema.
    def open_graphviz_svg(self):
        if not os.path.exists(self.ast_modern_svg_path):
            messagebox.showinfo("Open AST SVG", "There is no AST SVG to open yet.")
            return

        if not os.path.exists(self.ast_svg_viewer_path):
            self._write_ast_svg_viewer()

        target = self.ast_svg_viewer_path if os.path.exists(self.ast_svg_viewer_path) else self.ast_modern_svg_path
        self._open_path_in_browser(target)

    # Exporta el artefacto indicado para que pueda revisarse fuera de la GUI.
    def export_graphviz_svg(self):
        if not os.path.exists(self.ast_modern_svg_path):
            messagebox.showinfo("Export AST SVG", "There is no AST SVG to export yet.")
            return

        destination = filedialog.asksaveasfilename(
            title="Save AST as SVG",
            initialfile=os.path.basename(self.ast_modern_svg_path),
            defaultextension=".svg",
            filetypes=[
                ("SVG", "*.svg"),
                ("All files", "*.*"),
            ],
        )

        if destination:
            shutil.copyfile(self.ast_modern_svg_path, destination)
            messagebox.showinfo("Export AST SVG", f"AST SVG exported to:\n{destination}")

    # Exporta el artefacto indicado para que pueda revisarse fuera de la GUI.
    def export_graphviz_image(self):
        if not os.path.exists(self.ast_png_path):
            messagebox.showinfo("Export AST PNG", "There is no AST PNG to export yet.")
            return

        destination = filedialog.asksaveasfilename(
            title="Save AST as PNG",
            initialfile=os.path.basename(self.ast_png_path),
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("All files", "*.*"),
            ],
        )

        if destination:
            shutil.copyfile(self.ast_png_path, destination)
            messagebox.showinfo("Export AST PNG", f"AST PNG exported to:\n{destination}")

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _hex_to_rgb_tuple(self, color, fallback="#000000"):
        """Converts a hex color from the active GUI theme into an RGB tuple for CSS rgba()."""
        value = str(color or fallback).strip()
        if value.startswith("#"):
            value = value[1:]
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        try:
            if len(value) != 6:
                raise ValueError
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        except Exception:
            fallback_value = str(fallback or "#000000").strip().lstrip("#")
            if len(fallback_value) == 3:
                fallback_value = "".join(ch * 2 for ch in fallback_value)
            try:
                return tuple(int(fallback_value[i:i + 2], 16) for i in (0, 2, 4))
            except Exception:
                return (0, 0, 0)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _rgba(self, color, alpha=1.0, fallback="#000000"):
        r, g, b = self._hex_to_rgb_tuple(color, fallback)
        return f"rgba({r}, {g}, {b}, {alpha})"

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _theme_css_variables(self):
        """Builds CSS variables from the active GUI theme for external HTML viewers."""
        theme = self.THEME
        appearance = "light" if theme.get("appearance") == "light" else "dark"
        bg = theme.get("bg", "#0f172a")
        panel = theme.get("panel", "#111827")
        panel_2 = theme.get("panel_2", "#0b1220")
        panel_3 = theme.get("panel_3", "#1e293b")
        border = theme.get("border", "#334155")
        text = theme.get("text", "#e5e7eb")
        muted = theme.get("muted", "#94a3b8")
        accent = theme.get("accent", "#38bdf8")
        accent_2 = theme.get("accent_2", "#2563eb")
        button_hover = theme.get("button_hover", panel_3)
        shadow_alpha = "0.12" if appearance == "light" else "0.28"

        values = {
            "bg": bg,
            "panel": panel,
            "panel2": panel_2,
            "panel3": panel_3,
            "border": border,
            "text": text,
            "muted": muted,
            "accent": accent,
            "accent2": accent_2,
            "button-hover": button_hover,
            "purple": theme.get("purple", "#a78bfa"),
            "orange": theme.get("orange", "#fb923c"),
            "green": theme.get("green", "#86efac"),
            "yellow": theme.get("tag_memory", theme.get("warning", "#fde68a")),
            "header-bg": self._rgba(panel, 0.92),
            "toolbar-bg": self._rgba(panel, 0.94),
            "toolbar-fade": self._rgba(bg, 0.86),
            "card-bg": self._rgba(panel, 0.92),
            "table-head-bg": self._rgba(panel_2, 0.95),
            "pill-bg": self._rgba(panel_2, 0.84),
            "border-soft": self._rgba(border, 0.75),
            "focus-ring": self._rgba(accent, 0.16),
            "shadow-color": f"rgba(0, 0, 0, {shadow_alpha})",
        }

        lines = [":root {", f"  color-scheme: {appearance};"]
        for name, value in values.items():
            lines.append(f"  --{name}: {value};")
        lines.append("}")
        return "\n".join(lines)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _write_ast_svg_viewer(self):
        if not os.path.exists(self.ast_modern_svg_path):
            return

        try:
            with open(self.ast_modern_svg_path, "r", encoding="utf-8") as f:
                svg = f.read()
        except UnicodeDecodeError:
            with open(self.ast_modern_svg_path, "r", encoding="latin-1") as f:
                svg = f.read()

        title = html.escape(os.path.basename(self.ast_modern_svg_path))
        theme_style = self._theme_css_variables()
        doc = f"""<!doctype html>
<html lang=\"es\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>AST Viewer - {title}</title>
  <style>
    {theme_style}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:radial-gradient(circle at top left, var(--panel3) 0, var(--bg) 34rem); color:var(--text); font-family:Inter, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif; }}
    .toolbar {{ position:sticky; top:0; z-index:10; display:flex; gap:.6rem; align-items:center; flex-wrap:wrap; padding:.75rem 1rem; background:var(--toolbar-bg); border-bottom:1px solid var(--border-soft); backdrop-filter:blur(10px); }}
    .toolbar strong {{ color:var(--accent); }}
    button, a.button {{ border:1px solid var(--border); border-radius:.7rem; padding:.5rem .75rem; color:var(--text); background:var(--panel3); text-decoration:none; font-weight:700; cursor:pointer; }}
    button:hover, a.button:hover {{ background:var(--button-hover); }}
    #viewer {{ width:100vw; height:calc(100vh - 58px); overflow:auto; padding:0; }}
    #canvas {{ position:relative; min-width:100%; min-height:100%; padding:72px; }}
    #canvas svg {{ display:block; max-width:none; max-height:none; overflow:visible; margin:0 auto; }}
    .hint {{ color:var(--muted); font-size:.9rem; }}
  </style>
</head>
<body>
  <div class=\"toolbar\">
    <strong>AST Viewer</strong>
    <button type=\"button\" data-action=\"fit\">Fit whole tree</button>
    <button type=\"button\" data-action=\"width\">Fit width</button>
    <button type=\"button\" data-action=\"in\">Zoom +</button>
    <button type=\"button\" data-action=\"out\">Zoom −</button>
    <button type=\"button\" data-action=\"reset\">Reset</button>
    <a class=\"button\" href=\"{html.escape(Path(self.ast_modern_svg_path).name)}\" target=\"_blank\" rel=\"noreferrer\">Open raw SVG</a>
    <span class=\"hint\">Default view fits the whole tree on screen.</span>
  </div>
  <main id=\"viewer\"><div id=\"canvas\">{svg}</div></main>
  <script>
    const viewer = document.querySelector('#viewer');
    const canvas = document.querySelector('#canvas');
    const svg = canvas.querySelector('svg');
    const PADDING = 144;
    let zoom = 1;

    function getNaturalSize() {{
      const vb = svg.viewBox && svg.viewBox.baseVal;
      if (vb && vb.width > 0 && vb.height > 0) {{
        return {{ width: vb.width, height: vb.height }};
      }}

      try {{
        const box = svg.getBBox();
        if (box.width > 0 && box.height > 0) {{
          return {{ width: box.width, height: box.height }};
        }}
      }} catch (error) {{
        // Fall through to a safe default.
      }}

      return {{ width: 1200, height: 800 }};
    }}

    const natural = getNaturalSize();
    svg.removeAttribute('width');
    svg.removeAttribute('height');
    svg.style.transform = 'none';

    function clampScale(value) {{
      return Math.max(0.05, Math.min(6, value));
    }}

    function resizeSvg(scale, mode = 'preserve') {{
        const oldScrollWidth = Math.max(1, viewer.scrollWidth);
        const oldScrollHeight = Math.max(1, viewer.scrollHeight);

        const currentCenterX = viewer.scrollLeft + viewer.clientWidth / 2;
        const currentCenterY = viewer.scrollTop + viewer.clientHeight / 2;

        const ratioX = currentCenterX / oldScrollWidth;
        const ratioY = currentCenterY / oldScrollHeight;

        zoom = clampScale(scale);
        const width = Math.max(1, natural.width * zoom);
        const height = Math.max(1, natural.height * zoom);

        svg.style.width = `${{width}}px`;
        svg.style.height = `${{height}}px`;
        canvas.style.width = `${{width + PADDING}}px`;
        canvas.style.height = `${{height + PADDING}}px`;

        requestAnimationFrame(() => {{
            if (mode === 'center') {{
            viewer.scrollLeft = Math.max(0, (canvas.scrollWidth - viewer.clientWidth) / 2);
            viewer.scrollTop = Math.max(0, (canvas.scrollHeight - viewer.clientHeight) / 2);
            return;
            }}

            if (mode === 'preserve') {{
            viewer.scrollLeft = Math.max(
                0,
                viewer.scrollWidth * ratioX - viewer.clientWidth / 2
            );
            viewer.scrollTop = Math.max(
                0,
                viewer.scrollHeight * ratioY - viewer.clientHeight / 2
            );
            }}
        }});
        }}

        function fitWholeTree() {{
        const availableWidth = Math.max(100, viewer.clientWidth - PADDING);
        const availableHeight = Math.max(100, viewer.clientHeight - PADDING);
        resizeSvg(Math.min(availableWidth / natural.width, availableHeight / natural.height), 'center');
        }}

        function fitWidth() {{
        const availableWidth = Math.max(100, viewer.clientWidth - PADDING);
        resizeSvg(availableWidth / natural.width, 'center');
        }}

        document.querySelector('[data-action=fit]').addEventListener('click', fitWholeTree);
        document.querySelector('[data-action=width]').addEventListener('click', fitWidth);
        document.querySelector('[data-action=in]').addEventListener('click', () => resizeSvg(zoom * 1.2, 'preserve'));
        document.querySelector('[data-action=out]').addEventListener('click', () => resizeSvg(zoom / 1.2, 'preserve'));
        document.querySelector('[data-action=reset]').addEventListener('click', fitWholeTree);
        window.addEventListener('resize', fitWholeTree);
        fitWholeTree();
  </script>
</body>
</html>"""
        with open(self.ast_svg_viewer_path, "w", encoding="utf-8") as f:
            f.write(doc)

    # Abre el recurso solicitado usando la herramienta disponible del sistema.
    def open_ast_folder(self):
        path = getattr(self, "ast_dir", None) or self.current_output_dir
        if not path or not os.path.exists(path):
            messagebox.showinfo("Open AST folder", "There is no AST folder yet.")
            return
        self._open_path_in_browser(path)

    # ---------------------------------------------------------------------
    # Status and output helpers
    # ---------------------------------------------------------------------

    # Devuelve esta parte del estado a sus valores iniciales seguros.
    def reset_stage_cards(self):
        self.set_stage("lexico", "idle")
        self.set_stage("sintactico", "idle")
        self.set_stage("semantico", "idle")

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def set_stage(self, stage, state):
        names = {"lexico": "Lexical", "sintactico": "Syntax", "semantico": "Semantic"}
        icons = {"idle": "○", "pending": "…", "success": "✓", "error": "✕"}
        colors = {
            "idle": self.THEME['muted'],
            "pending": self.THEME['warning'],
            "success": self.THEME['success'],
            "error": self.THEME['error'],
        }
        self.stage_states[stage] = state
        label = self.stage_cards[stage]
        label.configure(text=f"{icons[state]} {names[stage]}", text_color=colors[state])

    # Actualiza la interfaz o el estado interno después de un cambio relevante.
    def update_status(self, message, status_type="normal"):
        self.status_text = message
        self.status_type = status_type
        colors = {"success": self.THEME['success'], "error": self.THEME['error'], "warning": self.THEME['warning'], "normal": self.THEME['muted']}
        self.status_label.configure(text=message, text_color=colors.get(status_type, self.THEME['muted']))

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def append_output(self, text):
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def append_error(self, text):
        self.error_text.insert(tk.END, text + "\n")
        self.error_text.see(tk.END)

    # Devuelve esta parte del estado a sus valores iniciales seguros.
    def reset_outputs(self, keep_code=True):
        for box in [self.output_text, self.error_text, self.vm_output_text]:
            box.configure(state="normal")
            box.delete("1.0", tk.END)
            if box is self.vm_output_text:
                box.configure(state="disabled")
        self._clear_tree(self.token_tree)
        self._clear_tree(self.symbol_tree)
        self._clear_tree(self.function_tree)
        for tree in [self.tac_tree, self.tac_optimized_tree, self.target_tree]:
            self._clear_tree(tree)
        if hasattr(self, "ast_info_text"):
            self.ast_info_text.configure(state="normal")
            self.ast_info_text.delete("1.0", tk.END)
            self.ast_info_text.insert(
                "1.0",
                "Compile code to generate the AST files.\n\n"
                "This tab no longer embeds a PNG preview. Use Open SVG Viewer to see the complete tree in your browser."
            )
            self.ast_info_text.configure(state="disabled")
        self.update_status("Ready", "success")
        if not keep_code:
            self.code_input.delete("1.0", tk.END)
            self.current_file_path = None
            self.update_line_numbers()
            self.schedule_highlight()
        self.set_placeholder_texts()

    # Limpia datos visibles o temporales para iniciar una nueva corrida.
    def clear_all(self):
        self.reset_outputs(keep_code=False)
        self.reset_stage_cards()
        self.tabs.set("Output")

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def set_placeholder_texts(self):
        instruction_placeholders = [
            (self.tac_tree, self.tac_summary_label, "TAC", "Compile code to generate TAC."),
            (self.tac_optimized_tree, self.tac_optimized_summary_label, "TAC Optimized", "Compile code to generate optimized TAC."),
            (self.target_tree, self.target_summary_label, "Target Code", "Compile code to generate target code."),
        ]
        for tree, summary_label, title, message in instruction_placeholders:
            self._insert_instruction_placeholder(tree, message)
            self._set_instruction_summary(summary_label, f"{title}: {message}", self.THEME['muted'])

        if hasattr(self, "vm_output_text"):
            self._set_vm_summary(
                self.vm_summary_label,
                "VM Output: compile code to run the VM.",
                self.THEME['muted'],
            )
            self.vm_output_text.configure(state="normal")
            self.vm_output_text.delete("1.0", tk.END)
            self.vm_output_text.insert("1.0", "Compile code to see the explicit output of the VM here.")
            self.vm_output_text.configure(state="disabled")

        if hasattr(self, "ast_info_text"):
            self.ast_info_text.configure(state="normal")
            self.ast_info_text.delete("1.0", tk.END)
            self.ast_info_text.insert(
                "1.0",
                "Compile code to generate the AST files.\n\n"
                "This tab no longer embeds a PNG preview. Use Open SVG Viewer to see the complete tree in your browser."
            )
            self.ast_info_text.configure(state="disabled")

    # ---------------------------------------------------------------------
    # Grammar viewer
    # ---------------------------------------------------------------------
    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _ensure_grammar_viewer(self, silent=False):
        """Generates assets/grammar/index.html once, outside compilation output folders."""
        try:
            from parser_sdt.parsertable import productions, terminales, no_terminales
            terminals = terminales
            no_terminals = no_terminales
        except Exception as exc:
            if not silent:
                messagebox.showerror("Grammar", f"Could not load grammar:\n{exc}")
            return None

        grammar_dir = os.path.join(SRC_ROOT, "assets", "grammar")
        os.makedirs(grammar_dir, exist_ok=True)
        template_path = os.path.join(grammar_dir, "grammar_template.html")
        css_path = os.path.join(grammar_dir, "grammar.css")
        js_path = os.path.join(grammar_dir, "grammar.js")

        missing_assets = [path for path in (template_path, css_path, js_path) if not os.path.exists(path)]
        if missing_assets:
            if not silent:
                messagebox.showerror(
                    "Grammar",
                    "Missing grammar viewer asset(s):\n" + "\n".join(missing_assets)
                )
            return None

        grouped = {}
        for index, production in enumerate(productions):
            try:
                lhs, rhs = production
            except Exception:
                continue
            grouped.setdefault(lhs, []).append((index, rhs))

        def symbol_span(symbol):
            symbol = str(symbol)
            css = "terminal" if symbol in terminals else "nonterminal" if symbol in no_terminals else "symbol"
            return f'<span class="{css}">{html.escape(symbol)}</span>'

        def rhs_html(rhs):
            if not rhs:
                return '<span class="epsilon">ε</span>'
            return " ".join(symbol_span(sym) for sym in rhs)

        def plain_rhs(rhs):
            return "ε" if not rhs else " ".join(map(str, rhs))

        cards = []
        table_rows = []
        for lhs, alternatives in grouped.items():
            alt_html = []
            for alt_index, (prod_index, rhs) in enumerate(alternatives):
                prefix = "→" if alt_index == 0 else "|"
                search = html.escape((lhs + " " + plain_rhs(rhs)).lower())
                alt_html.append(
                    f'<div class="alt" data-search="{search}">'
                    f'<span class="prod-num">P{prod_index:03d}</span>'
                    f'<span class="arrow">{prefix}</span>'
                    f'<span class="rhs">{rhs_html(rhs)}</span>'
                    '</div>'
                )
                table_rows.append(
                    f'<tr data-search="{search}"><td>P{prod_index:03d}</td>'
                    f'<td>{symbol_span(lhs)}</td><td class="arrow-cell">→</td><td>{rhs_html(rhs)}</td></tr>'
                )
            cards.append(
                f'<section class="grammar-card" data-search="{html.escape(lhs.lower())}">'
                f'<div class="lhs">{symbol_span(lhs)}</div><div class="alts">{"".join(alt_html)}</div></section>'
            )

        with open(template_path, "r", encoding="utf-8") as f:
            doc = f.read()

        replacements = {
            "{{PRODUCTION_COUNT}}": str(len(productions)),
            "{{GROUP_COUNT}}": str(len(grouped)),
            "{{TERMINAL_COUNT}}": str(len(terminals)),
            "{{NON_TERMINAL_COUNT}}": str(len(no_terminals)),
            "{{VISIBLE_COUNT}}": str(len(grouped)),
            "{{THEME_STYLE}}": self._theme_css_variables(),
            "{{GRAMMAR_CARDS}}": "".join(cards),
            "{{GRAMMAR_ROWS}}": "".join(table_rows),
        }
        for key, value in replacements.items():
            doc = doc.replace(key, value)

        grammar_path = os.path.join(grammar_dir, "index.html")
        with open(grammar_path, "w", encoding="utf-8") as f:
            f.write(doc)

        self.grammar_html_path = grammar_path
        return grammar_path

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def show_grammar_window(self):
        """Opens the grammar viewer generated under assets/grammar instead of outputs/<run>."""
        grammar_path = self._ensure_grammar_viewer(silent=False)
        if not grammar_path:
            return
        self.update_status("Grammar viewer opened", "success")
        self._open_path_in_browser(grammar_path)

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def _open_path_in_browser(self, path):
        path = os.path.abspath(path)
        if sys.platform == "darwin":
            for browser in ["Google Chrome", "Safari", "Firefox", "Microsoft Edge", "Brave Browser", "Arc"]:
                try:
                    subprocess.run(["open", "-a", browser, path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except Exception:
                    pass
        webbrowser.open_new_tab(Path(path).resolve().as_uri())

    # ---------------------------------------------------------------------
    # File operations
    # ---------------------------------------------------------------------
    # Abre el recurso solicitado usando la herramienta disponible del sistema.
    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open source file",
            filetypes=[("C code / text", "*.c *.h *.txt"), ("All files", "*.*")],
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

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def save_file(self):
        path = filedialog.asksaveasfilename(
            title="Save code",
            defaultextension=".c",
            filetypes=[("C code", "*.c"), ("Text", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.get_code())
        self.current_file_path = path
        self.update_status(f"Code saved: {os.path.basename(path)}", "success")


# Coordina el modo de ejecución cuando el archivo se llama desde terminal.
def main():
    root = ctk.CTk()
    app = CompilerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
