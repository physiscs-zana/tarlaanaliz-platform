# PATH: src/infrastructure/integrations/storage/s3_storage.py
# DESC: StorageService portunun S3-uyumlu implementasyonu (AWS S3 / MinIO).
"""
S3 Storage adapter: AWS S3 / MinIO object storage implementasyonu.

Amaç: StorageService portunun S3-uyumlu storage implementasyonu.
Sorumluluk: boto3 client ile S3/MinIO'ya blob yükleme, indirme, metadata
  sorgulama, presigned URL oluşturma, silme ve varlık kontrolü.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (bucket, key, content, metadata).
  Çıktı: Port DTO'ları (BlobMetadata, PresignedUrl).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; access_key/secret_key env/secret manager üzerinden; TLS zorunlu.
  Presigned URL'ler sınırlı sürelidir (varsayılan 1 saat).
  Dekont blob'ları şifreli saklanır; erişim audit loglanır.

Hata Modları (idempotency/retry/rate limit):
  Aynı key'e yazma üzerine yazar (overwrite semantics, idempotent).
  Retry: boto3 adaptive retry (max 3 attempts).
  Büyük dosya upload'larında multipart desteği (gelecek versiyon).

Observability (log fields/metrics/traces):
  latency, error_code, retries, blob_id, blob_size_bytes, operation_type.

Testler: Contract test (port), integration test (MinIO stub), e2e.
Bağımlılıklar: boto3, botocore, structlog.
Notlar/SSOT: Tek referans: tarlaanaliz_platform_tree v3.2.2 FINAL.
  Aynı kavram başka yerde tekrar edilmez.
"""

from __future__ import annotations

import asyncio
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


class S3StorageIntegration(StorageService):
    """StorageService port implementasyonu (S3/MinIO) — integrations katmanı.

    boto3 sync client kullanır. Adaptive retry modunda (max 3 attempts)
    transient hatalar otomatik yeniden denenir.

    MinIO desteği: s3_endpoint_url tanımlı ise MinIO'ya bağlanır.
    Presigned URL'ler varsayılan olarak 1 saat geçerlidir.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        client_kwargs: dict[str, Any] = {
            "region_name": settings.s3_region,
            "aws_access_key_id": settings.s3_access_key_id.get_secret_value(),
            "aws_secret_access_key": settings.s3_secret_access_key.get_secret_value(),
            "config": BotoConfig(
                retries={"max_attempts": 3, "mode": "adaptive"},
                signature_version="s3v4",
            ),
        }
        if settings.s3_endpoint_url:
            client_kwargs["endpoint_url"] = settings.s3_endpoint_url

        self._client = boto3.client("s3", **client_kwargs)
        self._default_bucket = settings.s3_default_bucket
        self._default_expire = settings.s3_presigned_url_expire_seconds

    def _resolve_bucket(self, bucket: str) -> str:
        """Bucket adı boş ise default'u kullanır."""
        return bucket or self._default_bucket

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------
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
        resolved_bucket = self._resolve_bucket(bucket)

        put_kwargs: dict[str, Any] = {
            "Bucket": resolved_bucket,
            "Key": key,
            "Body": content,
            "ContentType": content_type,
        }
        if metadata:
            put_kwargs["Metadata"] = metadata

        logger.info(
            "s3_upload",
            bucket=resolved_bucket,
            key=key,
            size_bytes=len(content),
            content_type=content_type,
        )

        response = await asyncio.to_thread(self._client.put_object, **put_kwargs)
        etag = response.get("ETag", "").strip('"')

        return BlobMetadata(
            blob_id=f"{resolved_bucket}/{key}",
            bucket=resolved_bucket,
            key=key,
            size_bytes=len(content),
            content_type=content_type,
            etag=etag,
            custom_metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------
    async def download_blob(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bytes:
        """Blob içeriğini indir."""
        resolved_bucket = self._resolve_bucket(bucket)

        logger.info("s3_download", bucket=resolved_bucket, key=key)

        try:
            response = await asyncio.to_thread(self._client.get_object, Bucket=resolved_bucket, Key=key)
            return cast(bytes, response["Body"].read())
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                raise KeyError(f"Blob bulunamadı: {resolved_bucket}/{key}") from exc
            raise

    # ------------------------------------------------------------------
    # Metadata sorgulama
    # ------------------------------------------------------------------
    async def get_blob_metadata(
        self,
        *,
        bucket: str,
        key: str,
    ) -> Optional[BlobMetadata]:
        """Blob metadata bilgisini sorgula (HEAD isteği)."""
        resolved_bucket = self._resolve_bucket(bucket)

        try:
            response = await asyncio.to_thread(self._client.head_object, Bucket=resolved_bucket, Key=key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return None
            raise

        return BlobMetadata(
            blob_id=f"{resolved_bucket}/{key}",
            bucket=resolved_bucket,
            key=key,
            size_bytes=response.get("ContentLength", 0),
            content_type=response.get("ContentType", "application/octet-stream"),
            etag=response.get("ETag", "").strip('"'),
            custom_metadata=response.get("Metadata"),
        )

    # ------------------------------------------------------------------
    # Presigned URL
    # ------------------------------------------------------------------
    async def generate_presigned_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in_seconds: int = 3600,
        http_method: str = "GET",
    ) -> PresignedUrl:
        """Sınırlı süreli erişim URL'i oluştur."""
        # SEC-FIX: Validate bucket and key to prevent path traversal
        import re
        if not re.match(r"^[a-zA-Z0-9._-]+$", bucket):
            raise ValueError(f"Invalid bucket name: {bucket}")
        if ".." in key or key.startswith("/") or "\x00" in key:
            raise ValueError(f"Invalid object key: path traversal or null byte detected")

        resolved_bucket = self._resolve_bucket(bucket)
        client_method = "get_object" if http_method.upper() == "GET" else "put_object"

        url = await asyncio.to_thread(self._client.generate_presigned_url,
            ClientMethod=client_method,
            Params={"Bucket": resolved_bucket, "Key": key},
            ExpiresIn=expires_in_seconds or self._default_expire,
        )

        logger.info(
            "s3_presigned_url",
            bucket=resolved_bucket,
            key=key,
            http_method=http_method.upper(),
            expires_in_seconds=expires_in_seconds,
        )

        return PresignedUrl(
            url=url,
            expires_in_seconds=expires_in_seconds,
            http_method=http_method.upper(),
        )

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    async def delete_blob(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """Blob'u sil."""
        resolved_bucket = self._resolve_bucket(bucket)

        logger.info("s3_delete", bucket=resolved_bucket, key=key)

        exists = await self.blob_exists(bucket=resolved_bucket, key=key)
        if not exists:
            return False

        await asyncio.to_thread(self._client.delete_object, Bucket=resolved_bucket, Key=key)
        return True

    # ------------------------------------------------------------------
    # Varlık kontrolü
    # ------------------------------------------------------------------
    async def blob_exists(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """Blob'un varlığını kontrol et (HEAD isteği)."""
        resolved_bucket = self._resolve_bucket(bucket)

        try:
            await asyncio.to_thread(self._client.head_object, Bucket=resolved_bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        """Storage servisinin erişilebilirliğini kontrol et."""
        try:
            await asyncio.to_thread(self._client.list_buckets)
            return True
        except Exception:
            logger.warning("s3_health_check_failed")
            return False
