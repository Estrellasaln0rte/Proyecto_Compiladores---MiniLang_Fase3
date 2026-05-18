# manejo de memoria y ambitos
class TablaSimbolos:
    def __init__(self):
        # pila para manejar bloques global locales
        self.ambitos = [{}] 
        self.tabla_historica = [] 

    def entrar_ambito(self):
        self.ambitos.append({})

    def salir_ambito(self):
        self.ambitos.pop()

    def definir(self, nombre, tipo_dato, valor, rol, linea, col):
        ambito_actual = self.ambitos[-1]
        if nombre in ambito_actual:
            return False 
        
        simbolo = {
            'nombre': nombre, 'tipo': tipo_dato, 'valor': valor,
            'rol': rol, 'linea': linea, 'columna': col, 'ambito': len(self.ambitos) - 1
        }
        ambito_actual[nombre] = simbolo
        self.tabla_historica.append(simbolo)
        return True

    def buscar(self, nombre):
        # busqueda de local a global de abajo hacia arriba
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def actualizar(self, nombre, valor):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                ambito[nombre]['valor'] = valor
                return True
        return False

# recorrido y validacion
class AnalizadorSemantico:
    def __init__(self):
        self.ts = TablaSimbolos()
        self.errores = []
        self.warnings = []
        self.linea_actual = 0  
        self.col_actual = 0    

    def reportar_error(self, linea, col, mensaje):
        self.errores.append(f"línea {linea}, columna {col}: **ERROR** {mensaje}")

    def reportar_warning(self, linea, col, mensaje):
        self.warnings.append(f"línea {linea}, columna {col}: ADVERTENCIA {mensaje}")

    # enviar nodos AST
    def visitar(self, nodo, alcanzable=True):
        if not nodo or not isinstance(nodo, tuple):
            return None, None
        
        nombre_metodo = f'visitar_{nodo[0]}'
        metodo = getattr(self, nombre_metodo, self.visitar_generico)
        return metodo(nodo, alcanzable)

    def visitar_generico(self, nodo, alcanzable): pass

    def visitar_programa(self, nodo, alcanzable):
        for decl in nodo[1]:
            self.visitar(decl, alcanzable)

    # variables y constantes
    def visitar_decl_var_simple(self, nodo, alcanzable):
        _, tipo, nombre_id, linea, col = nodo
        if not self.ts.definir(nombre_id, tipo, None, 'variable', linea, col):
            self.reportar_error(linea, col, f"Variable '{nombre_id}' ya declarada en este ámbito")
        return None, None

    def visitar_decl_var_comp(self, nodo, alcanzable):
        _, tipo_dato, nombre_id, expresion, linea, col = nodo
        self.linea_actual = linea 
        self.col_actual = col 
        
        # inalcanzable encontrado estaticamente
        if not alcanzable:
            self.reportar_warning(linea, col, f"Variable '{nombre_id}' inicializada en código inalcanzable")
        
        valor, tipo_expr = self.visitar(expresion, alcanzable)

        # validacion de tipos y coerción
        if tipo_expr:
            if tipo_dato == 'float' and tipo_expr == 'int':
                tipo_expr = 'float' 
                if valor is not None: valor = float(valor)
            elif tipo_dato != tipo_expr:
                self.reportar_error(linea, col, f"No se puede operar el tipo '{tipo_dato}' con '{tipo_expr}'")
                valor = None

        if not self.ts.definir(nombre_id, tipo_dato, valor, 'variable', linea, col):
            self.reportar_error(linea, col, f"Variable '{nombre_id}' ya declarada en este ámbito")
        return None, None

    def visitar_decl_const_simple(self, nodo, alcanzable):
        _, tipo_dato, nombre_id, linea, col = nodo
        if not self.ts.definir(nombre_id, tipo_dato, None, 'constante', linea, col):
            self.reportar_error(linea, col, f"Constante '{nombre_id}' ya declarada")

    def visitar_decl_const_comp(self, nodo, alcanzable):
        _, tipo_dato, nombre_id, expresion, linea, col = nodo
        self.linea_actual = linea 
        self.col_actual = col 
        
        if not alcanzable:
            self.reportar_warning(linea, col, f"Constante '{nombre_id}' inicializada en código inalcanzable")
        
        valor, tipo_expr = self.visitar(expresion, alcanzable)

        if tipo_expr:
            if tipo_dato == 'float' and tipo_expr == 'int':
                tipo_expr = 'float' 
                if valor is not None: valor = float(valor)
            elif tipo_dato != tipo_expr:
                self.reportar_error(linea, col, f"No se puede operar el tipo '{tipo_dato}' con '{tipo_expr}'")
                valor = None

        if not self.ts.definir(nombre_id, tipo_dato, valor, 'constante', linea, col):
            self.reportar_error(linea, col, f"Constante '{nombre_id}' ya declarada")
        return None, None

    def visitar_asignacion(self, nodo, alcanzable):
        _, nombre_id, expresion, linea, col = nodo
        self.linea_actual = linea 
        self.col_actual = col 
        
        simbolo = self.ts.buscar(nombre_id)
        if not simbolo:
            self.reportar_error(linea, col, f"Variable '{nombre_id}' no declarada")
            return None, None

        # restricciones para constantes
        if simbolo['rol'] == 'constante' and simbolo['valor'] is not None:
            self.reportar_error(linea, col, f"No se puede reasignar un valor a la constante '{nombre_id}'")
            return None, None

        if not alcanzable:
            self.reportar_warning(linea, col, f"Asignación a variable '{nombre_id}' en código inalcanzable")

        valor, tipo_expr = self.visitar(expresion, alcanzable)

        if tipo_expr:
            if simbolo['tipo'] == 'float' and tipo_expr == 'int':
                tipo_expr = 'float'
                if valor is not None: valor = float(valor)
            elif simbolo['tipo'] != tipo_expr:
                self.reportar_error(linea, col, f"No se puede asignar el tipo '{tipo_expr}' a la variable '{nombre_id}'")
                return None, None

        self.ts.actualizar(nombre_id, valor) 
        return None, None

    # control de flujo
    def visitar_if(self, nodo, alcanzable):
        condicion, sentencia_true = nodo[1], nodo[2]
        else_statement = nodo[3] if len(nodo) > 5 else None

        valor_cond, _ = self.visitar_condicion(condicion, alcanzable)
        alcanzable_true = alcanzable and (valor_cond is not False)
        alcanzable_false = alcanzable and (valor_cond is not True)

        self.ts.entrar_ambito()
        self.visitar(sentencia_true, alcanzable_true)
        self.ts.salir_ambito()

        if else_statement:
            self.ts.entrar_ambito()
            self.visitar(else_statement, alcanzable_false)
            self.ts.salir_ambito()
        return None, None

    def visitar_bloque(self, nodo, alcanzable):
        self.ts.entrar_ambito()
        for decl in nodo[1]:
            self.visitar(decl, alcanzable)
        self.ts.salir_ambito()
        return None, None

    # funciones
    def visitar_decl_var_func(self, nodo, alcanzable):
        _, tipo_retorno, nombre_id, parametros, bloque, linea, col = nodo
        
        if not self.ts.definir(nombre_id, tipo_retorno, None, 'funcion', linea, col):
            self.reportar_error(linea, col, f"Función '{nombre_id}' ya declarada")
            return None, None
            
        simbolo_func = self.ts.buscar(nombre_id)
        tipos_esperados = [p[0] for p in parametros] if parametros else []
        simbolo_func['parametros'] = tipos_esperados 

    def visitar_call_stmt(self, nodo, alcanzable):
        _, nombre_func, argumentos, linea, col = nodo
        self.linea_actual = linea 
        self.col_actual = col 
        
        if not alcanzable:
            self.reportar_warning(linea, col, f"Llamada a función '{nombre_func}' en código inalcanzable")
            
        simbolo = self.ts.buscar(nombre_func)
        if not simbolo or simbolo['rol'] != 'funcion':
            self.reportar_error(linea, col, f"Función '{nombre_func}' no declarada")
            return None, None
            
        params_esperados = simbolo.get('parametros', [])
        args_enviados = argumentos if argumentos else []
        
        # regla de cantidad
        if len(args_enviados) != len(params_esperados):
            self.reportar_error(linea, col, f"La función '{nombre_func}' espera {len(params_esperados)} argumentos, recibió {len(args_enviados)}")
            return None, None
            
        # regla de tipo
        for i, arg_expr in enumerate(args_enviados):
            _, tipo_arg = self.visitar(arg_expr, alcanzable)
            if tipo_arg != params_esperados[i]:
                self.reportar_error(linea, col, f"Un argumento para la función '{nombre_func}' es inválido. Se esperaba '{params_esperados[i]}', pero se recibió '{tipo_arg}'")
        return None, None

        # registro temporal de parametros en el ambito local de la funcion
        self.ts.entrar_ambito()
        if parametros:
            for tipo_p, nombre_p in parametros:
                self.ts.definir(nombre_p, tipo_p, None, 'parametro', linea, col)
        
        self.visitar(bloque, alcanzable)
        self.ts.salir_ambito()
        return None, None

    # evaluaciones matematicas y Constant Folding
    def visitar_expresion(self, nodo, alcanzable):
        _, termino, expresion_prima = nodo
        valor_izq, tipo_izq = self.visitar_termino(termino, alcanzable)

        if expresion_prima:
            for op, term in expresion_prima:
                valor_der, tipo_der = self.visitar_termino(term, alcanzable)
                
                # reglas de tipado suma resta
                if tipo_izq == 'int' and tipo_der == 'int': tipo_res = 'int'
                elif (tipo_izq == 'float' and tipo_der in ('int', 'float')) or (tipo_der == 'float' and tipo_izq in ('int', 'float')): tipo_res = 'float'
                elif tipo_izq == 'string' and tipo_der == 'string' and op == '+': tipo_res = 'string'
                else:
                    self.reportar_error(self.linea_actual, self.col_actual, f"No se puede operar el tipo '{tipo_izq}' y '{tipo_der}' con el operador '{op}'")
                    tipo_res = None 

                # realizacion literal de la operacion 
                if valor_izq is not None and valor_der is not None:
                    try:
                        if op == '+': valor_izq = valor_izq + valor_der
                        elif op == '-': valor_izq = valor_izq - valor_der
                    except: valor_izq = None
                else:
                    valor_izq = None
                tipo_izq = tipo_res

        return valor_izq, tipo_izq

    def visitar_termino(self, nodo, alcanzable):
        factor, termino_prima = nodo
        valor_izq, tipo_izq = self.visitar_factor(factor, alcanzable)

        if termino_prima:
            for op, fact in termino_prima:
                valor_der, tipo_der = self.visitar_factor(fact, alcanzable)
                
                # reglas tipado multiplicacion division
                if tipo_izq == 'int' and tipo_der == 'int':
                    tipo_res = 'float' if op == '/' else 'int'
                elif (tipo_izq == 'float' and tipo_der in ('int', 'float')) or (tipo_der == 'float' and tipo_izq in ('int', 'float')):
                    tipo_res = 'float'
                else:
                    self.reportar_error(self.linea_actual, self.col_actual, f"No se puede operar el tipo '{tipo_izq}' y '{tipo_der}' con el operador '{op}'")
                    tipo_res = None 

                if valor_izq is not None and valor_der is not None:
                    try:
                        if op == '*': valor_izq = valor_izq * valor_der
                        elif op == '/': valor_izq = valor_izq / valor_der if valor_der != 0 else None
                    except: valor_izq = None
                else:
                    valor_izq = None
                tipo_izq = tipo_res

        return valor_izq, tipo_izq

    def visitar_factor(self, nodo, alcanzable):
        if isinstance(nodo, tuple): 
            if nodo[0] == 'id': # busca su valor anterior
                nombre_id = nodo[1]
                linea, col = nodo[2], nodo[3]
                simbolo = self.ts.buscar(nombre_id)
                if not simbolo:
                    self.reportar_error(linea, col, f"Variable '{nombre_id}' no declarada")
                    return None, 'int' 
                return simbolo.get('valor'), simbolo.get('tipo')
                
            elif nodo[0] == 'call': # validacion de llamada a funcion
                nombre_func, argumentos = nodo[1], nodo[2]
                linea, col = nodo[3], nodo[4]
                
                simbolo = self.ts.buscar(nombre_func)
                if not simbolo or simbolo['rol'] != 'funcion':
                    self.reportar_error(linea, col, f"Función '{nombre_func}' no declarada")
                    return None, 'int'
                
                params_esperados = simbolo.get('parametros', [])
                args_enviados = argumentos if argumentos else []
                
                # regla de cantidad
                if len(args_enviados) != len(params_esperados):
                    self.reportar_error(linea, col, f"La función '{nombre_func}' espera {len(params_esperados)} argumentos, recibió {len(args_enviados)}")
                    return None, simbolo['tipo']
                
                # regla de tipo recorre los argumentos y los compara 1 a 1
                for i, arg_expr in enumerate(args_enviados):
                    _, tipo_arg = self.visitar(arg_expr, alcanzable)
                    if tipo_arg != params_esperados[i]:
                        self.reportar_error(linea, col, f"Un argumento para la función '{nombre_func}' es inválido. Se esperaba '{params_esperados[i]}', pero se recibió '{tipo_arg}'")
                
                return None, simbolo['tipo'] 
                
            elif nodo[0] == 'expresion':
                return self.visitar_expresion(nodo, alcanzable)
        else:
            # determinacion directa de literales
            val_str = str(nodo)
            
            # validación de Strings y null
            if val_str.startswith('"'): 
                return val_str.strip('"'), 'string'
            
            elif val_str.isdigit(): 
                return int(val_str), 'int'
            
            elif '.' in val_str:
                try: return float(val_str), 'float'
                except: pass
                
            elif val_str in ('true', 'false'): 
                return val_str == 'true', 'bool'
        
        return None, None

    def visitar_condicion(self, nodo, alcanzable):
        return None, 'bool'
