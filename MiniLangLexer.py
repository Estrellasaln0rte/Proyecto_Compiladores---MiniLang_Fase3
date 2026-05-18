import ply.lex as lex

# tokens para uso en gramatica
tokens = (
    'CONST',
    'VOID',
    'ID', 
    'NUM_INT', 
    'NUM_FLOAT', 
    'STRING_LINE',
    'INT', 
    'FLOAT', 
    'STRING', 
    'BOOL',  
    'IF', 
    'ELSE', 
    'WHILE', 
    'READ', 
    'WRITE', 
    'TRUE', 
    'FALSE', 
    'RETURN', 
    'OR', 
    'AND', 
    'NOT', 
    'APAREN', 
    'CPAREN', 
    'ALLAVE', 
    'CLLAVE', 
    'PUNTOCOMA', 
    'COMA', 
    'IGUAL', 
    'MAS', 
    'MENOS', 
    'MULT', 
    'DIV', 
    'MAYQ', 
    'MENQ', 
    'MAYOQ', 
    'MENOQ', 
    'IG', 
    'NOIG'
)

RESERVADAS = {
    'int': 'INT', 'float': 'FLOAT', 'string': 'STRING', 'bool': 'BOOL', 'const': 'CONST', 'void': 'VOID', 
    'if': 'IF', 'else': 'ELSE', 'while': 'WHILE', 'Read': 'READ', 'Write': 'WRITE', 
    'true': 'TRUE', 'false': 'FALSE', 'return': 'RETURN', 'and': 'AND', 'not': 'NOT', 'or': 'OR'
}

class Token:
    def __init__(self, tipo, valor, linea, col_inicio, col_fin):
        self.tipo = tipo
        self.valor = valor 
        self.linea = linea
        self.col_inicio = col_inicio
        self.col_fin = col_fin

    def __repr__(self):
        return f"<{self.tipo}, {self.valor}, {self.linea}, {self.col_inicio}, {self.col_fin}>"
    
class MiniLangLexer:
    def __init__(self, fuente=None):
        self.fuente = fuente 
        self.pos = 0 
        self.linea_actual = 1 
        self.columna_actual = 1 
        self.tokens = [] 
        self.errores = [] 
        self.pila_indentacion = [0] 
        self.limite_indentacion = 5
        self.indice_token_actual = 0
    
    def convertir_LexToken(self, t): 
        tok = lex.LexToken()
        tok.type = t.tipo
        tok.value = t.valor
        tok.lineno = t.linea
        tok.lexpos = t.col_inicio
        return tok

    def token(self): 
        while self.indice_token_actual < len(self.tokens): 
            t = self.tokens[self.indice_token_actual]
            self.indice_token_actual += 1

            if t.tipo in ('NEWLINE', 'INDENT', 'DEDENT'): 
                continue

            if t.tipo == 'EOF':
                return None

            return self.convertir_LexToken(t)
        return None

    def input(self, fuente): 
        self.fuente = fuente 
        self.pos = 0 
        self.linea_actual = 1 
        self.columna_actual = 1 
        self.tokens = [] 
        self.errores_lexicos = [] 
        self.pila_indentacion = [0] 
        self.indice_token_actual = 0
    
        self._tokenizar_todo()

    def reportar_error(self, mensaje):
        err = f"line {self.linea_actual}, col {self.columna_actual}: ERROR LEXICO: {mensaje}"
        self.errores.append(err)
    
    def _tokenizar_todo(self):
        lineas = self.fuente.splitlines(keepends=True)
        
        for num_linea, contenido in enumerate(lineas, 1):
            self.linea_actual = num_linea
            self.columna_actual = 1
            self.pos = 0 
            
            # Condición original limpia
            if not contenido.strip() or contenido.strip().startswith('#'):
                continue

            espacios = 0
            idx = 0
            while idx < len(contenido) and contenido[idx] in ' \t':
                if contenido[idx] == ' ': espacios += 1
                elif contenido[idx] == '\t': espacios += 4 
                idx += 1
            
            actual_indent = espacios
            if actual_indent > self.pila_indentacion[-1]:
                if len(self.pila_indentacion) > self.limite_indentacion:
                    self.reportar_error("se excede limite de indentacion")
                self.pila_indentacion.append(actual_indent)
                self.tokens.append(Token('INDENT', '', self.linea_actual, 1, actual_indent))
            else:
                while actual_indent < self.pila_indentacion[-1]:
                    self.pila_indentacion.pop()
                    self.tokens.append(Token('DEDENT', '', self.linea_actual, 1, actual_indent))
                if actual_indent != self.pila_indentacion[-1]:
                    self.reportar_error("indent invalido")

            self.pos = idx 
            self.columna_actual = idx + 1
            
            while self.pos < len(contenido):
                char = contenido[self.pos]
                proximo = contenido[self.pos + 1] if self.pos + 1 < len(contenido) else ""

                if char.isspace() and char != '\n':
                    self.avanzar()
                    continue

                if char == '#': 
                    break

                if char == '\n':
                    self.tokens.append(Token('NEWLINE', '\\n', self.linea_actual, self.columna_actual, self.columna_actual))
                    self.avanzar()
                    continue

                if char == '=' and proximo == '=':
                    self.agregar_token('IG', '==', 2)
                    continue
                if char == '!' and proximo == '=':
                    self.agregar_token('NOIG', '!=', 2)
                    continue
                if char == '>' and proximo == '=':
                    self.agregar_token('MAYOQ', '>=', 2)
                    continue
                if char == '<' and proximo == '=':
                    self.agregar_token('MENOQ', '<=', 2)
                    continue

                simples = {
                    '+': 'MAS', '-': 'MENOS', '*': 'MULT', '/': 'DIV', '(': 'APAREN', ')': 'CPAREN', '{': 'ALLAVE', '}': 'CLLAVE', ';': 'PUNTOCOMA', ',': 'COMA', '=': 'IGUAL', '>': 'MAYQ', '<': 'MENQ'
                }

                if char in simples:
                    self.agregar_token(simples[char], char)
                    continue

                if char == '"':
                    self.manejar_string(contenido)
                    continue

                if char.isdigit():
                    self.manejar_numero(contenido)
                    continue

                if char.isalpha() or char == '_':
                    self.manejar_id(contenido)
                    continue

                self.reportar_error(f"carácter inesperado '{char}'")
                self.avanzar()

        while len(self.pila_indentacion) > 1:
            self.pila_indentacion.pop()
            self.tokens.append(Token('DEDENT', '', self.linea_actual, 1, 1))

        self.tokens.append(Token('EOF', 'EOF', self.linea_actual, self.columna_actual, self.columna_actual))

    def avanzar(self, n=1):
        self.pos += n
        self.columna_actual += n

    def agregar_token(self, tipo, valor, longitud=1):
        self.tokens.append(Token(tipo, valor, self.linea_actual, self.columna_actual, self.columna_actual + longitud - 1))
        self.avanzar(longitud)

    def manejar_string(self, contenido):
        inicio_col = self.columna_actual
        lexema = char_inicial = contenido[self.pos] 
        self.avanzar()
        while self.pos < len(contenido) and contenido[self.pos] not in ('"', '\n'):
            lexema += contenido[self.pos]
            self.avanzar()
        
        if self.pos < len(contenido) and contenido[self.pos] == '"':
            lexema += '"' 
            self.tokens.append(Token('STRING_LINE', lexema, self.linea_actual, inicio_col, self.columna_actual))
            self.avanzar()
        else:
            self.reportar_error("cadena sin cerrar")

    def manejar_numero(self, contenido):
        inicio_col = self.columna_actual
        lexema = ""
        es_float = False
        while self.pos < len(contenido) and (contenido[self.pos].isdigit() or contenido[self.pos] == '.'):
            if contenido[self.pos] == '.':
                if es_float: break 
                es_float = True
            lexema += contenido[self.pos]
            self.avanzar()
        
        tipo = 'NUM_FLOAT' if es_float else 'NUM_INT'
        self.tokens.append(Token(tipo, lexema, self.linea_actual, inicio_col, self.columna_actual - 1))

    def manejar_id(self, contenido):
        inicio_col = self.columna_actual
        lexema = ""
        while self.pos < len(contenido) and (contenido[self.pos].isalnum() or contenido[self.pos] == '_'):
            lexema += contenido[self.pos]
            self.avanzar()
        
        if len(lexema) > 31:
            self.reportar_error(f"identificador invalido: {lexema[:31]}")
            lexema = lexema[:31]

        tipo = RESERVADAS.get(lexema, 'ID')
        self.tokens.append(Token(tipo, lexema, self.linea_actual, inicio_col, self.columna_actual - 1))
