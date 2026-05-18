from MiniLangLexer import MiniLangLexer
from MiniLangParser import parser
from MiniLangParser import errores_sintacticos
# importar analizador semantico
from AnalizadorSemantico import AnalizadorSemantico

import os
import tkinter
# importar ttk para usar el Treeview para Tabla
from tkinter import filedialog, messagebox, scrolledtext, ttk

ABS_PATH = os.path.abspath(os.path.dirname(__file__))
DOCS_DIR = os.path.join(ABS_PATH, "docs")
OUTPUTS_DIR = os.path.join(ABS_PATH, "outputs")

def ensure_dirs():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

def run_analyzer(source_tuple, outputs_dir):
    try:
        os.makedirs(outputs_dir, exist_ok=True)
        
        if source_tuple[0] == "file":
            with open(source_tuple[1], 'r', encoding='utf-8') as f:
                codigo = f.read()
            base_name = os.path.basename(source_tuple[1]).rsplit('.', 1)[0]
        else:
            codigo = source_tuple[1]
            base_name = "codigo_temporal"

        errores_sintacticos.clear()
        lexer = MiniLangLexer()
        lexer.errores = []
        
        resultado = parser.parse(input=codigo, lexer=lexer, debug=False)

        errores_totales = lexer.errores + errores_sintacticos
        # variable para extraer la tabla y mostrarla en la GUI
        semantico_historico = []

        # si no hay errores criticos ejecutar el semantico
        if not errores_totales and resultado:
            semantico = AnalizadorSemantico()
            semantico.visitar(resultado) 
            
            # Unimos los errores semánticos a la consola
            errores_totales.extend(semantico.errores)
            errores_totales.extend(semantico.warnings)
            semantico_historico = semantico.ts.tabla_historica

            # generacion del archivo .csv de la Tabla de Símbolos
            ts_path = os.path.join(outputs_dir, f"{base_name}_tabla_simbolos.csv")
            with open(ts_path, 'w', encoding='utf-8') as f:
                f.write("Nombre,Tipo,Valor,Rol,Linea,Columna,Ambito\n")
                for sim in semantico_historico:
                    val = sim['valor'] if sim['valor'] is not None else 'NULL'
                    f.write(f"{sim['nombre']},{sim['tipo']},{val},{sim['rol']},{sim['linea']},{sim['columna']},{sim['ambito']}\n")

        out_path = os.path.join(outputs_dir, f"{base_name}_tokens.out")
        with open(out_path, 'w', encoding='utf-8') as f:
            for tk in lexer.tokens:
                if tk.tipo != 'EOF':
                    f.write(f"{tk}\n")

        err_path = os.path.join(outputs_dir, f"{base_name}_errores.err")
        with open(err_path, 'w', encoding='utf-8') as f:
            if errores_totales:
                for err in errores_totales:
                    f.write(f"{err}\n")
            else:
                f.write("OK\n")

        return True, errores_totales, base_name, semantico_historico
    except Exception as e:
        return False, str(e), None, []

class AreaConLineas(tkinter.Frame):
    def __init__(self, master, bg_color, fg_color, bg_lineas, fg_lineas, font_style, height=10, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.text = scrolledtext.ScrolledText(
            self, bg=bg_color, fg=fg_color, font=font_style, height=height,
            insertbackground=fg_color, undo=True, wrap=tkinter.NONE, bd=0
        )
        self.text.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=True)

        self.canvas_lineas = tkinter.Canvas(self, width=45, bg=bg_lineas, highlightthickness=0)
        self.canvas_lineas.pack(side=tkinter.LEFT, fill=tkinter.Y)

        for evento in ["<KeyRelease>", "<MouseWheel>", "<Configure>", "<Button-1>", "<Return>"]:
            self.text.bind(evento, self._actualizar)
            
        self.fg_lineas = fg_lineas
        self._actualizar()

    def _actualizar(self, event=None):
        self.after(10, self._redibujar)

    def _redibujar(self):
        self.canvas_lineas.delete("all")
        i = self.text.index("@0,0")
        while True:
            dline = self.text.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            num_linea = str(i).split(".")[0]
            self.canvas_lineas.create_text(38, y, anchor="ne", text=num_linea, font=self.text.cget("font"), fill=self.fg_lineas)
            i = self.text.index(f"{i}+1line")

    def delete(self, *args):
        self.text.delete(*args)
        self._actualizar()

    def insert(self, *args):
        self.text.insert(*args)
        self._actualizar()

    def get(self, *args):
        return self.text.get(*args)

class DarkEditor(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analizador Lex/Sint/Sem - MiniLang")
        self.geometry("1350x760")
        self.configure(bg="#2b0f14")
        self.current_filepath = None
        self.last_analyzed_basename = None 
        ensure_dirs()
        self._configurar_estilos_tabla()
        self._build_ui()

    # pintar el Treeview como si fuera Excel oscuro
    def _configurar_estilos_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#3a0f16",
                        foreground="#ffffff",
                        rowheight=25,
                        fieldbackground="#3a0f16",
                        bordercolor="#2b0f14",
                        borderwidth=0)
        style.map('Treeview', background=[('selected', '#9b4b52')])
        style.configure("Treeview.Heading",
                        background="#2b0f14",
                        foreground="#f3b2bc",
                        font=('Arial', 10, 'bold'),
                        borderwidth=1)
        style.map("Treeview.Heading", background=[('active', '#3a0f16')])

    def _build_ui(self):
        top = tkinter.Frame(self, bg="#2b0f14")
        top.pack(side=tkinter.TOP, fill=tkinter.X, padx=20, pady=15)
        
        btns = [
            ("Abrir Archivo", self.open_file),
            ("Guardar Archivo", self.save_file),
            ("Guardar Como", self.save_file_as),
            ("Analizar Código", self.analyze_current_file_or_text),
        ]

        for name, cmd in btns:
            b = tkinter.Button(top, text=name, command=cmd,
                               bg="#9b4b52", fg="#ffffff", activebackground="#b35a60",
                               bd=0, padx=12, pady=8, font=("Arial", 10, "bold"))
            b.pack(side=tkinter.LEFT, padx=8)

        tkinter.Label(top, text="Compilador MiniLang",
                      bg="#2b0f14", fg="#f3b2bc", font=("Arial", 12, "bold")).pack(side=tkinter.RIGHT, padx=20)

        workspace = tkinter.Frame(self, bg="#2b0f14")
        workspace.pack(fill=tkinter.BOTH, expand=True, padx=20, pady=(0,20))

        # lado Derecho para la TS interactiva
        right = tkinter.Frame(workspace, bg="#2b0f14")
        right.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=True, padx=(20,0))

        tkinter.Label(right, text="Tabla de Símbolos (Memoria)", bg="#2b0f14", fg="#f3b2bc", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,4))

        table_container = tkinter.Frame(right, bg="#2b0f14")
        table_container.pack(fill=tkinter.BOTH, expand=True, pady=(0,15))

        columnas = ("Nombre", "Tipo", "Valor", "Rol", "Linea", "Col", "Ambito")
        self.tree = ttk.Treeview(table_container, columns=columnas, show="headings", height=15)
        
        anchos = {"Nombre": 100, "Tipo": 70, "Valor": 70, "Rol": 80, "Linea": 50, "Col": 50, "Ambito": 60}
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=anchos[col], anchor=tkinter.CENTER)
            
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

        btn_frame = tkinter.Frame(right, bg="#2b0f14")
        btn_frame.pack(fill=tkinter.X)
        
        btn_style = {"bg": "#9b4b52", "fg": "#ffffff", "activebackground": "#b35a60", "bd": 0, "padx": 12, "pady": 8, "font": ("Arial", 10, "bold")}
        
        tkinter.Button(btn_frame, text="Ver Tokens (.out)", command=lambda: self.open_last_output("_tokens.out"), **btn_style).pack(side=tkinter.LEFT, expand=True, fill=tkinter.X, padx=(0, 5))
        tkinter.Button(btn_frame, text="Contacto", command=self.help_text, **btn_style).pack(side=tkinter.LEFT, expand=True, fill=tkinter.X, padx=(5, 0))

        # lado Izquierdo ahora contiene solo Código y Errores
        left = tkinter.Frame(workspace, bg="#2b0f14")
        left.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

        tkinter.Label(left, text="Archivo de texto", bg="#2b0f14", fg="#f3b2bc", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,4))

        self.text_area = AreaConLineas(
            left, bg_color="#ffffff", fg_color="#111111", bg_lineas="#f0f0f0", fg_lineas="#999999", font_style=("Consolas", 12), height=15
        )
        self.text_area.pack(fill=tkinter.BOTH, expand=True, pady=(0,15))

        tkinter.Label(left, text="Consola / Errores", bg="#2b0f14", fg="#f3b2bc", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,4))

        self.error_area = AreaConLineas(
            left, bg_color="#ffffff", fg_color="#111111", bg_lineas="#f0f0f0", fg_lineas="#999999", font_style=("Consolas", 10), height=8 
        )
        self.error_area.pack(fill=tkinter.X)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos MiniLang","*.mlng")])
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete(1.0, tkinter.END)
            self.text_area.insert(tkinter.END, content)
            self.current_filepath = path
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir:\n{e}")

    def save_file(self):
        if self.current_filepath:
            try:
                with open(self.current_filepath, "w", encoding="utf-8") as f:
                    f.write(self.text_area.get(1.0, tkinter.END))
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".mlng", filetypes=[("Archivos MiniLang","*.mlng")])
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_area.get(1.0, tkinter.END))
            self.current_filepath = path
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def open_last_output(self, extension):
        if not self.last_analyzed_basename:
            messagebox.showwarning("Aviso", "Aún no has analizado ningún código.")
            return
        
        filename = self.last_analyzed_basename + extension
        path = os.path.join(OUTPUTS_DIR, filename)
        
        if not os.path.exists(path):
            messagebox.showwarning("No encontrado", f"No se encontró {filename}.")
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete(1.0, tkinter.END)
            self.text_area.insert(tkinter.END, content)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al abrir archivo:\n{e}")

    def analyze_current_file_or_text(self):
        text_content = self.text_area.get(1.0, tkinter.END).strip()
        if not text_content: return
        
        if self.current_filepath: 
            self.save_file()
        
        source = ("text", text_content)
        ok, errores, basename, tabla_simbolos = run_analyzer(source, OUTPUTS_DIR)
        
        self.error_area.delete(1.0, tkinter.END)
        # limpiar la tabla en la GUI antes de cada analisis
        for item in self.tree.get_children():
            self.tree.delete(item)

        if ok:
            self.last_analyzed_basename = basename
            
            if len(errores) == 0:
                self.error_area.insert(tkinter.END, "OK")
            else:
                for err in errores:
                    self.error_area.insert(tkinter.END, f"{err}\n")
                    
            # lleanr la tabla de simbolos GUI iterando sobre los datos recuperados por el analizador semantico
            for sim in tabla_simbolos:
                val = sim['valor'] if sim['valor'] is not None else 'NULL'
                self.tree.insert("", tkinter.END, values=(sim['nombre'], sim['tipo'], val, sim['rol'], sim['linea'], sim['columna'], sim['ambito']))
        else:
            messagebox.showerror("Error de Análisis", f"El compilador falló críticamente:\n{errores}")

    def help_text(self):
        help_text = "Compilador MiniLang - Fase #3\n\nDesarrolladoras:\n- Lizbeth Andrea Herrera Ortega\n- Marcela Nicole Letran Lee"
        self.text_area.delete(1.0, tkinter.END)
        self.text_area.insert(tkinter.END, help_text)

if __name__ == "__main__":
    app = DarkEditor()
    app.mainloop()
