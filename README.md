# DevOps-Obligatorio-2025

## Contenido:
1- Introduccion

2- Parte 1 script de Bash: ej1_crea_usuarios.sh

3- Parte 2 script de Python: deploy_app.py

4- GitHub y flujo de trabajo

5- Entorno virtual python

## 1- Introduccion
Banco Riendo estuvo analizando los beneficios de adoptar un modelo de nube hibrida por
requerimientos del negocio la adopción deber ser lo más acelerada posible por lo tanto 
nos encargamos de las siguientes tareas:

1- Un script en Bash que cree los usuarios contenidos en un archivo pasado como
parámetro, con información que especifica la Shell por defecto, directorio home,
comentario y si se va a crear o no el directorio home si no existe. El script incluye las 
siguientes opciones e informa, para cada usuario contenido en el archivo pasado como parámetro, el
resultado de la creación (si fue creado con éxito o no) y crear todos los usuarios con una contraseña 
pasada como parámetro de la opción.

2- Un script en Python en donde se deberá automatizar el despliegue de la aplicación
de recursos humanos en donde se alojan información sensible como son los nombres,
email y salario de los empleados actuales de la empresa con los siguientes requerimientos:
Este despliegue considere todas las medidas de seguridad para evitar
Filtraciones, todos los cambios deberán ser trazables mediante un repositorio de GitHub y la documentacion
se encontrara en el README en la cual se deberá ver reflejado Descripción del proyecto, Requisitos // Requerimientos,
Modo de uso, etc.

## 2- Script de bash
El siguiente script ej1_crea_usuarios.sh se tendra que ejecutar con permisos sudo, 
tambien se encuentra un ejemplo del archivo que contendra los usuarios a crear.

Ejemplo de uso: ej1_crea_usuarios.sh [-i] [-c contraseña ] usuarios.example

El script crea los usuarios indicados en el archivo usuarios.example pasado
como parámetro, definiendo para cada usuario (según el contenido del archivo pasado como
parámetro) los campos de shell por defecto, directorio home, comentario y si se va a crear o no el
directorio home si no existe. En caso que alguno de esos campos no esté definido para algún usuario
en el archivo usuarios.example, se creara el usuario usando los valores por
defecto que utilice el comando que crea los usuarios; useradd.
La información de los usuarios, contenida en el archivo pasado como parámetro, estará separada por
":" y tendrá una sintaxis de la forma:
Nombre de usuario: Comentario: Directorio home: crear dir home si no existe (SI/NO): Shell por defecto
Si el script recibe el modificador -i (desplegar información de la creación de los usuarios), para cada
usuario a crear, contenido en el archivo usuarios.example, se desplegará información
del resultado de la creación o intento de creación del mismo. Después del listado de información de
cada usuario, y con una línea vacía de separación, se desplegará el total de usuarios creados con éxito.
Si el script recibe el modificador -c, seguido de un texto que se considerará como una contraseña, el
script asignará esa contraseña a cada uno de los usuarios creados. Si no se recibe este modificador
(no se define una contraseña para los usuarios), se tomará (en este aspecto) el comportamiento por
defecto del comando que se use para crear los usuarios; useradd.
En caso de errores, el script terminara con un código de retorno distinto de 0 y diferente para
cada posible error encontrado (como por ejemplo archivo inexistente, que no sea un archivo regular o
no se tengan permisos de lectura sobre él, sintaxis incorrecta del archivo pasado como parámetro -
donde alguna de sus líneas no contenga exactamente 4 campos separados por ":"-, parámetros
incorrectos -como no recibirse la contraseña al usarse el modificador -c o usarse modificadores
inválidos-, cantidad de parámetros incorrectos, y cualquier otro error que se produzca), y desplegará
un mensaje de error adecuado por la salida estándar de errores.

### 2.1- Ejemplo de uso 
Suponga que el archivo Usuarios, que está en el directorio corriente de trabajo, contiene la siguiente
información (los campos del archivo son Nombre de usuario: Comentario: Directorio home: crear el
directorio home si no existe (SI/NO): Shell por defecto):

    pepe:Este es mi amigo pepe:/home/jose:SI:/bin/bash

    papanatas:Este es un usuario trucho:/trucho:NO:/bin/sh

    elmaligno::::/bin/el_maligno

Y se ejecuta el comando:
ej1_crea_usuarios.sh -i -c "123456" usuarios.example

Entonces se crean con éxito los usuarios pepe y elmaligno pero no se puede crear el usuario
papanatas, desplegara por la salida estándar la información siguiente (por la opción -i):
Si se pueden crear con éxito los usuarios pepe y elmaligno pero no se puede crear el usuario
papanatas, se deberá (aparte de crear los usuarios pepe y elmaligno con contraseña 123456) desplegar
por la salida estándar la información siguiente (por la opción -i):

Usuario pepe creado con éxito con datos indicados:

    Comentario: Este es mi amigo pepe

    Dir home: :/home/jose

    Asegurado existencia de directorio home: SI

    Shell por defecto: /bin/bash

ATENCION: el usuario papanatas no pudo ser creado

Usuario elmaligno creado con éxito con datos indicados:

    Comentario: < valor por defecto >

    Dir home: < valor por defecto >

    Asegurado existencia de directorio home: < valor por defecto >

    Shell por defecto: /bin/el_maligno

Se han creado 2 usuarios con éxito.


## 3- Script de python
El script principal para desplegar la aplicacion es deploy_app.py

Este script despliega automáticamente una aplicación web PHP con apache en AWS, creando y configurando todos 
los recursos necesarios AWS que se detallaran a continuacion:

    1) Importa librerias y variables de entorno desde el archivo .env

    2) Crea y devuelve un cliente EC2 autenticado con las credenciales del .env

    3) Crea el key pair en AWS y evita duplicados, ademas almacena el .pem localmente

    4) Crea el Security Group para EC2, si existe obtiene su ID

    5) Gestiona el Security Group de la base de datos (crea o reutiliza el existente)

    6) Abre puertos (22/80) en EC2 y permite a EC2 acceder a DB (3306)

    7) Crea cliente RDS para administrar instancias de base de datos

    8) Consulta RDS y devuelve el endpoint público de la DB

    9) Crea la instancia RDS o usa la existente y devuelve su endpoint

    10) Crea y devuelve un cliente S3 con credenciales AWS

    11) Crea un cliente EC2 tipo resource para manipular instancias

    12) crear o reutilizar una instancia EC2 en AWS y preparar la aplicación web para que quede disponible

    13) Genera el script de Bash al inicializar la instancia 

        13.1) actualiza sistema e instala paquetes

        13.2) configura e inicia servicios apache y php

        13.3) copia aplicacion desde el s3

        13.4) Importar base de datos a RDS

        13.5) Crear archivo .env con la configuración

        13.6) Configurar permisos

        13.7) Reinicia los servicios para aplicar cambios
 
# Como usar GITHUB

Instalación y configuración inicial de github (una vez)
## Instalar Git
sudo apt install git-all
### Generar clave SSH
ssh-keygen -t ed25519 -C "tu_email@example.com"
### Copiar clave y agregar en GitHub
cat ~/.ssh/id_ed25519.pub
### Pegar en GitHub → Settings → SSH and GPG keys
### Verificar conexión
ssh -T git@github.com
### Clonar repositorio git
git clone git@github.com:FernandoSosa-123/DevOps-Obligatorio-2025.git

## Creacion y seleccion de rama
### Creacion de nueva rama
git checkout -b feature/mirama

### subir rama por primera vez
git add .

git commit -m"Descripcion de cambios"

git push --set-upstram origin feature/mirama

en github abrir pull request y aprobar el merge main
## Flujo de trabajo diario github
### Hacer cambios en archivos...
git checkout feature/mirama

git add . (todos los archivos)

git add nombre_archivo (un solo archivo)

git status (verifica los cambios a subir)

git commit -m "Descripción de los cambios"

git push

en github abrir pull request y aprobar el merge main 
### Flujo copiar main a mi rama y subir rama
git checkout main

git fetch

git pull

git checkout feature/mirama

git merge main

git push
### Flujo copiar mi rama a la main
git checkout main

git pull

git merge feature/mirama

git push
## Archivos importantes github
.gitignore: Archivos que Git ignorará

.env.example: Template de variables de entorno

.env: Variables locales (NUNCA subir a Git)

.venv/ Entorno virtual de python (NUNCA subir a git)

test_deploy_app.py Script temporal para testeo (NUNCA subir a git)

# Como crear AMBIENTE VIRTUAL python
verificar primero si esta python instalado python3 --version

## instalacion python y modulo ambiente virtual
sudo apt update

sudo apt install python3

sudo apt install python3-venv

## creacion de ambiente virtual
python3 -m venv .venv

## Activacion del entorno
source .venv/bin/activate

## Desactivacion del entorno
deactivate

## Instalacion de Dependencias 
### Activar tu entorno virtual
source .venv/bin/activate

### Opcion 1: Instalar desde requirements.txt
pip install -r requirements.txt

### Opcion 2 Instalar manualmente
pip install boto3

pip install dotenv
