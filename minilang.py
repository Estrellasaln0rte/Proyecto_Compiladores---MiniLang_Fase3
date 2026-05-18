# Analizador
from MiniLangLexer import MiniLangLexer
from MiniLangParser import parser
from MiniLangParser import errores_sintacticos

import sys
# Interfaz
import os
import tkinter
from tkinter import filedialog, messagebox, scrolledtext
import webbrowser

# rutas y carpetas
ABS_PATH = os.path.abspath(os.path.dirname(__file__))
DOCS_DIR = os.path.join(ABS_PATH, "docs")
OUTPUTS_DIR = os.path.join(ABS_PATH, "outputs")

def ensure_dirs():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

# hook conexion GUI
def run_analyzer(source_tuple, outputs_dir):
    try:
        os.makedirs(outputs_dir, exist_ok=True)
        
        # Determinar el nombre base para los archivos de salida
        if source_tuple[0] == "file":
            with open(source_tuple[1], 'r', encoding='utf-8') as f:
                codigo = f.read()
            base_name = os.path.basename(source_tuple[1]).rsplit('.', 1)[0]
        else:
            codigo = source_tuple[1]
            base_name = "codigo_temporal"

        # Ejecutar Lexer y Parser
        errores_sintacticos.clear()
        lexer = MiniLangLexer()
        lexer.errores = []
        
        resultado = parser.parse(input=codigo, lexer=lexer, debug=False)

        errores_totales = lexer.errores + errores_sintacticos

        # tokens .out
        out_path = os.path.join(outputs_dir, f"{base_name}_tokens.out")
        with open(out_path, 'w', encoding='utf-8') as f:
            for tk in lexer.tokens:
                if tk.tipo != 'EOF':
                    f.write(f"{tk}\n")

        # errores .err
        err_path = os.path.join(outputs_dir, f"{base_name}_errores.err")
        with open(err_path, 'w', encoding='utf-8') as f:
            if errores_totales:
                for err in errores_totales:
                    f.write(f"{err}\n")
            else:
                f.write("OK: No se encontraron errores léxicos ni sintácticos\n")

        return True, errores_totales, base_name
    except Exception as e:
        return False, str(e), None

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

# tkinter
class DarkEditor(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analizador Léxico y Sintáctico - MiniLang")
        self.geometry("1100x720")
        self.configure(bg="#2b0f14")
        self.current_filepath = None
        self.last_analyzed_basename = None 
        ensure_dirs()
        self._build_ui()

    # formas
    def _build_ui(self):
        # Barra superior
        top = tkinter.Frame(self, bg="#2b0f14")
        #Bordes superior
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

        # Derecha panel de botones de apertura
        right = tkinter.Frame(workspace, bg="#3a0f16", width=280)
        right.pack(side=tkinter.RIGHT, fill=tkinter.Y, padx=(20,0))

        tkinter.Label(right, text="Documentación", bg="#3a0f16", fg="#f3b2bc", font=("Arial", 12, "bold")).pack(pady=(18,15))
        
        btn_style = {"bg": "#9b4b52", "fg": "#ffffff", "activebackground": "#b35a60", "bd": 0, "padx": 12, "pady": 8, "font": ("Arial", 10, "bold")}
        
        tkinter.Button(right, text="Abrir README", command=lambda: self.open_doc("README.md"), **btn_style).pack(fill=tkinter.X, pady=8, padx=30)
        tkinter.Button(right, text="Abrir Tokens", command=lambda: self.open_last_output("_tokens.out"), **btn_style).pack(fill=tkinter.X, pady=8, padx=30)
        tkinter.Button(right, text="Contacto", command=self.help_text, **btn_style).pack(fill=tkinter.X, pady=8, padx=30)

        # Izquierda agrupa el texto y errores para igualar anchos
        left = tkinter.Frame(workspace, bg="#2b0f14")
        left.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

        tkinter.Label(left, text="Archivo de texto", bg="#2b0f14", fg="#f3b2bc", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,4))

        self.text_area = AreaConLineas(
            left,
            bg_color="#ffffff",      
            fg_color="#111111",      
            bg_lineas="#f0f0f0",     
            fg_lineas="#999999",     
            font_style=("Consolas", 12),
            height=20
        )
        self.text_area.pack(fill=tkinter.BOTH, expand=True, pady=(0,15)) # : espaciado

        # Título de Errores
        tkinter.Label(left, text="Errores", bg="#2b0f14", fg="#f3b2bc", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,4))

        self.error_area = AreaConLineas(
            left,
            bg_color="#ffffff",
            fg_color="#111111", 
            bg_lineas="#f0f0f0",
            fg_lineas="#999999",
            font_style=("Consolas", 10),
            height=10 
        )
        self.error_area.pack(fill=tkinter.X)

# funciones de archivo
    def open_file(self):
        path = filedialog.askopenfilename(
            title="Abrir código fuente",
            filetypes=[("Archivos MiniLang","*.mlng")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete(1.0, tkinter.END)
            self.text_area.insert(tkinter.END, content)
            self.current_filepath = path
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")

    def save_file(self):
        if self.current_filepath:
            try:
                with open(self.current_filepath, "w", encoding="utf-8") as f:
                    f.write(self.text_area.get(1.0, tkinter.END))
                messagebox.showinfo("Guardado", "Archivo guardado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".ming",
            filetypes=[("Archivos MiniLang","*.mlng")],
            title="Guardar como"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_area.get(1.0, tkinter.END))
            self.current_filepath = path
            messagebox.showinfo("Guardado", "Archivo guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")

    def open_doc(self, filename):
        path = os.path.join(DOCS_DIR, filename)
        if not os.path.exists(path):
            path = os.path.join(ABS_PATH, filename)
            
        if not os.path.exists(path):
            messagebox.showwarning("No encontrado", f"No se encontró el archivo '{filename}'")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.text_area.delete(1.0, tkinter.END)
            self.text_area.insert(tkinter.END, content)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el documento:\n{e}")

    def open_last_output(self, extension):
        if not self.last_analyzed_basename:
            messagebox.showwarning("Aviso", "Aún no has analizado ningún código.")
            return
        
        filename = self.last_analyzed_basename + extension
        path = os.path.join(OUTPUTS_DIR, filename)
        
        if not os.path.exists(path):
            messagebox.showwarning("No encontrado", f"No se encontró el archivo de salida {filename}.")
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            self.text_area.delete(1.0, tkinter.END)
            self.text_area.insert(tkinter.END, content)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo de salida:\n{e}")

# ejec analizador
    def analyze_current_file_or_text(self):
        text_content = self.text_area.get(1.0, tkinter.END).strip()
        
        if not text_content:
            messagebox.showwarning("Vacío", "El editor está vacío.")
            return
        
        if self.current_filepath: 
            respuesta = messagebox.askyesno("Guardar archivo", "¿Desea guardar antes de analizar?")
            if respuesta: 
                self.save_file()
        
        source = ("text", text_content)
            
        ok, errores, basename = run_analyzer(source, OUTPUTS_DIR)
        self.error_area.delete(1.0, tkinter.END)

        if ok:
            self.last_analyzed_basename = basename

            if len(errores) == 0:
                messagebox.showinfo("Resultado de Análisis", "No se encontraron errores")
                self.error_area.insert(tkinter.END, "No hay errores\n")
            else:
                messagebox.showwarning("Resultado de Análisis", f"Se encontraron {len(errores)} error(es)")
                for err in errores:
                    self.error_area.insert(tkinter.END, f"{err}\n")
        else:
            messagebox.showerror("Error de Análisis", f"El compilador falló críticamente")

    def help_text(self):
        help_text = (
            "Compilador MiniLang - Análisis Léxico y Sintáctico\n\n"
            "Desarrolladoras:\n"
            "- Lizbeth Andrea Herrera Ortega – 1246024\n"
            "- Marcela Nicole Letran Lee – 1102124\n"
        )
        self.text_area.delete(1.0, tkinter.END)
        self.text_area.insert(tkinter.END, help_text)

if __name__ == "__main__":
    app = DarkEditor()
    app.mainloop()
