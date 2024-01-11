from tkinter import filedialog, ttk, scrolledtext as st
import tkinter as tk
import re, os

def AbrirArchivo():
    global directorio
    #abrir el directorio para selecionar un archivo
    directorio = filedialog.askopenfilename(initialdir="C:", title="Abrir archivo",
    filetypes=(("Archivo", ".txt"),))

    if directorio != "":
        # Leer el archivo
        with open(directorio, "r") as f:
            contenido = f.read()
        # Mostrar contenido
        cajaCodigo.delete("1.0", tk.END)
        cajaCodigo.insert(tk.END, contenido)
        enumerarLineas(None)
        # Extraer el nombre del archivo
        nombre_archivo = os.path.basename(directorio)
        # Establecer el nombre del archivo como el título de la ventana
        ventana.title(nombre_archivo)

def Guardar():
    if directorio != "":
        contenido = cajaCodigo.get(1.0,"end-1c")
        archivo= open(directorio, "w+")
        archivo.write(contenido)
        archivo.close()
        
def GuardarComo():
    # Mostrar cuadro de diálogo
    archivo = filedialog.asksaveasfile(mode='w', defaultextension=".txt")
    if archivo is not None:
        # Obtener el contenido de la caja de texto
        contenido = cajaCodigo.get(1.0, "end-1c")
        # Escribir el contenido en el archivo
        archivo.write(contenido)
        archivo.close()

op = {"+", "-", "*", "/", "=", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "!", "&", "|", "^", "~", "<<", ">>", "++", "--",
    "+=", "-=", "*=", "/=", "%=", "<<=", ">>=", "&=", "^=", "|="}
pr = {"printf", "main", "auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else","enum",
    "extern", "float", "for", "goto", "if", "inline", "int", "long", "register", "restrict", "return", "short", "signed",
    "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while", "_Bool", "include"}
sep = {"(", ")", "[", "]", "{", "}", ",", ".", ";", ":", "?", "#", "##"}
lib = {"stdio.h", "stdlib.h", "string.h", "math.h", "time.h", "ctype.h", "stddef.h", "stdbool.h", "limits.h", "float.h",
    "errno.h", "assert.h", "signal.h", "setjmp.h", "stdarg.h"}

def clasificar_token(ctokens, errores, num_linea):
    ctoken_temp = ""
    i = 0
    length = len(ctokens)
    while i < length:
        c = ctokens[i]
        # Token numérico
        if c.isdigit():
            token = c
            i += 1
            while i < length and (ctokens[i].isdigit() or ctokens[i] == '.'):
                token += ctokens[i]
                i += 1
            if token.count('.') > 1 or token.startswith('.') or token.endswith('.') or (token.count('.') == 1 and (len(token.split('.')) != 2 or not token.split('.')[0].isdigit() or not token.split('.')[1].isdigit())):
                errores.append(f"Error léxico, línea {num_linea}: número inválido '{token}'")
            elif int(token) > 2147483647:
                errores.append(f"Error léxico, línea {num_linea}: número demasiado largo '{token}'")
            else:
                ctoken_temp += f"LIT({token})"
        #token de identificador
        elif c.isidentifier():
            token = c
            i += 1
            while i < length and (ctokens[i].isidentifier() or ctokens[i] == '-' or ctokens[i] == '.'):
                token += ctokens[i]
                i += 1
            # Verificar si el token es una palabra reservada
            if token in pr:
                if i < length and ctokens[i] == '=':
                    errores.append(f"Error léxico, línea {num_linea}: palabra reservada '{token}' utilizada como identificador")
                else:
                    ctoken_temp += f"PR({token})"
            elif token in lib:
                ctoken_temp += f"LIB({token})"
            # Verificar si exite puntuacion al final de la declaracion de un identificador
            elif ';' not in ctokens[i:] or '=' not in ctokens[i:]:
                errores.append(f"Error sintático, línea {num_linea}: declaracion de variable incompleta '{token}'")
            elif '-' in token:
                errores.append(f"Error léxico, línea {num_linea}: identificador inválido '{token}', utilice guión bajo")
            else:
                ctoken_temp += f"ID({token})"
        # Token de cadena
        elif c == '"':
            token = c
            i += 1
            while i < length and ctokens[i] != '"':
                token += ctokens[i]
                i += 1
            if i < length and ctokens[i] == '"':
                token += ctokens[i]
                i += 1
            else:
                errores.append(f"Error léxico, línea {num_linea}: cadena no terminada '{token}'")
            ctoken_temp += f"CAD({token})"
        elif c in lib:
            ctoken_temp += f"LIB({c})"
            i += 1
        elif c in op:
            ctoken_temp += f"OP({c})" 
            i += 1
        elif c in sep:
            ctoken_temp += f"SEP({c})" 
            i += 1
        else:
            # error de carácter inválido
            errores.append(f"Error léxico, línea {num_linea}: caracter inválido '{c}'")
            i += 1
    return ctoken_temp

def obtener_valor_inicial(tokens):
    pattern = r"ID\((\w+)\)\s*OP\(=\)\s*(?:LIT|CAD)\(([\w\W]+?)\)"
    match = re.search(pattern, tokens)
    if match:
        return match.group(2)
    else:
        return ""

def obtener_alcance(linea, nombre):
    if f"ID({nombre})" in linea:
        # Verificar si está dentro de una función
        if "SEP({)" in linea:
            return "local"
        else:
            bloque_abierto = False
            for token in linea.split(","):
                if "SEP({)" in token:
                    bloque_abierto = True
                elif "SEP(})" in token:
                    bloque_abierto = False
            if bloque_abierto:
                return "local"
            else:
                match = re.search(r"ID\((\w+)\)", token)
                if match and match.group(1) == nombre:
                    for tipo in ["int", "char", "float", "double", "void", "short", "long", "static"]:
                        if tipo in linea:
                            return "global"
    return "global"

def obtener_tipo(linea, nombre):
    if f"ID({nombre})" in linea:
        for tipo in ["int", "char", "float", "double", "void", "short", "long", "struct", "union"]:
            if tipo in linea:
                return tipo
    return "Desconocido"

def Compilar():
    global identificadores
    identificadores = []
    errores = []
    cadena = cajaCodigo.get(1.0, "end-1c")
    lineas = cadena.split("\n")
    ctokens = cajaTokens
    # eliminar el contenido previo
    ctokens.delete("1.0", tk.END)
    cajaError.delete("1.0", tk.END)
    # iterar sobre cada línea
    for num_linea, linea in enumerate (lineas, start=1):
        token = ""
        palabra = ""
        i = 0
        while i < len(linea):
            caracter = linea[i]
            if caracter == " " or caracter == "\t":
                if palabra != "":
                    ctoken_temp = clasificar_token(palabra, errores, num_linea)
                    token += ctoken_temp + ","
                    palabra = ""
                i += 1
            # unir los caracteres entre comillas de cada linea para formar una cadena
            elif caracter == '"':
                palabra += caracter
                i += 1
                while i < len(linea) and linea[i] != '"':
                    palabra += linea[i]
                    i += 1
                if i < len(linea) and linea[i] == '"':
                    palabra += linea[i]
                    i += 1
            else:
                palabra += caracter
                i += 1
        if palabra != "":
            ctoken_temp = clasificar_token(palabra, errores, num_linea)
            token += ctoken_temp
        # Verificar si es un identificador y obtener sus datos
        if "ID(" in token and not any(f"Error léxico, línea {num_linea}:" in error for error in errores):
            nombre = re.search(r"ID\((\w+)\)", token).group(1)
            tipo = obtener_tipo(token, nombre)
            valor_inicial = obtener_valor_inicial(token)
            alcance = obtener_alcance(token, nombre)
            identificadores.append((nombre, tipo, valor_inicial, alcance))
        ctokens.insert(tk.INSERT, token + "\n")
    for error in errores:
        cajaError.insert(tk.INSERT, error + "\n")

def TablaS(identificadores):
    # Crear ventana emergente
    ventana = tk.Toplevel()
    ventana.title("Tabla de Símbolos")
    # Crear tabla
    tabla = ttk.Treeview(ventana, columns=('Tipo', 'Valor inicial', 'Alcance'))
    tabla.heading("#0", text='Nombre')
    tabla.heading("Tipo", text='Tipo')
    tabla.heading("Valor inicial", text='Valor inicial/cadena')
    tabla.heading("Alcance", text='Alcance')
    tabla.delete(*tabla.get_children())
    for identificador in identificadores:
        nombre, tipo, valor_inicial, alcance = identificador
        tabla.insert('', 'end', text=nombre, values=(tipo, valor_inicial, alcance))
    tabla.pack()

def salir():
    ventana.destroy()

def enumerarLineas (event):
    # Eliminar números de línea existentes
    cajaLineas.delete("1.0", "end")
    # Obtener número de líneas de la caja de texto
    num_linea = cajaCodigo.index("end").split(".")[0]
    # Agregar números de línea
    for lin in range(1, int(num_linea)):
        cajaLineas.insert(f"{lin}.0", f"{lin}\n", "right")
        #desplzar la caja
        cajaLineas.see(f"{lin}.0")
    #justifiacar a la derecha
    cajaLineas.tag_configure("right", justify="right")

ventana = tk.Tk()
ventana.title("Analizador lexico")
ventana.geometry("1150x660")
ventana.configure(background="aliceblue")
#menu desplegable
menu = tk.Menu(ventana)
opc = tk.Menu(menu, tearoff=0)
ventana.config(menu=menu)
opc.add_command(label="Abrir", command= AbrirArchivo)
opc.add_command(label="Guardar", command= Guardar)
opc.add_command(label="Guardar como", command= GuardarComo)
opc.add_command(label="Compilar", command= Compilar)
opc.add_command(label="Tabla de Simbolos", command=lambda:TablaS(identificadores))
opc.add_separator()
opc.add_command(label="Salir", command= salir)
menu.add_cascade(label="Opciones", menu=opc)

cajaLineas = tk.Text(ventana, width=3, height=25)
cajaLineas.grid(column=0, row=0, padx=5, pady=5)
cajaLineas.config(foreground="blue", font=("Consolas", 11))
# caja de codigo
cajaCodigo = st.ScrolledText(ventana, width=60, height=25)
cajaCodigo.grid(column=1, row=0, padx=5, pady=5)
cajaCodigo.config(foreground="black", font=("Consolas", 11))
cajaCodigo.bind("<KeyRelease>", enumerarLineas)
enumerarLineas(None)
# caja de tokens
cajaTokens = st.ScrolledText(ventana, width=70, height=25)
cajaTokens.grid(column=2, row=0, padx=5, pady=5)
cajaTokens.config(foreground="blue", font=("Consolas", 11))
# caja de error
cajaError = st.ScrolledText(ventana, width=140, height=10)
cajaError.grid(columnspan=3, column=0, row=1, padx=5, pady=10)
cajaError.config(foreground="red", font=("Consolas", 11))

ventana.mainloop()