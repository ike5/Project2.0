"""
Object storage (MinIO in dev, S3 in prod) via boto3.

The browser uploads file bytes **directly** to storage using a short-lived
*presigned* URL — the bytes never pass through Django. Django only mints the URL and
later stores the file's metadata (key, name, size) as an Attachment row.
"""
import boto3
from botocore.client import Config
from django.conf import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def presign_put(key: str, content_type: str, expires: int = 300) -> str:
    """A URL the browser can PUT the file bytes to (valid `expires` seconds)."""
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def presign_get(key: str, expires: int = 3600) -> str:
    """A URL the browser can GET the file from (valid `expires` seconds)."""
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def ensure_bucket() -> None:
    """Create the bucket if it doesn't exist (dev convenience)."""
    s3 = _client()
    existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
    if settings.S3_BUCKET not in existing:
        s3.create_bucket(Bucket=settings.S3_BUCKET)
