import os
import sys

SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

#verificar dependencias
from deps_checker import check_all, show_gui_warning

obligatorias_ok, resultados, recomendaciones = check_all()

if not obligatorias_ok:
    #mostrar error y salir
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    from tkinter import messagebox
    messagebox.showerror(
        "Error de dependencias",
        "Tkinter no esta instalado.\n\nInstale Tkinter con:\nbrew install python-tk"
    )
    sys.exit(1)

#verificar dependencias opcionales y mostrar advertencia
missing_opcionales = [dep for dep, (ok, _) in resultados.items() if not ok and dep != 'tkinter']
if missing_opcionales:
    show_gui_warning(missing_opcionales, recomendaciones)

PILLOW_AVAILABLE = resultados['pillow'][0]
GRAPHVIZ_AVAILABLE = resultados['graphviz'][0]

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk

if PILLOW_AVAILABLE:
    from PIL import Image, ImageTk
else:
    Image = None
    ImageTk = None

import lexer.lector as lector
import parser_sdt.syntax_parser as parser
from parser_sdt.sdt import tabla_simbolos


class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Parser & SDT - Team 05 Compiler")
        self.root.geometry("1300x750")
        self.root.configure(bg='#2b2b2b')
        
        self.create_widgets()
    
    def _on_image_configure(self, event):
        """Actualizar el área de scroll cuando la imagen cambia de tamaño"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        """Centrar la imagen cuando el canvas cambia de tamaño"""
        canvas_width = event.width
        bbox = self.canvas.bbox('all')
        if bbox:
            bbox_width = bbox[2] - bbox[0]
            if bbox_width < canvas_width:
                self.canvas.move('all', (canvas_width - bbox_width) // 2, 0)
        
    def create_widgets(self):
        # PanedWindow para dividir izquierda/derecha
        main_pane = tk.PanedWindow(self.root, bg='#2b2b2b', sashwidth=5, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo (Entrada)
        left_frame = tk.Frame(main_pane, bg='#3c3f41')
        main_pane.add(left_frame, width=500)
        
        tk.Label(left_frame, text="📝 Code Editor", bg='#3c3f41', fg='white',
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=5, pady=5)
        
        self.code_input = scrolledtext.ScrolledText(left_frame, height=20,
                                                      font=('Consolas', 11),
                                                      bg='#2b2b2b', fg='#e6e6e6',
                                                      insertbackground='white')
        self.code_input.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.code_input.insert('1.0', 'float y = (2 + 3) * 4;')
        
        # Botones
        button_frame = tk.Frame(left_frame, bg='#3c3f41')
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.compile_btn = tk.Button(button_frame, text="🔨 Compile", 
                              command=self.compile_code,
                              bg='#2c3e50', fg="#292929",
                              activebackground='#34495e',
                              activeforeground='white',
                              font=('Arial', 10, 'bold'),
                              padx=20, pady=5,
                              relief=tk.FLAT, bd=1)
        self.compile_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.clear_btn = tk.Button(button_frame, text="🗑 Clear All", 
                                    command=self.clear_all,
                                    bg='#7f8c8d', fg="#292929",
                                    activebackground='#95a5a6',
                                    activeforeground='white',
                                    font=('Arial', 10, 'bold'),
                                    padx=20, pady=5,
                                    relief=tk.FLAT, bd=1)
        self.clear_btn.pack(side=tk.LEFT)
        
        # Panel derecho (Resultados)
        right_frame = tk.Frame(main_pane, bg='#3c3f41')
        main_pane.add(right_frame, width=700)
        
        # Notebook (pestañas)
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestañas
        self.create_output_tab(notebook)
        self.create_symbol_table_tab(notebook)
        self.create_ast_tab(notebook)
        self.create_ast_image_tab(notebook)
        
    def create_output_tab(self, notebook):
        tab = tk.Frame(notebook, bg='#3c3f41')
        notebook.add(tab, text="📤 Output")
        
        self.output_text = scrolledtext.ScrolledText(tab, font=('Consolas', 10),
                                                       bg='#1e1e1e', fg='#d4d4d4')
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_label = tk.Label(tab, text="✅ Ready", bg='#3c3f41', fg='#4caf50',
                                      font=('Arial', 10), anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=5, pady=(0, 5))
        
    def create_symbol_table_tab(self, notebook):
        tab = tk.Frame(notebook, bg='#3c3f41')
        notebook.add(tab, text="📋 Symbol Table")
        
        columns = ('Variable', 'Type', 'Value')
        self.symbol_tree = ttk.Treeview(tab, columns=columns, show='headings', height=18)
        
        self.symbol_tree.heading('Variable', text='Variable Name')
        self.symbol_tree.heading('Type', text='Type')
        self.symbol_tree.heading('Value', text='Value')
        
        self.symbol_tree.column('Variable', width=150)
        self.symbol_tree.column('Type', width=100)
        self.symbol_tree.column('Value', width=150)
        
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.symbol_tree.yview)
        self.symbol_tree.configure(yscrollcommand=scrollbar.set)
        
        self.symbol_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
    def create_ast_tab(self, notebook):
        tab = tk.Frame(notebook, bg='#3c3f41')
        notebook.add(tab, text="🌲 AST (Text)")
        
        self.ast_text = scrolledtext.ScrolledText(tab, font=('Consolas', 10),
                                                    bg='#1e1e1e', fg='#d4d4d4')
        self.ast_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def create_ast_image_tab(self, notebook):
        """Pestaña para mostrar la imagen del AST generada por Graphviz"""
        tab = tk.Frame(notebook, bg='#3c3f41')
        notebook.add(tab, text="🌲 AST (Image)")
        
        # Frame para contener la imagen y scroll
        image_frame = tk.Frame(tab, bg='#3c3f41')
        image_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas con scroll para la imagen
        self.canvas = tk.Canvas(image_frame, bg='#1e1e1e')
        scrollbar_v = tk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_h = tk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Label para mostrar la imagen dentro del canvas
        self.ast_image_label = tk.Label(self.canvas, bg='#1e1e1e')
        self.canvas.create_window((0, 0), window=self.ast_image_label, anchor='nw')
        
        self.ast_image_label.bind('<Configure>', self._on_image_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
    def compile_code(self):
        self.output_text.delete('1.0', tk.END)
        self.ast_text.delete('1.0', tk.END)
        self.clear_symbol_table()
        self.clear_ast_image()
        
        code = self.code_input.get('1.0', tk.END).strip()
        
        if not code:
            self.append_output("[ERROR] No code to compile.\n")
            self.update_status("❌ No code to compile", 'error')
            return
            
        self.append_output(f"{'='*60}\n")
        self.append_output(f"📄 INPUT:\n{code}\n")
        self.append_output(f"{'='*60}\n\n")
        
        try:
            tokens = lector.analizeterminal(code)
            
            if tokens is None:
                self.append_output("[ERROR] Lexical analysis failed.\n")
                self.update_status("❌ Lexical Error", 'error')
                return
                
            self.append_output("[✓] Lexical analysis: SUCCESS\n\n")
            
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                result = parser.analizar(tokens)
            
            output = f.getvalue()
            self.append_output(output)
            
            if "Parse/AST tree:" in output:
                ast_part = output.split("Parse/AST tree:")[1].split("AST DOT generated")[0]
                self.ast_text.insert(tk.END, ast_part.strip())
            
            if result:
                self.update_status("✅ Parsing Success! SDT Verified!", 'success')
                self.append_output("\n[✓] COMPILATION SUCCESSFUL\n")
                self.load_symbol_table()
                self.load_ast_image()
            else:
                self.update_status("❌ Compilation failed", 'error')
                
        except Exception as e:
            self.append_output(f"[ERROR] {str(e)}\n")
            self.update_status(f"❌ Error: {str(e)}", 'error')
            
    def append_output(self, text):
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        
    def clear_symbol_table(self):
        for item in self.symbol_tree.get_children():
            self.symbol_tree.delete(item)
            
    def load_symbol_table(self):
        from parser_sdt.sdt import tabla_simbolos
        
        self.clear_symbol_table()
        
        for name, data in tabla_simbolos.simbolos.items():
            self.symbol_tree.insert('', tk.END, values=(
                name,
                data.get('tipo', 'unknown'),
                data.get('valor', 'None')
            ))
            
        if len(tabla_simbolos.simbolos) == 0:
            self.symbol_tree.insert('', tk.END, values=('(empty)', '(empty)', '(empty)'))
            
    def load_parse_table(self):
        from parser_sdt.parsertable import tabla_action, tabla_goto
        
        self.parse_table_text.delete('1.0', tk.END)
        
        self.parse_table_text.insert(tk.END, "="*60 + "\n")
        self.parse_table_text.insert(tk.END, "ACTION TABLE (LALR)\n")
        self.parse_table_text.insert(tk.END, "="*60 + "\n\n")
        
        for state, actions in list(tabla_action.items())[:40]:
            self.parse_table_text.insert(tk.END, f"State {state}: {actions}\n")
            
        if len(tabla_action) > 40:
            self.parse_table_text.insert(tk.END, f"\n... and {len(tabla_action)-40} more states\n")
            
        self.parse_table_text.insert(tk.END, "\n" + "="*60 + "\n")
        self.parse_table_text.insert(tk.END, "GOTO TABLE\n")
        self.parse_table_text.insert(tk.END, "="*60 + "\n\n")
        
        for state, gotos in list(tabla_goto.items())[:40]:
            self.parse_table_text.insert(tk.END, f"State {state}: {gotos}\n")
            
    def update_status(self, message, status_type='normal'):
        self.status_label.config(text=message)
        
        if status_type == 'error':
            self.status_label.config(fg="#f44336")
        elif status_type == 'success':
            self.status_label.config(fg="#4caf50")
        else:
            self.status_label.config(fg="#e6e6e6")
            
    def clear_all(self):
        self.code_input.delete('1.0', tk.END)
        self.output_text.delete('1.0', tk.END)
        self.ast_text.delete('1.0', tk.END)
        self.clear_symbol_table()
        self.parse_table_text.delete('1.0', tk.END)
        self.update_status("✅ Ready", 'success')

    def clear_ast_image(self):
        """Limpiar la imagen del AST"""
        self.ast_image_label.config(image='')
        self.ast_image_label.image = None

    def load_ast_image(self):
        """Cargar la imagen del AST generada por Graphviz"""
        import os
        from PIL import Image, ImageTk
        
        ast_png_path = os.path.join(os.path.dirname(__file__), 'ast.png')
        
        if os.path.exists(ast_png_path):
            try:
                # Abrir y redimensionar la imagen si es muy grande
                image = Image.open(ast_png_path)
                
                # Redimensionar si es muy grande (máximo 800x600)
                max_width, max_height = 800, 600
                if image.width > max_width or image.height > max_height:
                    ratio = min(max_width / image.width, max_height / image.height)
                    new_size = (int(image.width * ratio), int(image.height * ratio))
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                
                self.ast_image = ImageTk.PhotoImage(image)
                self.ast_image_label.config(image=self.ast_image)
                self.ast_image_label.image = self.ast_image
                
                # Actualizar scroll region
                self.canvas.configure(scrollregion=self.canvas.bbox('all'))
                
            except Exception as e:
                self.ast_image_label.config(text=f"Error loading AST image:\n{str(e)}", 
                                            fg='#f44336', bg='#1e1e1e')
        else:
            self.ast_image_label.config(text="No AST image available.\nRun compilation first.", 
                                        fg='#888888', bg='#1e1e1e')

def main():
    root = tk.Tk()
    app = CompilerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()