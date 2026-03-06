# PATH: src/infrastructure/external/storage_adapter.py
# DESC: StorageService portunun adapter implementasyonu.
"""
StorageService adapter: S3/MinIO object storage implementasyonu.

boto3 async wrapper ile S3-uyumlu storage'a bağlanır. Dataset paketleri,
kalibrasyon manifest'leri, analiz raporları ve ödeme dekontları saklanır.

Idempotency: Aynı key'e yazma üzerine yazar (overwrite semantics).
Retry: Transient hatalarda exponential backoff.
"""

from __future__ import annotations

import hashlib
from typing import Any, Optional, cast

import boto3
import structlog
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from src.core.ports.external.storage_service import (
    BlobMetadata,
    PresignedUrl,
    StorageService,
)
from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)


class S3StorageAdapter(StorageService):
    """StorageService port implementasyonu (S3/MinIO).

    boto3 sync client kullanılır; async wrapper gerekirse
    run_in_executor ile sarmalanabilir. Presigned URL'ler
    sınırlı sürelidir (varsayılan 1 saat).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        client_kwargs: dict[str, Any] = {
            "region_name": settings.s3_region,
            "aws_access_key_id": settings.s3_access_key_id.get_secret_value(),
            "aws_secret_access_key": settings.s3_secret_access_key.get_secret_value(),
            "config": BotoConfig(
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
        }
        if settings.s3_endpoint_url:
            client_kwargs["endpoint_url"] = settings.s3_endpoint_url

        self._client = boto3.client("s3", **client_kwargs)
        self._default_expire = settings.s3_presigned_url_expire_seconds

    async def upload_blob(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> BlobMetadata:
        """Blob'u S3'e yükle."""
        put_kwargs: dict[str, Any] = {
            "Bucket": bucket,
            "Key": key,
            "Body": content,
            "ContentType": content_type,
        }
        if metadata:
            put_kwargs["Metadata"] = metadata

        logger.info("storage_upload", bucket=bucket, key=key, size_bytes=len(content))
        response = self._client.put_object(**put_kwargs)
        etag = response.get("ETag", "").strip('"')

        return BlobMetadata(
            blob_id=f"{bucket}/{key}",
            bucket=bucket,
            key=key,
            size_bytes=len(content),
            content_type=content_type,
            etag=etag,
            custom_metadata=metadata,
        )

    async def download_blob(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bytes:
        """Blob içeriğini indir."""
        logger.info("storage_download", bucket=bucket, key=key)
        try:
            response = self._client.get_object(Bucket=bucket, Key=key)
            return cast(bytes, response["Body"].read())
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                raise KeyError(f"Blob bulunamadı: {bucket}/{key}") from exc
            raise

    async def get_blob_metadata(
        self,
        *,
        bucket: str,
        key: str,
    ) -> Optional[BlobMetadata]:
        """Blob metadata bilgisini sorgula (HEAD isteği)."""
        try:
            response = self._client.head_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return None
            raise

        return BlobMetadata(
            blob_id=f"{bucket}/{key}",
            bucket=bucket,
            key=key,
            size_bytes=response.get("ContentLength", 0),
            content_type=response.get("ContentType", "application/octet-stream"),
            etag=response.get("ETag", "").strip('"'),
            custom_metadata=response.get("Metadata"),
        )

    async def generate_presigned_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in_seconds: int = 3600,
        http_method: str = "GET",
    ) -> PresignedUrl:
        """Sınırlı süreli erişim URL'i oluştur."""
        client_method = "get_object" if http_method.upper() == "GET" else "put_object"
        url = self._client.generate_presigned_url(
            ClientMethod=client_method,
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )
        return PresignedUrl(
            url=url,
            expires_in_seconds=expires_in_seconds,
            http_method=http_method.upper(),
        )

    async def delete_blob(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """Blob'u sil."""
        logger.info("storage_delete", bucket=bucket, key=key)
        exists = await self.blob_exists(bucket=bucket, key=key)
        if not exists:
            return False
        self._client.delete_object(Bucket=bucket, Key=key)
        return True

    async def blob_exists(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """Blob'un varlığını kontrol et (HEAD isteği)."""
        try:
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    async def health_check(self) -> bool:
        """Storage servisinin erişilebilirliğini kontrol et."""
        try:
            self._client.list_buckets()
            return True
        except Exception:
            logger.warning("storage_health_check_failed")
            return False
