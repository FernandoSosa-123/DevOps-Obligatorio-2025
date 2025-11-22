# DevOps-Obligatorio-2025

########################### GITHUB ##########################

Instalación y configuración inicial de github (una vez)
# Instalar Git
sudo apt install git-all
# Generar clave SSH
ssh-keygen -t ed25519 -C "tu_email@example.com"
# Copiar clave y agregar en GitHub
cat ~/.ssh/id_ed25519.pub
# Pegar en GitHub → Settings → SSH and GPG keys
# Verificar conexión
ssh -T git@github.com
# Clonar repositorio git
git clone git@github.com:FernandoSosa-123/DevOps-Obligatorio-2025.git

Flujo de trabajo diario github
# Hacer cambios en archivos...
git add . (todos los archivos) git add nombre_archivo (un solo archivo)
git status (verifica los cambios a subir)
git commit -m "Descripción de los cambios"
git push 
# Sincronizar con main
git pull

Archivos importantes github
.gitignore: Archivos que Git ignorará
.env.example: Template de variables de entorno
.env: Variables locales (NUNCA subir a Git)
