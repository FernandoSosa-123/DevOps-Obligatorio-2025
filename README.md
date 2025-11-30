# DevOps-Obligatorio-2025
Este obligatorio 2025 consta de 2 partes
## 1-Script de bash
El siguiente script ej1_crea_usuarios.sh se tendra que ejecutar con permisos sudo, 
tambien se encuentra un ejemplo del archivo que contendra los usuarios a crear.

Ejemplo de uso: ej1_crea_usuarios.sh [-i] [-c contraseña ] usuarios.example
## 2-Script de python
El script principal para desplegar la aplicacion es deploy_app.py

Para poder ejecutarlo sera necesario un entorno virtual en el cual instalara las
bibliotecas necesarias con el archivo requirements.txt, los pasos estan descriptos en
este readme. Ademas los archivos necesarios para la app se deben encontrar en el mismo
directorio como se encuentran en la carpeta /python/
 
# GITHUB

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

# PYTHON Y CREACION DE AMBIENTE VIRTUAL
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
