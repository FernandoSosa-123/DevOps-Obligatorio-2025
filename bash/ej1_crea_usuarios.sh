#!/bin/bash


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