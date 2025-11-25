# ---------------------------------------------------------------
# Descripción: Este script automatiza el despliegue completo de una aplicación web en AWS
# Autor: Guillermo Larrea, Fernando Sosa y ChatGPT (GPT-5)
# ---------------------------------------------------------------

import os
import boto3

from dotenv import load_dotenv

# Cargar las variables del archivo .env y creo variables globales
load_dotenv()

key_name = os.getenv('KEY_NAME')
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_session_token = os.getenv('AWS_SESSION_TOKEN')
aws_region = os.getenv('AWS_REGION', 'us-east-1')
aws_image_id = os.getenv('AWS_IMAGE_ID')
aws_instance_type = os.getenv('AWS_INSTANCE_TYPE', 't2.micro')
aws_s3_name = os.getenv('AWS_S3_NAME')
aws_ec2_name = os.getenv('AWS_EC2_NAME')
sg_ec2_name = os.getenv('SG_EC2_NAME')
sg_db_name = os.getenv('SG_DB_NAME')
db_identifier = os.getenv('DB_IDENTIFIER')
db_instance_class = os.getenv('DB_INSTANCE_CLASS')
db_engine = os.getenv('DB_ENGINE')
db_username = os.getenv('DB_USER_NAME')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
app_user = os.getenv('APP_USER')
app_pass = os.getenv('APP_PASS')

# Crea y devuelve un cliente EC2 autenticado con las credenciales del .env
def crear_cliente_ec2():
    ec2 = boto3.client(
        'ec2',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=aws_region
    )
    return ec2                                                        #devuelve el cliente

# Crea el key pair en AWS y evita duplicados, ademas almacena el .pem localmente
def crear_par_de_claves(ec2):
    try:
        key_pair = ec2.create_key_pair(KeyName=key_name)              #crea el key pair en aws
        with open(f'{key_name}.pem', 'w') as file:                    #guarda el .pem localmente
            file.write(key_pair['KeyMaterial'])                       
            os.chmod(f'{key_name}.pem', 0o400)                        #asigna permisos solo lectura
        print(f"Par de claves creado y guardado como {key_name}.pem")
    except ec2.exceptions.ClientError as e:
        if 'InvalidKeyPair.Duplicate' in str(e):                      #verifica si ya existe
            print(f"La clave {key_name} ya existe")
        else:
            raise

# Crea el Security Group para EC2, si existe obtiene su ID   
def crear_grupo_seguridad_ec2(ec2):
    try:
        response = ec2.create_security_group(GroupName=sg_ec2_name, Description="Grupo de seguridad para mi ec2")                                                               #crea el SG en aws
        sg_ec2_id = response['GroupId']                             #Obtengo el ID del sg
        print(f"Grupo de seguridad creado con el id: {sg_ec2_id}")  
        return sg_ec2_id                                            #devuelvo el ID del sg
    except ec2.exceptions.ClientError as e:
        if 'InvalidGroup.Duplicate' in str(e):                      #si ya existe el grupo
            print(f"El grupo de seguridad {sg_ec2_name} ya existe")
            response = ec2.describe_security_groups(
                          Filters=[                                 #busco el SG existente
                            {
                              'Name': 'group-name',
                              'Values': [sg_ec2_name]
                            }
                          ])
            if response['SecurityGroups']:                          #Valido si la busqueda devolvio algo
                for sg in response['SecurityGroups']:
                    sg_ec2_id = sg['GroupId']                       #Extraigo ID del grupo existente
                    print(f"    ID del grupo de seguridad: {sg_ec2_id}")
                    return sg_ec2_id                                #devuelvo el id encontrado
            else:
                print("No se encontraron grupos de seguridad con los filtros especificados.")
        else:
            raise

# Gestiona el Security Group de la base de datos (crea o reutiliza el existente)
def crear_grupo_seguridad_db(ec2):
    try:
        response = ec2.create_security_group(GroupName=sg_db_name, Description="Grupo de seguridad para la base de datos")                                                   #Crea la SG para la base de datos
        sg_db_id = response['GroupId']                            #Obtengo el ID del SG creado
        print(f"Grupo de seguridad creado con el id: {sg_db_id}")
        return sg_db_id                                           #Devuelvo el ID
    except ec2.exceptions.ClientError as e:
        if 'InvalidGroup.Duplicate' in str(e):                    #Si el SG ya existe
            print(f"El grupo de seguridad {sg_db_name} ya existe")
            response = ec2.describe_security_groups(
                Filters=[                                         #Busco el SG existente
                    {
                        'Name': 'group-name',
                        'Values': [sg_db_name]
                    }
                ])
            if response['SecurityGroups']:                        #verifico resultados
                for sg in response['SecurityGroups']:
                    sg_db_id = sg['GroupId']                      #Obtengo el ID del SG existente
                    print(f"    ID del grupo de seguridad: {sg_db_id}")
                    return sg_db_id                               #Devuelvo el ID
            else:
                print("No se encontraron grupos de seguridad con los filtros especificados.")
        else:
            raise

# Abre puertos (22/80) en EC2 y permite a EC2 acceder a DB (3306)
def crear_reglas_de_seguridad(ec2, sg_ec2_id, sg_db_id):    #Crea reglas para los grupos
    try:
        ec2.authorize_security_group_ingress(
            GroupId=sg_ec2_id,                              #En el SG de EC2 agrego reglas
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },                                          #Habilito SSH desde cualquier IP
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }                                           #Habilito HTTP desde cualquier IP
            ]
        )
    except ec2.exceptions.ClientError as e:
        if 'InvalidPermission.Duplicate' in str(e):         #Si ya existen aviso en pantalla
            print("Las reglas de seguridad de ec2 ya existen")
        else:
            raise
    
    try:
        ec2.authorize_security_group_ingress(
            GroupId=sg_db_id,                               #En el SG de la DB agrego regla
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 3306,
                    'ToPort': 3306,
                    'UserIdGroupPairs': [{'GroupId': sg_ec2_id}]
                }                                           #Habilito 3306 solo desde mi EC2
            ]
        )
    except ec2.exceptions.ClientError as e:
        if 'InvalidPermission.Duplicate' in str(e):         #Si ya existen aviso en pantalla
            print("Las reglas de seguridad de db ya existen")
        else:
            raise

# Crea cliente RDS para administrar instancias de base de datos
def crear_cliente_rds():
    rds = boto3.client(
        'rds',                                       #Servicio RDS
        aws_access_key_id=aws_access_key_id,  
        aws_secret_access_key=aws_secret_access_key,  
        aws_session_token=aws_session_token,  
        region_name=aws_region  
    )
    return rds                                       # Devuelve cliente RDS

# Consulta RDS y devuelve el endpoint público de la DB
def obtener_endpoint_rds(rds):
    """Obtener el endpoint de la base de datos RDS"""
    try:                                             #Consulta la instancia buscando primera coincidencia
        response = rds.describe_db_instances(DBInstanceIdentifier=db_identifier)
        db_instance = response['DBInstances'][0]
        return db_instance['Endpoint']['Address']    #Devuelve endpoint
    except Exception as e:
        print(f"Error obteniendo endpoint de RDS: {e}")
        return None

# Crea la instancia RDS o usa la existente y devuelve su endpoint
def crear_base_de_datos(rds, sg_db_id):
    try:
        response = rds.create_db_instance(
            DBInstanceIdentifier=db_identifier,    #nombre
            AllocatedStorage=20,                   #tamaño en GB
            DBInstanceClass=db_instance_class,     #tipo de instancia
            Engine=db_engine,                      #motor de db
            MasterUsername=db_username,            #usuario admin
            MasterUserPassword=db_password,        #contraseña admin
            VpcSecurityGroupIds=[sg_db_id]         #SG asignado a la DB
        )
        print("Instancia RDS creada")
        print("Esperando que quede disponible ...")
        waiter = rds.get_waiter('db_instance_available')       #espera que este lista
        waiter.wait(DBInstanceIdentifier=db_identifier)
        print("Ahora la db ya está pronta")
        endpoint = obtener_endpoint_rds(rds)                   #obtengo endpoint
        if endpoint:
            print(f"Endpoint de la base de datos: {endpoint}")
            return endpoint
        return None
    except rds.exceptions.ClientError as e:
        if 'DBInstanceAlreadyExists' in str(e):                #si ya existe la DB
            print("La instancia de base de datos ya existe")
            endpoint = obtener_endpoint_rds(rds)               #obtengo endpoint existente
            if endpoint:
                print(f"Endpoint de la base de datos existente: {endpoint}")
                return endpoint
            return None
        else:
            raise

# Crea y devuelve un cliente S3 con credenciales AWS     
def crear_cliente_s3():
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=aws_region
    )
    return s3_client            #Devuelve cliente s3

# Sube archivos de la app al bucket S3, omitiendo existentes
def subir_app_a_s3(s3_client):
    try:
        s3_client.create_bucket(Bucket=aws_s3_name)        #Creo el bucket s3
        print(f"Bucket {aws_s3_name} creado")
    except (s3_client.exceptions.BucketAlreadyExists, 
            s3_client.exceptions.BucketAlreadyOwnedByYou): #si ya existe
        print(f"El bucket {aws_s3_name} ya existe")
        
    archivos_a_incluir = [
        'app.css', 'app.js', 'config.php', 'index.html',
        'index.php', 'init_db.sql', 'login.css', 'login.html',
        'login.js', 'login.php'
    ]                                                      #Archivos que se subiran
    
    for archivo in archivos_a_incluir:
        if os.path.exists(archivo):                        #Confirma si estan los archivos
            try:                                           #Busca si ya existen en la s3
                s3_client.head_object(Bucket=aws_s3_name, Key=archivo)
                print(f"    {archivo} ya existe en S3, omitiendo")
                continue
            except:
                pass                                       #si el archivo no existe lo sube
                
            s3_client.upload_file(archivo, aws_s3_name, archivo)
            print(f"    {archivo} subido a S3")
        else:
            print(f"    {archivo} no existe, omitiendo")   #si el archivo no lo tengo localmente
            
# Crea un cliente EC2 tipo resource para manipular instancias
def crear_cliente_ec2_resource():
    ec2_resource = boto3.resource(
        'ec2',                                   #Servicio ec2 en modo resource
        aws_access_key_id=aws_access_key_id,  
        aws_secret_access_key=aws_secret_access_key,  
        aws_session_token=aws_session_token,  
        region_name=aws_region  
    )
    return ec2_resource                          #Devuelve resource de ec2
            
# crear o reutilizar una instancia EC2 en AWS y preparar la aplicación web para que quede disponible
def crear_instancia_ec2(ec2_resource, sg_ec2_id, db_endpoint):

    user_data_script = generar_user_data(db_endpoint)    # Ejecuta script de Bash al iniciar EC2

    existing_instances = list(ec2_resource.instances.filter(
        Filters=[                                        # Busca instancias creadas
            {'Name': 'tag:Name', 'Values': [aws_ec2_name]},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'pending']}
        ]
    ))
    
    if existing_instances:
        instance = existing_instances[0]                 #Usa la instancia existente
        instance_id = instance.id                        #Id de la instancia
        print(f"La instancia EC2 '{aws_ec2_name}' ya existe con ID: {instance_id}")
        instance.reload()                                #Actualiza datos
        ip_publica = instance.public_ip_address          #Obtengo IP publica y la muestro
        print(f"App disponible en http://{ip_publica}/login.php")
        return instance_id                               #Retorno la id
        
    try:
        instances = ec2_resource.create_instances(
            ImageId=aws_image_id,                        #AMI usada
            MinCount=1,
            MaxCount=1,                                  #1 sola instancia
            InstanceType=aws_instance_type,              #tipo
            KeyName=key_name,                            #Par de claves
            SecurityGroupIds=[sg_ec2_id],                #SG asignado
            UserData=user_data_script,                   #Script de inicializacion
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': aws_ec2_name}]  #Nombre en tags
                }
            ]
        )
        instance_id = instances[0].id
        print("Instancia creada con ID:", instance_id)
        print("    Esperando a que inicie instancia")
        instance = instances[0]
        instance.wait_until_running()                    #Espera estado de "running"
        instance.reload()                                #actualiza info
        
        while instance.public_ip_address is None:        #Esperar hasta obtener IP pública
            time.sleep(3)                                #Espera un poco y recarga
            instance.reload()

        ip_publica = instance.public_ip_address
        print(f"Desplegando app en: http://{ip_publica}/login.php")
        return instance_id
    except Exception as e:
        print(f"Error creando instancia EC2: {e}")       #Muestra si surge un error
        raise

# Genera el script de Bash al inicializar la instancia
def generar_user_data(db_endpoint):  
    return f"""#!/bin/bash

export AWS_ACCESS_KEY_ID={aws_access_key_id}
export AWS_SECRET_ACCESS_KEY={aws_secret_access_key}
export AWS_SESSION_TOKEN={aws_session_token}
export AWS_REGION={aws_region}
export S3_BUCKET={aws_s3_name}

#actualiza sistema e instala paquetes
sudo dnf clean all
sudo dnf makecache
sudo dnf -y update
sudo dnf -y install httpd php php-cli php-fpm php-common php-mysqlnd mariadb105 mariadb105-server-utils.x86_64

#configura e inicia servicios
sudo systemctl enable --now httpd
sudo systemctl enable --now php-fpm
sudo systemctl restart httpd php-fpm

#copia aplicacion desde el s3
aws s3 cp s3://{aws_s3_name}/ /var/www/html --recursive
mv /var/www/html/init_db.sql /var/www

#Archivo de prueba
echo "<?php phpinfo(); ?>" | sudo tee /var/www/html/info.php

# Importar base de datos a RDS
mysql -h {db_endpoint} -u {db_username} -p{db_password} < /var/www/init_db.sql

# Crear archivo .env con la configuración
tee /var/www/.env > /dev/null <<EOF
DB_HOST={db_endpoint}
DB_NAME={db_name}
DB_USER={db_username}
DB_PASS={db_password}

APP_USER={app_user}
APP_PASS={app_pass}
EOF

# Configurar permisos seguros
sudo chown apache:apache /var/www/.env
sudo chmod 600 /var/www/.env

# Configurar permisos generales
sudo chown -R apache:apache /var/www/html
sudo chmod -R 755 /var/www/html

# Reiniciar servicios para aplicar cambios
sudo systemctl restart httpd php-fpm
"""

if __name__ == "__main__":
    cliente_ec2 = crear_cliente_ec2()
    crear_par_de_claves(cliente_ec2)
    sg_ec2_id = crear_grupo_seguridad_ec2(cliente_ec2)
    sg_db_id = crear_grupo_seguridad_db(cliente_ec2)
    crear_reglas_de_seguridad(cliente_ec2, sg_ec2_id, sg_db_id)
    cliente_rds = crear_cliente_rds()
    db_endpoint = crear_base_de_datos(cliente_rds, sg_db_id)
    cliente_s3 = crear_cliente_s3()
    subir_app_a_s3(cliente_s3)
    ec2_resource = crear_cliente_ec2_resource()
    instance_id = crear_instancia_ec2(ec2_resource, sg_ec2_id, db_endpoint)
