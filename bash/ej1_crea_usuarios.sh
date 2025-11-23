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