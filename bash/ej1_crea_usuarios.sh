#!/bin/bash

# ---------------------------------------------------------------
# Descripción: Crea usuarios desde un archivo con formato definido.
# Autor: Guillermo Larrea, Fernando Sosa y ChatGPT (GPT-5)
# ---------------------------------------------------------------

#Codigos de error, se manejan como variables permitiondo que estos sean cambiados de ser nesesario de una manera sencilla
error_formato=1
error_arch=2
error_perm=3

#Variables a usar
desplegar_info=0
contrase=""
archivo_usuarios=""

#Funcion que señala error de uso y muestra su correcto funcionamiento
mostrar_uso() {
    echo "Modo de uso: $0 [-i] [-c contraseña] archivo_usuarios" >&2
    exit $error_formato
}

#Con el comando "getopts" nos permitira prosesar modificadores nesesarios "-i" y "-c" con una contraseña
while getopts ":ic:" opcion; do
    case "$opcion" in
        i) desplegar_info=1
		#controlo si nesesito desplegar la informacion de creacion de usuario
		;;		
        c) contrase="$OPTARG"
		#getopts pone automaticamente el argumento que continua del modificadores "-c" 
		#de una opción en la variable OPTARG que sera la contaseña de los usuarios
		;;
        :) echo "Error de uso, la opción -$OPTARG requiere un argumento." >&2
		#La opcion ":" en un "case" usando "getopts" señala que no axiste un argumento despues del "-c" 
		mostrar_uso
		;;
        \?) echo "Error de uso, opción inválida -$OPTARG" >&2
		mostrar_uso
		;;
    esac
done

#getopts solo procesa opciones y sus argumentos, sin tomar en cuenta argumentos posicionales (argumentos sin - o --)
#Esto puede generar error si los usuarios introducen argumentos extra
#Esto se solucionara con el comando "shift" y la variable de "getopts" "OPTIND", que mueve los modificadores dado por el usario
shift $((OPTIND - 1))

#Verificar que se recibió un archivo
if [ $# -ne 1 ]; then
    echo "Error de uso, falta el archivo de usuarios" >&2
    mostrar_uso
fi

archivo_usuarios="$1"

#Verifico que el archivo existe
if [ ! -e "$archivo_usuarios" ]; then
    echo "Error de uso, el archivo '$archivo_usuarios' no existe." >&2
    exit $error_arch
fi
#Verifico que es un archivo
if [ ! -f "$archivo_usuarios" ]; then
    echo "Error de uso, '$archivo_usuarios' no es un archivo regular." >&2
    exit $error_arch
fi
#Verifico que tiene permiso de lectura
if [ ! -r "$archivo_usuarios" ]; then
    echo "Error de uso, no tiene permisos de lectura sobre '$archivo_usuarios'." >&2
    exit $error_perm
fi

#Proceso archivo línea a línea

#Cuento usarios creados
total_ok=0

#con "IFS" denoto el separador ":" que se usara en el formato del archivo y se le asigna a las variables
while IFS=":" read -r usuario comentario dir_home crear_home shell_def; do
    #Cheque con el usuario exite como variable y si no existe con "continue" se omite los comandos restantes dentro del bucle 
	#para la iteración actual y pasa al siguiente iteración del bucle.
    [ -z "$usuario" ] && echo "ATENCION: usuario sin valor NO pudo ser creado" && continue
	
	#convertimos a "crear_home" en minuscula si o si, para poder comprobar en cualquier caso que alla un "no"
    prueba_de_home="${crear_home,,}"

    #Similar al caso anterior utilizo un "test" verificando si el valor de crear_home es un "no" y si lo es saltamos los comandos restantes y se pasa de bucle 
    [ ! -d "$dir_home" ] && [ "$prueba_de_home" = "no" ] && echo "ATENCION: el usuario $usuario no pudo ser creado" && echo "" && continue	
	
    #Verifco los valores de las variables, si estos estan vacios los cambio con ":-" por "valor por defecto"
    comentario=${comentario:-"<valor por defecto>"}
    dir_home=${dir_home:-"<valor por defecto>"}
    crear_home=${crear_home:-"<valor por defecto>"}
    shell_def=${shell_def:-"/bin/bash"}


    #se construira el comando "useradd", para esto se asignara como una variable y dependiendo el contenido del archivo con los usarios se armara
    cmd="useradd"
    #Se susitura los valores quitados del archivo por cada uno de los valores por defecto de ser el caso
    [ "$comentario" != "<valor por defecto>" ] && cmd+=" -c \"$comentario\""
    [ "$dir_home" != "<valor por defecto>" ] && cmd+=" -d \"$dir_home\""
    [ "$shell_def" != "<valor por defecto>" ] && cmd+=" -s \"$shell_def\""

    #Crear directorio home si aplica
    if [ "$prueba_de_home" = "si" ]; then
        cmd+=" -m"
    fi

    cmd+=" $usuario"

    #Luego de construir el comando "useradd" y todas sus opciones, con "eval"
	#que permite usar un string como si fuera un comando se implementara al usuario
    eval $cmd
    if [ $? -eq 0 ]; then
        #Comprobamos que el comando "useradd" sea exitoso y sumamos una ejecucion de este
		((total_ok++))

        #Asignar contraseña si corresponde con el comando "chpasswd" y envaiamos sus posibles errores a "/dev/null"
        if [ -n "$contrase" ]; then
            echo "$usuario:$contrase" | chpasswd 2>/dev/null
        fi

        if [ $desplegar_info -eq 1 ]; 
		    #Desplegamos la informacion de creacion del usuario
            echo "Usuario $usuario creado con éxito con datos indicados:"
            echo "Comentario: $comentario"
            echo "Dir home: $dir_home"
            echo "Asegurado existencia de directorio home: $crear_home"
            echo "Shell por defecto: $shell_def"
            echo ""
        fi
    else
        if [ $desplegar_info -eq 1 ]; then
		    #Damos un mesaje de error por si no se puede crear el usuario
            echo ""
			echo "ATENCIÓN: el usuario $usuario no pudo ser creado"
            echo ""
        fi
    fi

done < "$archivo_usuarios"
#A el "for" cargamos el archivo que se le paso
if [ $desplegar_info -eq 1 ]; then
    echo "Se han creado $total_ok usuarios con éxito."
fi
#Final de cuenta de usuarios creados