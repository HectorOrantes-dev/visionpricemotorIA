import os

import boto3
from botocore.config import Config

from src.feature.extraction.domain.repositories import IObjectStorage


class R2StorageAdapter(IObjectStorage):
    """
    Adaptador de object storage para Cloudflare R2 (compatible con S3 vía boto3).

    El cliente boto3 se crea de forma perezosa (en el primer upload) para que una
    configuración incompleta no tumbe el arranque de la app, sino que falle solo
    el job concreto (cuyo error se reporta por callback).
    """

    def __init__(self, endpoint_url: str, access_key_id: str, secret_access_key: str,
                 bucket: str, public_url: str = ""):
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.bucket = bucket
        self.public_url = public_url.rstrip("/")
        self._client = None

    def _get_client(self):
        if self._client is None:
            missing = [name for name, val in [
                ("R2_ENDPOINT_URL", self.endpoint_url),
                ("R2_ACCESS_KEY_ID", self.access_key_id),
                ("R2_SECRET_ACCESS_KEY", self.secret_access_key),
                ("R2_BUCKET", self.bucket),
            ] if not val]
            if missing:
                raise RuntimeError(f"Configuración de R2 incompleta. Faltan: {', '.join(missing)}")

            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name="auto",
                config=Config(signature_version="s3v4"),
            )
        return self._client

    def upload(self, local_path: str, object_key: str) -> str:
        self._get_client().upload_file(local_path, self.bucket, object_key)
        if self.public_url:
            return f"{self.public_url}/{object_key}"
        return object_key

    def download_prefix(self, prefix: str, dest_dir: str) -> int:
        """
        Descarga todos los objetos bajo `prefix` dentro de `dest_dir`,
        preservando la estructura relativa. Devuelve cuántos archivos bajó.
        Se usa al arrancar para traer el modelo BETO desde R2.
        """
        client = self._get_client()
        paginator = client.get_paginator("list_objects_v2")
        count = 0
        prefix = prefix.rstrip("/")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                rel = key[len(prefix):].lstrip("/")
                local_path = os.path.join(dest_dir, rel)
                os.makedirs(os.path.dirname(local_path) or dest_dir, exist_ok=True)
                client.download_file(self.bucket, key, local_path)
                count += 1
        return count
