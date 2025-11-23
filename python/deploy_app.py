import os
import boto3

from dotenv import load_dotenv

# Cargar las variables una vez al inicio del módulo
load_dotenv()

# Definir variables globales
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

def crear_cliente_ec2():
    ec2 = boto3.client(
        'ec2',
        aws_access_key_id=aws_access_key_id,  
        aws_secret_access_key=aws_secret_access_key,  
        aws_session_token=aws_session_token,  
        region_name=aws_region  
    )
    return ec2
    
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
            
def crear_reglas_de_seguridad(ec2, sg_ec2_id, sg_db_id):
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
        
def crear_cliente_rds():
    rds = boto3.client(
        'rds',
        aws_access_key_id=aws_access_key_id,  
        aws_secret_access_key=aws_secret_access_key,  
        aws_session_token=aws_session_token,  
        region_name=aws_region  
    )
    return rds
    
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
    except rds.exceptions.ClientError as e:
        if 'DBInstanceAlreadyExists' in str(e):
            print("La instancia de base de datos ya existe")
        else:
            raise
            
def crear_cliente_s3():
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=aws_region
    )
    return s3_client
    
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
            
def crear_cliente_ec2_resource():
    ec2_resource = boto3.resource(
        'ec2',
        aws_access_key_id=aws_access_key_id,  
        aws_secret_access_key=aws_secret_access_key,  
        aws_session_token=aws_session_token,  
        region_name=aws_region  
    )
    return ec2_resource
            
def crear_instancia_ec2(ec2_resource, sg_ec2_id):
    existing_instances = list(ec2_resource.instances.filter(
        Filters=[
            {'Name': 'tag:Name', 'Values': [aws_ec2_name]},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
        ]
    ))
    
    if existing_instances:
        instance_id = existing_instances[0].id
        print(f"La instancia EC2 '{aws_ec2_name}' ya existe con ID: {instance_id}")
        return instance_id
    try:
        instances = ec2_resource.create_instances(
            ImageId=aws_image_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=aws_instance_type, 
            KeyName=key_name,
            SecurityGroupIds=[sg_ec2_id],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': aws_ec2_name}]
                }
            ]
        )
        instance_id = instances[0].id
        print("Instancia creada con ID:", instance_id)
        return instance_id
    except Exception as e:
        print(f"Error creando instancia EC2: {e}")
        raise

if __name__ == "__main__":
    cliente_ec2 = crear_cliente_ec2()
    crear_par_de_claves(cliente_ec2)
    sg_ec2_id = crear_grupo_seguridad_ec2(cliente_ec2)
    sg_db_id = crear_grupo_seguridad_db(cliente_ec2)
    crear_reglas_de_seguridad(cliente_ec2, sg_ec2_id, sg_db_id)
    cliente_rds = crear_cliente_rds()
    crear_base_de_datos(cliente_rds, sg_db_id)
    cliente_s3 = crear_cliente_s3()
    subir_app_a_s3(cliente_s3)
    ec2_resource = crear_cliente_ec2_resource()
    instance_id = crear_instancia_ec2(ec2_resource, sg_ec2_id)
