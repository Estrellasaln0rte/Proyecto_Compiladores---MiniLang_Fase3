import ply.lex as lex

# tokens para uso en gramatica
tokens = (
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

#palabras reservadas mapeo de las cadenas exactas al tipo de token esperado
RESERVADAS = {
    'int': 'INT', 'float': 'FLOAT', 'string': 'STRING', 'bool': 'BOOL', 'if': 'IF', 'else': 'ELSE', 'while': 'WHILE', 'Read': 'READ', 'Write': 'WRITE', 'true': 'TRUE', 'false': 'FALSE', 'return': 'RETURN', 'and': 'AND', 'not': 'NOT', 'or': 'OR'
}

#def tokens
class Token:
    def __init__(self, tipo, valor, linea, col_inicio, col_fin):
        self.tipo = tipo #id token
        self.valor = valor #lexema
        self.linea = linea
        self.col_inicio = col_inicio
        self.col_fin = col_fin

    def __repr__(self):
        return f"<{self.tipo}, {self.valor}, {self.linea}, {self.col_inicio}, {self.col_fin}>"
    
class MiniLangLexer:
#scanner
    #se recorre caracter por caracter
    def __init__(self, fuente=None):
        self.fuente = fuente #codigo fuente, entrada, a string
        self.pos = 0 #indice global del caracter actual
        self.linea_actual = 1 #contador
        self.columna_actual = 1 #contador
        self.tokens = [] #lista de tokens validos
        self.errores = [] #lista de err lexicos 
        self.pila_indentacion = [0] #pila de estado
        self.limite_indentacion = 5
        self.indice_token_actual = 0
    
    # conversión de Token a formato LexToken para uso con ply.yacc
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

            # ignorar tokens que no se usarán para análisis sintáctico
            if t.tipo in ('NEWLINE', 'INDENT', 'DEDENT'): 
                continue

            # ignorar EOF
            if t.tipo == 'EOF':
                return None
                
            return self.convertir_LexToken(t)
        return None

    def input(self, fuente): 
        self.fuente = fuente #codigo fuente, entrada, a string
        self.pos = 0 #indice global del caracter actual
        self.linea_actual = 1 #contador
        self.columna_actual = 1 #contador
        self.tokens = [] #lista de tokens validos
        self.errores_lexicos = [] #lista de err lexicos 
        self.pila_indentacion = [0] #pila de estado
        self.indice_token_actual = 0
    
        self._tokenizar_todo()

    def reportar_error(self, mensaje):
        #no lanza excepciones solo guarda el error para que la ejecucion continue
        err = f"line {self.linea_actual}, col {self.columna_actual}: ERROR LEXICO: {mensaje}"
        self.errores.append(err)
    
    def _tokenizar_todo(self):
        #separa el texto por líneas manteniendo el salto de línea al final
        lineas = self.fuente.splitlines(keepends=True)
        
        for num_linea, contenido in enumerate(lineas, 1):
            self.linea_actual = num_linea
            self.columna_actual = 1
            self.pos = 0 #reiniciamos la posicion del puntero de lectura de la linea
            
            if not contenido.strip() or contenido.strip().startswith('#'):
                # ignorar lineas vacias o comentarios
                continue

            #calculo de indent 
            espacios = 0
            idx = 0
            #cont espacios antes de encontrar caracter
            while idx < len(contenido) and contenido[idx] in ' \t':
                if contenido[idx] == ' ': espacios += 1
                elif contenido[idx] == '\t': espacios += 4 #normaliza tab a 4 espacios
                idx += 1
            
            #evaluar cont_indent con el tope de pila
            actual_indent = espacios
            if actual_indent > self.pila_indentacion[-1]:
                #si los espacios contados es mayor a la sima de pila emitir token INDENT
                if len(self.pila_indentacion) > self.limite_indentacion:
                    self.reportar_error("se excede limite de indentacion")
                self.pila_indentacion.append(actual_indent)
                self.tokens.append(Token('INDENT', '', self.linea_actual, 1, actual_indent))
            else:
                #si los espacios contados son menor a la sima de pila extraer de pila emitiendo token DEDENT hasta encontrar coincidencia
                while actual_indent < self.pila_indentacion[-1]:
                    self.pila_indentacion.pop()
                    self.tokens.append(Token('DEDENT', '', self.linea_actual, 1, actual_indent))
                #si no se encuentra coincidencia error de indentacion 
                if actual_indent != self.pila_indentacion[-1]:
                    self.reportar_error("indent invalido")

            # manejar resto de la linea
            self.pos = idx #mov indice global hasta la  ultima indent
            self.columna_actual = idx + 1
            
            #se lee caracter por caracter consumeindo la linea
            while self.pos < len(contenido):
                char = contenido[self.pos]

                #si no son inciio de linea ignorar espacios en blanco entre lexemas
                if char.isspace() and char != '\n':
                    self.avanzar()
                    continue

                #ignorar comentarios intermedios
                if char == '#': # ignorar hasta fin de linea
                    break

                #emitir token NEWLINE si salto de linea 
                if char == '\n':
                    self.tokens.append(Token('NEWLINE', '\\n', self.linea_actual, self.columna_actual, self.columna_actual))
                    self.avanzar()
                    continue

                # operadores dobles usando lookahead
                proximo = contenido[self.pos + 1] if self.pos + 1 < len(contenido) else ""
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

                # operadores y puntuacion
                simples = {
                    '+': 'MAS', '-': 'MENOS', '*': 'MULT', '/': 'DIV', '(': 'APAREN', ')': 'CPAREN', '{': 'ALLAVE', '}': 'CLLAVE', ';': 'PUNTOCOMA', ',': 'COMA', '=': 'IGUAL', '>': 'MAYQ', '<': 'MENQ'
                }

                if char in simples:
                    self.agregar_token(simples[char], char)
                    continue

                #ver literales cadena string
                if char == '"':
                    self.manejar_string(contenido)
                    continue

                #ver literales numericas int float
                if char.isdigit():
                    self.manejar_numero(contenido)
                    continue

                #ver id y reservadas
                if char.isalpha() or char == '_':
                    self.manejar_id(contenido)
                    continue

                #si caracter fuera del lenguaje error lexico
                self.reportar_error(f"carácter inesperado '{char}'")
                #forzar continuacion del analisis
                self.avanzar()

        #limpiar DEDENTS pendientes al final del archivo cerrando los INDENT pedientes en pila
        while len(self.pila_indentacion) > 1:
            self.pila_indentacion.pop()
            self.tokens.append(Token('DEDENT', '', self.linea_actual, 1, 1))

        #token de fin de archivo para parser
        self.tokens.append(Token('EOF', 'EOF', self.linea_actual, self.columna_actual, self.columna_actual))

    def avanzar(self, n=1):
        #mov fila y columan
        self.pos += n
        self.columna_actual += n

    def agregar_token(self, tipo, valor, longitud=1):
        #registrar token avanzando puntero
        self.tokens.append(Token(tipo, valor, self.linea_actual, self.columna_actual, self.columna_actual + longitud - 1))
        self.avanzar(longitud)

    def manejar_string(self, contenido):
        #lee caracteres hasta encontrar las comillas de cierre o un salto de linea
        inicio_col = self.columna_actual
        lexema = char_inicial = contenido[self.pos] #guardar primera "
        self.avanzar()
        while self.pos < len(contenido) and contenido[self.pos] not in ('"', '\n'):
            lexema += contenido[self.pos]
            self.avanzar()
        
        if self.pos < len(contenido) and contenido[self.pos] == '"':
            lexema += '"' #cierra cadena
            self.tokens.append(Token('STRING_LINE', lexema, self.linea_actual, inicio_col, self.columna_actual))
            self.avanzar()
        else:
            #si no se encuentra la segunda " o se encuentra un salto de lnea antes se emite error lexico
            self.reportar_error("cadena sin cerrar")

    def manejar_numero(self, contenido):
        #acepta digitos considerando un punto como decimal
        inicio_col = self.columna_actual
        lexema = ""
        es_float = False
        while self.pos < len(contenido) and (contenido[self.pos].isdigit() or contenido[self.pos] == '.'):
            if contenido[self.pos] == '.':
                if es_float: break #si ya habia punto el segundo es invalido fin de token
                es_float = True
            lexema += contenido[self.pos]
            self.avanzar()
        
        tipo = 'NUM_FLOAT' if es_float else 'NUM_INT'
        self.tokens.append(Token(tipo, lexema, self.linea_actual, inicio_col, self.columna_actual - 1))

    def manejar_id(self, contenido):
        #lee letras numeros y guiones bajo
        inicio_col = self.columna_actual
        lexema = ""
        while self.pos < len(contenido) and (contenido[self.pos].isalnum() or contenido[self.pos] == '_'):
            lexema += contenido[self.pos]
            self.avanzar()
        
        #ver id>31 o error de tamaño
        if len(lexema) > 31:
            self.reportar_error(f"identificador invalido: {lexema[:31]}")
            lexema = lexema[:31]

        #si no es reservada es id
        tipo = RESERVADAS.get(lexema, 'ID')
        self.tokens.append(Token(tipo, lexema, self.linea_actual, inicio_col, self.columna_actual - 1))
