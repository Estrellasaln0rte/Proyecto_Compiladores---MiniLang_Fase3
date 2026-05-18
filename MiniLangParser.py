import ply.yacc as yacc
from MiniLangLexer import tokens

# precedencia de operaciones --> menor a mayor precedencia
precedence = (
    ('nonassoc', 'IFX'),
    ('nonassoc', 'ELSE'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('nonassoc', 'MENQ', 'MAYQ', 'MAYOQ', 'MENOQ', 'IG', 'NOIG'),
    ('left', 'MAS', 'MENOS'), 
    ('left', 'MULT', 'DIV')
)

errores_sintacticos = []

def p_error(p): 
    if p:
        errores_sintacticos.append(
            f"line {p.lineno}, col {p.lexpos}, token {p.type}, ERROR SINTÁCTICO: token inesperado {p.type}: '{p.value}'"
        )
    else:
        errores_sintacticos.append("EOF inesperado: ERROR SINTÁCTICO")

# definición de producciones BNF
# no se guardan simbolos para estructura '(', ')', '{', '}', '=', ';', ','
def p_programa(p): 
    'programa : lista_declaraciones'
    p[0] = ('programa', p[1])

def p_lista_declaraciones(p):
    '''lista_declaraciones : declaracion lista_declaraciones
                           | empty'''
        
    if len(p) == 3: 
        p[0] = [p[1]] + p[2]
    else: 
        p[0] = p[1]

def p_declaracion(p): 
    '''declaracion : declaracion_variable_funcion
                   | sentencia'''
    p[0] = p[1]

def p_declaracion_variable_funcion(p): 
    '''declaracion_variable_funcion : tipo ID PUNTOCOMA
                                    | tipo ID IGUAL expresion PUNTOCOMA
                                    | tipo ID APAREN parametros CPAREN bloque'''
    if len(p) == 4: 
        p[0] = ('decl_var_simple', p[1], p[2])

    elif len(p) == 6: 
        p[0] = ('decl_var_comp', p[1], p[2], p[4])
        
    elif len(p) == 7: 
        p[0] = ('decl_var_func', p[1], p[2], p[4], p[6])

def p_tipo(p): 
    '''tipo : INT
            | FLOAT
            | STRING 
            | BOOL'''
    p[0] = p[1]

def p_parametros(p): 
    '''parametros : lista_parametros 
                  | empty'''
    p[0] = p[1]

def p_lista_parametros(p): 
    '''lista_parametros : tipo ID
                        | tipo ID COMA lista_parametros'''
    if len(p) == 3: 
        p[0] = [(p[1], p[2])]
    elif len(p) == 5: 
        p[0] = [(p[1], p[2])] + p[4]

def p_bloque(p): 
    'bloque : ALLAVE lista_declaraciones CLLAVE'
    p[0] = ('bloque', p[2])

def p_sentencia(p): 
    '''sentencia : asignacion
                | if_statement
                | while_statement
                | read_statement
                | write_statement
                | return_statement
                | bloque'''
    p[0] = p[1]

def p_asignacion(p): 
    'asignacion : ID IGUAL expresion PUNTOCOMA'
    p[0] = ('asignacion', p[1], p[3])

# uso de IFX para asignar nivel de precedencia
def p_if_statement(p): 
    '''if_statement : IF APAREN condicion CPAREN sentencia %prec IFX
                    | IF APAREN condicion CPAREN sentencia else_statement'''
    if len(p) == 6: 
        p[0] = ('if', p[3], p[5])
    elif len(p) == 7:
        p[0] = ('if', p[3], p[5], p[6])

def p_else_statement(p): 
    'else_statement : ELSE sentencia'
    if len(p) == 3: 
        p[0] = ('else', p[2])
    elif len(p) == 2: 
        p[0] = p[1]
    
def p_while_statement(p): 
    'while_statement : WHILE APAREN condicion CPAREN sentencia'
    p[0] = ('while', p[3], p[5])
    
def p_read_statement(p): 
    '''read_statement : READ APAREN ID CPAREN PUNTOCOMA
                      | READ APAREN CPAREN PUNTOCOMA'''
    if len(p) == 6: 
        p[0] = ('read_id', p[3])
    elif len(p) == 5: 
        p[0] = ('read', p[1])

def p_write_statement(p): 
    'write_statement : WRITE APAREN expresion CPAREN PUNTOCOMA'
    p[0] = ('write', p[3])

def p_return_statement(p):     
    'return_statement : RETURN expresion PUNTOCOMA'
    p[0] = ('return', p[2])
    
def p_expresion(p): 
    'expresion : termino expresion_prima'
    p[0] = ('expresion', p[1], p[2])

def p_expresion_prima(p): 
    '''expresion_prima : MAS termino expresion_prima
                       | MENOS termino expresion_prima
                       | empty'''
    if len(p) == 4:
        p[0] = [(p[1], p[2])] + p[3]
    else: 
        p[0] = p[1]
    
def p_termino(p): 
    'termino : factor termino_prima'
    p[0] = (p[1], p[2])
    
def p_termino_prima(p): 
    '''termino_prima : MULT factor termino_prima
                     | DIV factor termino_prima
                     | empty'''
    if len(p) == 4:
        p[0] = [(p[1], p[2])] + p[3]
    else: 
        p[0] = p[1]
        
def p_factor(p):
    '''factor : ID factor_prima
              | APAREN expresion CPAREN
              | NUM_INT
              | NUM_FLOAT
              | STRING_LINE
              | TRUE
              | FALSE'''
    if len(p) == 3:
        if p[2] is None:
            p[0] = p[1]
        else:
            p[0] = ('call', p[1], p[2])
    elif len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = p[1]

def p_factor_prima(p): 
    '''factor_prima : APAREN argumentos CPAREN
                    | empty'''
    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = p[1]
    
def p_argumentos(p): 
    '''argumentos : lista_argumentos 
                  | empty'''
    p[0] = p[1]

def p_lista_argumentos(p): 
    '''lista_argumentos : expresion 
                        | expresion COMA lista_argumentos'''
    if len(p) == 2: 
        p[0] = [p[1]]
    elif len(p) == 4: 
        p[0] = [p[1]] + p[3]
    
def p_condicion(p): 
    'condicion : cond_or'
    p[0] = ('cond', p[1])

def p_cond_or(p): 
    'cond_or : cond_and cond_or_prima'
    p[0] = [p[1]] + p[2]

def p_cond_or_prima(p):
    '''cond_or_prima : OR cond_and cond_or_prima
                     | empty'''
    if len(p) == 4: 
        p[0] = [p[1], p[2]] + p[3]
    else: 
        p[0] = p[1]
    
def p_cond_and(p): 
    'cond_and : cond_not cond_and_prima'
    p[0] = [p[1]] + p[2]

def p_cond_and_prima(p):
    '''cond_and_prima : AND cond_not cond_and_prima
                      | empty'''
    if len(p) == 4: 
        p[0] = [p[1], p[2]] + p[3]
    else: 
        p[0] = p[1]

def p_cond_not(p): 
    '''cond_not : NOT cond_not
                | cond_rel'''
    if len(p) == 3: 
        p[0] = ('not', p[2])
    else: 
        p[0] = p[1]
    
def p_cond_rel(p): 
    '''cond_rel : expresion operador_relacional expresion
                | TRUE
                | FALSE
                | ID'''
    if len(p) == 4: 
        p[0] = (p[1], p[2], p[3])
    else: 
        p[0] = p[1]

def p_operador_relacional(p): 
    '''operador_relacional : MAYQ 
                           | MENQ 
                           | MAYOQ 
                           | MENOQ 
                           | IG 
                           | NOIG'''
    p[0] = p[1]

# producción vacía
def p_empty(p): 
    'empty :'
    p[0] = []

# creación de parser con ply.yacc
parser = yacc.yacc()
        
