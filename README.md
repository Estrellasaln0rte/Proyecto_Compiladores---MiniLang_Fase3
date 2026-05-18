# PROYECTO, FASE 3
*Analizador Léxico, Sintáctico y Semántico - MiniLang*

## Funcionamiento 
En esta fase, el programa extiende el compilador desarrollado en las fases anteriores incorporando un analizador semántico que opera sobre el árbol de sintaxis abstracta (AST), generado por el módulo de Análisis Sintáctico. 

El flujo completo incluye: 
1. Análisis Léxico (MiniLangLexer) 
2. Análisis Sintáctico (MiniLangParser)
3. Análisis Semántico (AnalizadorSemantico)

El objetivo principal de esta fase es garantizar que el programa tenga sentido semántico correcto, a la vez que se ejecutan las instrucciones declaradas en el código fuente.

## Relación modular Lexer + Parser + Semántico
El sistema sigue un modelo secuencial, divido en módulos con responsabilidades únicas y específicas:
- MiniLangLexer (Productor): Lee caracteres directamente y los agrupa en tokens válidos sin entender de lógica de programación.
- MiniLangParser (Consumidor): Depende totalmente del Lexer. Solicita tokens uno por uno mediante la función interna de PLY y verifica si el orden de estos tokens forma estructuras válidas, mientras construye un AST (Árbol de Sintaxis Abstracta). 
- AnalizadorSemantico (Validador): Recorre el AST generado en el Parser, validando reglas establecidas (validación de tipos, declaraciones, uso de identificadores y coherencia lógica) para el lenguaje MiniLang. 

## Analizador Semántico 
El analizador semántico es el módulo encargado de verificar que el programa tenga sentido lógico y coherente. Se implementa como un recorrido del AST guiado por reglas semánticas, apoyado por una tabla de símbolos con manejo de ámbitos.

## Uso de AST 
El Árbol de Sintaxis Abstracta (AST) es la estructura central sobre la cual opera el analizador semántico. A diferencia del árbol sintáctico completo, el AST elimina detalles innecesarios (como paréntesis o tokens intermedios) y conserva únicamente la información relevante para el significado del programa.

El AST se construye durante el análisis sintáctico y se representa mediante tuplas, donde: 
- El primer elemento indica el tipo de nodo
- Los siguientes representan sus componentes, dependiendo el tipo de nodo
- Los últimos dos elementos representan la línea y columna donde se está ejecutando la sección de código que se analiza

Por ejemplo, para la declaración de una variable simple, la tupla seguiría el formato: 
```
(decl_var_simple, tipo, lexema, linea, columna)
```

### Recorrido de AST 
Para el recorrdo del AST, se implementó un método general: `visitar(nodo, alcanzable)`

Este metodo funciona dinámicamente, donde: 
1. Se identifica el tipo de nodo (nodo[0])
2. Se construye el nombre del método correspondiente (visitar_*)
3. Se ejecuta el método

En el método se definen los atributos semánticos pertenecientes a cada producción y se verifican las reglas semánticas: Comprobación de tipos, verificación de existencia de identificadores, y validación y ejecución de operaciones aritméticas y lógicas.

Asimismo, el recorrido sigue dos enfoques: 
1. **Descendente**: Para propagación de atributos heredados y manejo de ámbitos (entrada/salida de bloques).
2. **Ascendente**: Para propagación de atributos sintetizados y evaluación de expresiones. 

## Atributos Semánticos
En esta fase, el análisis está basado en una gramática dirigida por atributos, donde cada producción maneja información necesaria para validar tipos y evaluar expresiones. 

### Tipos de atributos
**Sintetizados**
 
Se calculan a partir de los hijos del nodo y se retornan ascendentemente. Se utilizan en producciones de expresión. 
- **tipo :** tipo de dato de la expresión o función. 
- **valor :** valor de dato (para evaluación de expresiones). 

**Heredados**

Se transmiten de nodos padres hacia nodos hijos, de manera descendente. Se utiliza en todo tipo de instrucción (producción).

- **alcanzable :** indica si un bloque de código puede ejecutarse. 

## Diseño de Gramática BNF
La gramática fue adaptada para manejar declaración de variables constantes ('const') y de funciones tipo 'void', así como el uso de funciones sin necesidad de asignación. 

```
<programa> ::= <lista_declaraciones> 
<lista_declaraciones> ::= <declaracion> <lista_declaraciones> | ε
<declaracion> ::= <declaracion_variable_funcion> | <sentencia>
<declaracion_variable_funcion> ::= <tipo> ID PUNTOCOMA 
                                   | <tipo> ID IGUAL <expresion> PUNTOCOMA 
                                   | CONST tipo ID PUNTOCOMA
                                   | CONST tipo ID IGUAL expresion PUNTOCOMA
                                   | <tipo> ID APAREN <parametros> CPAREN <bloque>
<tipo> ::= INT | FLOAT | STRING | BOOL | VOID
<parametros> ::= <lista_parametros> | ε
<lista_parametros> ::= <tipo> ID | <tipo> ID COMA <lista_parametros>
<bloque> ::= ALLAVE <lista_declaraciones> CLLAVE
<sentencia> ::= <asignacion> 
                | <if_statement> 
                | <while_statement> 
                | <read_statement> 
                | <write_statement> 
                | <return_statement> 
                | <llamada_funcion_sentencia> 
                | <bloque>
<llamada_funcion_sentencia> ::= ID APAREN <argumentos> CPAREN PUNTOCOMA
<asignacion> ::= ID IGUAL <expresion> PUNTOCOMA
<if_statement> ::= IF APAREN <condicion> CPAREN <sentencia> 
                   | IF APAREN <condicion> CPAREN <sentencia> <else_statement>
<else_statement> ::= ELSE <sentencia>
<while_statement> ::= WHILE APAREN <condicion> CPAREN <sentencia>
<read_statement> ::= READ APAREN ID CPAREN PUNTOCOMA | READ APAREN CPAREN PUNTOCOMA
<write_statement> ::= WRITE APAREN <expresion> CPAREN PUNTOCOMA
<return_statement> ::= RETURN <expresion> PUNTOCOMA
<expresion> ::= <termino> <expresion_prima>
<expresion_prima> ::= MAS <termino> <expresion_prima> | MENOS <termino> <expresion_prima> | ε
<termino> ::= <factor> <termino_prima>
<termino_prima> ::= MULT <factor> <termino_prima> | DIV <factor> <termino_prima> | ε
<factor> ::= ID <factor_prima> | APAREN <expresion> CPAREN | NUM_INT | NUM_FLOAT 
             | STRING_LINE | TRUE | FALSE
<factor_prima> ::= APAREN <argumentos> CPAREN | ε
<argumentos> ::= <lista_argumentos> | ε
<lista_argumentos> ::= <expresion> | <expresion> COMA <lista_argumentos>
<condicion> ::= <cond_or>
<cond_or> ::= <cond_and> <cond_or_prima>
<cond_or_prima> ::= OR <cond_and> <cond_or_prima> | ε
<cond_and> ::= <cond_not> <cond_and_prima>
<cond_and_prima> ::= AND <cond_not> <cond_and_prima> | ε
<cond_not> ::= NOT <cond_not> | <cond_rel>
<cond_rel> ::= <expresion> <operador_relacional> <expresion> | TRUE | FALSE | ID
<operador_relacional> ::= MAYQ | MENQ | MAYOQ | MENOQ | IG | NOIG
```

## Tabla de Símbolos y Manejo de Ámbitos
Es la encargada de almacenar y gestionar toda la información relevante sobre los identificadores del programa (variables, constantes, funciones y parámetros). 

Cada simbolo ingresado tiene la siguiente estructura: 

|Nombre| Tipo |Valor|Rol|Línea|Columna|Ámbito|
|---|---|---|---|---|---|---|
|lexema| tipo de dato |(si aplica)|variable, constante, funcion o parametro |número|número|número|

La tabla de símbolos se implementa mediante una pila de ámbitos por medio de una lista de diccionarios.
- `ambitos = [{}]`:
Donde cada elemento representa un ambito de forma numérica aumentando ascendentemente, empezando desde 0 como ámbito global. En cada elemento se ingresan los símbolos propios de ese ámbito. 

Asimismo, se implementó una tabla histórica (`tabla_historica`) que almacena todos los símbolos definidos, independientemente de su ámbito. 

### Funciones para implementación de Tabla de Símbolos

- **Inserción**

    Se utiliza: `definir(nombre, tipo, valor, rol, linea, col)`

    Se implementa en declaraciones. Se obtiene el ámbito actual y verifica que el simbolo a insertar no exista dentro del mismo, insertandolo en la pila de ámbitos y la tabla histórica. 

- **Búsqueda**

    Se utiliza: `buscar(nombre)` 

    Se implementa en declaraciones, asignaciones y evaluaciones. Se recorre la pila de ámbitos de abajo hacia arriba (LIFO), empezando por el ámbito local, hacia el global. 

- **Actualización de Valores**

    Se utliza: `actualizar(nombre, valor)` 

    Se utiliza cuando se realiza una asignación. Se busca el símbolo siguiendo la lógica de búsqueda y se modifica su valor. 

- **Manejo de Ámbitos**

    Se realiza por medio de dos funciones: 
    - `entrar_ambito()`
        
        Se ejecuta en bloques, funciones y estructuras de control. 
    - `salir_ambito()`

        Elimina el ámbito actual, descartando todas sus variables locales. 
    
    Este manejo permite que variables declaradas dentro de un ámbito no sean accesibles fuera de él. 


## Estrategia de Comprobación de Tipos
El sistema realiza comprobación de tipos en: 
- **Asignaciones:** Verificación de compatibilidad entre variable y expresión. 
- **Expresiones:** Reglas de operación entre tipos. 
- **Funciones:** Cantidad y tipo de parámetros que acepta. 
- **Variables:** Verificación previa a declaración. 

## Manejo de errores
Con la integración de todas las fases, el compilador maneja y filtra los errores sin provocar la terminación abrupta (aborto) del programa, evaluando todo el archivo fuente.

### Errores Léxicos 
Si se detecta un carácter no reconocido, se registra en formato ERROR LEXICO, se avanza el puntero y se continúa tokenizando. El parser nunca recibe caracteres inválidos crudos.

### Errores Sintácticos 
Cuando el autómata LALR(1) recibe un token (Lookahead) para el cual no tiene una acción válida definida en su tabla de estados, se llama la función `p_error(p)`
- Registro: Se captura la línea, columna y token inesperado, almacenando un mensaje descriptivo en errores_sintacticos. 
- Recuperación: PLY descarta tokens o ajusta la pila hasta encontrar un punto válido, permitiendo continuar el análisis.
- Validación de Fin de Archivo: Si el error ocurre por un token nulo, se reporta como “EOF inesperado”, indicando posibles bloques no cerrados.

### Errores Semánticos 
Se generan durante el recorrido del AST cuando una construcción, aunque sintácticamente válida, viola las reglas del lenguaje. Se hace por medio de dos funciones: `reportar_error()` y `reportar_warning()`

- Registro: Se pueden registar errores (críticos para el programa) y advertencias (problemas lógicos). Cada mensaje incluye línea, columna y descripción del error, siguiendo el formato:  
    ```
    línea x, columna y: **ERROR** descripción
    línea x, columna y: ADVERTENCIA descripción
    ```

- Tipos de errores semánticos:
    - Variables no declaradas: Cuando un identificador es utilizado sin haber sido previamente definido en ningún ámbito accesible.
        ```
        Variable 'x' no declarada
        ```
    - Redeclaración de variables: Cuando se intenta declarar una variable, constante o función con un nombre ya existente en el ámbito actual.
        ```
        Variable 'x' ya declarada en este ámbito
        ```
    - Incompatibilidad de tipos: Cuando se intenta operar o asignar valores entre tipos incompatibles.
        ```
        No se puede operar el tipo 'int' con 'string'
        No se puede asignar el tipo 'float' a la variable 'x'
        ```
    - Reasignación de constantes: Se impide modificar el valor de una constante después de su inicialización.
        ```
        No se puede reasignar un valor a la constante 'PI'
        ```
    - Errores en llamadas a funciones: Incluye función no declarada, número incorrecto de argumentos y tipo de argumentos incompatibles.
        ```
        Función 'f' no declarada
        La función 'f' espera 2 argumentos, recibió 1
        Se esperaba 'int', pero se recibió 'string'
        ```
    - Operaciones inválidas: Cuando se utilizan operadores con tipos no soportados.
        ```
        No se puede operar el tipo 'bool' y 'int' con el operador '+'
        ```
- Advertencias: El sistema detecta situaciones que, aunque no invaliden el programa, pueden indicar problemas lógicos. 
    - Código inalcanzable: Se detecta mediante el atributo alcanzable, que se propaga durante el recorrido del AST.
        ```
        Variable 'x' inicializada en código inalcanzable
        Asignación a variable 'x' en código inalcanzable
        ```
        Estas advertencias permiten identificar secciones del programa que nunca serán ejecutadas.
- Recuperación: Se implementa una estrategia de recuperación pasiva, basado en no lanzar excepciones que detengan el programa, retornar valores nulos en evaluaciones inválidas y continuar el recorrido AST después de detectar y almacenar errores. 

## Mantenimiento 
El diseño del compilador en fases independientes (léxica, sintáctica y semántica) permite que el sistema sea modular y fácil de mantener. Cada componente cumple una función específica, lo que facilita realizar cambios sin afectar el resto del sistema.

Se permite la incorporación de nuevas características del lenguaje, como: 
- Nuevos tipos de datos
- Nuevas estructuras de control
- Nuevas reglas semánticas

Esto se logra fácilmente: 
- Agregando tokens en el lexer (MiniLangLexer)
- Definiendo nuevas producciones en el parser (MiniLangParser)
- Implementando el método visitar_ correspondiente en el Analizador Semántico

Asimismo, el manejo de errores centralizado en estructuras dedicadas (errores lexicos, errores sintácticos, errores semánticos y advertencias) permite el ajuste del formato de salida y mensajes sin alterar lógica principal. 
