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
            
def crear_grupo_seguridad(ec2):
    try:
        response = ec2.create_security_group(GroupName=sg_ec2_name, Description="Grupo de seguridad para mi ec2")
        sg_ec2_id = response['GroupId']
        print(f"Grupo de seguridad creado con el id: {sg_ec2_id}")
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
                    print(f"ID del grupo de seguridad: {sg_ec2_id}")
            else:
                print("No se encontraron grupos de seguridad con los filtros especificados.")
        else:
            raise
    
if __name__ == "__main__":
    cliente_ec2 = crear_cliente_ec2()
    crear_par_de_claves(cliente_ec2)
    crear_grupo_seguridad(cliente_ec2)
