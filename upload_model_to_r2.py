"""
Script de un solo uso: sube el modelo BETO local a R2.

Úsalo una vez desde tu máquina (con el modelo en ./modelo_beto_visionprice y
las credenciales R2 en tu .env). Después, en producción el contenedor lo
descarga solo al arrancar.

    python upload_model_to_r2.py
"""
import os

import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

LOCAL_DIR = os.getenv("BETO_MODEL_PATH", "./modelo_beto_visionprice")
PREFIX = os.getenv("R2_MODEL_PREFIX", "models/beto_visionprice").rstrip("/")
BUCKET = os.environ["R2_BUCKET"]

client = boto3.client(
    "s3",
    endpoint_url=os.environ["R2_ENDPOINT_URL"],
    aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    region_name="auto",
    config=Config(signature_version="s3v4"),
)

print(f"Subiendo modelo desde {LOCAL_DIR} a s3://{BUCKET}/{PREFIX}/ ...")
count = 0
for root, _, files in os.walk(LOCAL_DIR):
    for fname in files:
        local_path = os.path.join(root, fname)
        rel = os.path.relpath(local_path, LOCAL_DIR)
        key = f"{PREFIX}/{rel}".replace(os.sep, "/")
        print(f"  → {key}")
        client.upload_file(local_path, BUCKET, key)
        count += 1

print(f"✅ Listo. {count} archivos subidos a R2.")
