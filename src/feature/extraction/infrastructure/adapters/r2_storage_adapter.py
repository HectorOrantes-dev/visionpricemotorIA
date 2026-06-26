import boto3
from botocore.config import Config

from src.feature.extraction.domain.repositories import IObjectStorage


class R2StorageAdapter(IObjectStorage):
    """
    Adaptador de object storage para Cloudflare R2 (compatible con S3 vía boto3).
    """

    def __init__(self, endpoint_url: str, access_key_id: str, secret_access_key: str,
                 bucket: str, public_url: str = ""):
        self.bucket = bucket
        self.public_url = public_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    def upload(self, local_path: str, object_key: str) -> str:
        self.client.upload_file(local_path, self.bucket, object_key)
        if self.public_url:
            return f"{self.public_url}/{object_key}"
        return object_key
