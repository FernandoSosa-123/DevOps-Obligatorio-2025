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
    return ec2

# Crea el key pair en AWS y evita duplicados, ademas almacena el .pem localmente
def crear_par_de_claves(ec2):
    try:
        key_pair = ec2.create_key_pair(KeyName=key_name)
        with open(f'{key_name}.pem', 'w') as file:
            file.write(key_pair['KeyMaterial'])
            os.chmod(f'{key_name}.pem', 0o400)
        print(f"Par de claves creado y guardado como {key_name}.pem")
    except ec2.exceptions.ClientError as e:
        if 'InvalidKeyPair.Duplicate' in str(e):
            print(f"La clave {key_name} ya existe")
        else:
            raise

# Crea el Security Group para EC2, si existe obtiene su ID   
def crear_grupo_seguridad_ec2(ec2):
    try:
        response = ec2.create_security_group(GroupName=sg_ec2_name, Description="Grupo de seguridad para mi ec2")
        sg_ec2_id = response['GroupId']
        print(f"Grupo de seguridad creado con el id: {sg_ec2_id}")
        return sg_ec2_id
    except ec2.exceptions.ClientError as e:
        if 'InvalidGroup.Duplicate' in str(e):
            print(f"El grupo de seguridad {sg_ec2_name} ya existe")
            response = ec2.describe_security_groups(
                          Filters=[
                            {
                              'Name': 'group-name',
                              'Values': [sg_ec2_name]
                            }
                          ])
            if response['SecurityGroups']:
                for sg in response['SecurityGroups']:
                    sg_ec2_id = sg['GroupId']
                    print(f"    ID del grupo de seguridad: {sg_ec2_id}")
                    return sg_ec2_id
            else:
                print("No se encontraron grupos de seguridad con los filtros especificados.")
        else:
            raise

# Gestiona el Security Group de la base de datos (crea o reutiliza el existente)
def crear_grupo_seguridad_db(ec2):
    try:
        response = ec2.create_security_group(GroupName=sg_db_name, Description="Grupo de seguridad para la base de datos")
        sg_db_id = response['GroupId']
        print(f"Grupo de seguridad creado con el id: {sg_db_id}")
        return sg_db_id
    except ec2.exceptions.ClientError as e:
        if 'InvalidGroup.Duplicate' in str(e):
            print(f"El grupo de seguridad {sg_db_name} ya existe")
            response = ec2.describe_security_groups(
                Filters=[
                    {
                        'Name': 'group-name',
                        'Values': [sg_db_name]
                    }
                ])
            if response['SecurityGroups']:
                for sg in response['SecurityGroups']:
                    sg_db_id = sg['GroupId']
                    print(f"    ID del grupo de seguridad: {sg_db_id}")
                    return sg_db_id
            else:
                print("No se encontraron grupos de seguridad con los filtros especificados.")
        else:
            raise

# Abre puertos (22/80) en EC2 y permite a EC2 acceder a DB (3306)
def crear_reglas_de_seguridad(ec2, sg_ec2_id, sg_db_id):    #Crea reglas para los grupos y comprueba si existen
    try:
        ec2.authorize_security_group_ingress(
            GroupId=sg_ec2_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
    except ec2.exceptions.ClientError as e:
        if 'InvalidPermission.Duplicate' in str(e):
            print("Las reglas de seguridad de ec2 ya existen")
        else:
            raise
    
    try:
        ec2.authorize_security_group_ingress(
            GroupId=sg_db_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 3306,
                    'ToPort': 3306,
                    'UserIdGroupPairs': [{'GroupId': sg_ec2_id}]
                }
            ]
        )
    except ec2.exceptions.ClientError as e:
        if 'InvalidPermission.Duplicate' in str(e):
            print("Las reglas de seguridad de db ya existen")
        else:
            raise

# Crea cliente RDS para administrar instancias de base de datos
def crear_cliente_rds():
    rds = boto3.client(
        'rds',
        aws_access_key_id=aws_access_key_id,  
        aws_secret_access_key=aws_secret_access_key,  
        aws_session_token=aws_session_token,  
        region_name=aws_region  
    )
    return rds

# Consulta RDS y devuelve el endpoint público de la DB
def obtener_endpoint_rds(rds):
    """Obtener el endpoint de la base de datos RDS"""
    try:
        response = rds.describe_db_instances(DBInstanceIdentifier=db_identifier)
        db_instance = response['DBInstances'][0]
        return db_instance['Endpoint']['Address']
    except Exception as e:
        print(f"Error obteniendo endpoint de RDS: {e}")
        return None

# Crea la instancia RDS o usa la existente y devuelve su endpoint
def crear_base_de_datos(rds, sg_db_id):
    try:
        response = rds.create_db_instance(
            DBInstanceIdentifier=db_identifier,
            AllocatedStorage=20,
            DBInstanceClass=db_instance_class,
            Engine=db_engine,
            MasterUsername=db_username,
            MasterUserPassword=db_password,
            VpcSecurityGroupIds=[sg_db_id]
        )
        print("Instancia RDS creada")
        print("Esperando que quede disponible ...")
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=db_identifier)
        print("Ahora la db ya está pronta")
        endpoint = obtener_endpoint_rds(rds)
        if endpoint:
            print(f"Endpoint de la base de datos: {endpoint}")
            return endpoint
        return None
    except rds.exceptions.ClientError as e:
        if 'DBInstanceAlreadyExists' in str(e):
            print("La instancia de base de datos ya existe")
            endpoint = obtener_endpoint_rds(rds)
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
    return s3_client

# Sube archivos de la app al bucket S3, omitiendo existentes
def subir_app_a_s3(s3_client):
    try:
        s3_client.create_bucket(Bucket=aws_s3_name)
        print(f"Bucket {aws_s3_name} creado")
    except (s3_client.exceptions.BucketAlreadyExists, 
            s3_client.exceptions.BucketAlreadyOwnedByYou):
        print(f"El bucket {aws_s3_name} ya existe")
        
    archivos_a_incluir = [
        'app.css', 'app.js', 'config.php', 'index.html',
        'index.php', 'init_db.sql', 'login.css', 'login.html',
        'login.js', 'login.php'
    ]
    
    for archivo in archivos_a_incluir:
        if os.path.exists(archivo):
            try:
                s3_client.head_object(Bucket=aws_s3_name, Key=archivo)
                print(f"    {archivo} ya existe en S3, omitiendo")
                continue
            except:
                pass  # El archivo no existe, proceder a subirlo
                
            s3_client.upload_file(archivo, aws_s3_name, archivo)
            print(f"    {archivo} subido a S3")
        else:
            print(f"    {archivo} no existe, omitiendo")
            
# Crea un cliente EC2 tipo resource para manipular instancias
def crear_cliente_ec2_resource():
    ec2_resource = boto3.resource(
        'ec2',
        aws_access_key_id=aws_access_key_id,  
        aws_secret_access_key=aws_secret_access_key,  
        aws_session_token=aws_session_token,  
        region_name=aws_region  
    )
    return ec2_resource
            
# crear o reutilizar una instancia EC2 en AWS y preparar la aplicación web para que quede disponible
def crear_instancia_ec2(ec2_resource, sg_ec2_id, db_endpoint):

    user_data_script = generar_user_data(db_endpoint)    # Genera el script de Bash al inicializar la instancia


    existing_instances = list(ec2_resource.instances.filter(
        Filters=[
            {'Name': 'tag:Name', 'Values': [aws_ec2_name]},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'pending']}
        ]
    ))
    
    if existing_instances:
        instance = existing_instances[0]     
        instance_id = instance.id            

        print(f"La instancia EC2 '{aws_ec2_name}' ya existe con ID: {instance_id}")

        instance.reload()                   
        ip_publica = instance.public_ip_address  

        print(f"App disponible en http://{ip_publica}/login.php")

        return instance_id
        
    try:
        instances = ec2_resource.create_instances(
            ImageId=aws_image_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=aws_instance_type, 
            KeyName=key_name,
            SecurityGroupIds=[sg_ec2_id],
            UserData=user_data_script,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': aws_ec2_name}]
                }
            ]
        )
        instance_id = instances[0].id
        print("Instancia creada con ID:", instance_id)
        print("    Esperando a que inicie instancia")
        instance = instances[0]
        instance.wait_until_running()
        instance.reload()
        
        # Esperar hasta obtener IP pública
        while instance.public_ip_address is None:
            time.sleep(3)
            instance.reload()

        ip_publica = instance.public_ip_address
        print(f"Desplegando app en: http://{ip_publica}/login.php")
        return instance_id
    except Exception as e:
        print(f"Error creando instancia EC2: {e}")
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
