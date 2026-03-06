# PATH: src/core/ports/external/storage_service.py
# DESC: StorageService portu: dataset/manifest/report objelerinin saklanması.
# SSOT: KR-018 (kalibrasyon verileri), KR-029 (training export), KR-033 (dekont)
"""
StorageService portu: dataset/manifest/report objelerinin saklanması.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  Object storage (S3/MinIO) ile iletişimi soyutlar. Dataset paketleri,
  kalibrasyon manifest'leri, analiz raporları ve ödeme dekontları saklanır.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (blob içerik, metadata, path).
  Çıktı: IO sonuçları (blob_id, presigned URL, silme onayı).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: dekont blob'ları şifreli saklanır; erişim audit loglanır.
  Presigned URL'ler sınırlı sürelidir (varsayılan 1 saat).

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). Büyük dosya upload'larında multipart desteği.

Observability (log fields/metrics/traces):
  latency, error_code, retries, blob_id, blob_size_bytes, operation_type.

Testler: Contract test (port), integration test (MinIO stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


# ------------------------------------------------------------------
# Port-specific DTOs (Contract nesneleri)
# ------------------------------------------------------------------
@dataclass(frozen=True)
class BlobMetadata:
    """Saklanan blob'un metadata bilgisi.

    PII içermez; yalnızca teknik metadata taşır.
    """

    blob_id: str
    bucket: str
    key: str
    size_bytes: int
    content_type: str = "application/octet-stream"
    etag: Optional[str] = None
    custom_metadata: Optional[dict[str, str]] = None


@dataclass(frozen=True)
class PresignedUrl:
    """Sınırlı süreli erişim URL'i."""

    url: str
    expires_in_seconds: int
    http_method: str = "GET"  # GET | PUT


# ------------------------------------------------------------------
# Port Interface
# ------------------------------------------------------------------
class StorageService(ABC):
    """Object Storage portu.

    Dataset paketleri, kalibrasyon manifest'leri, analiz raporları
    ve ödeme dekontlarının saklanmasını soyutlar.

    Infrastructure katmanı bu interface'i implemente eder:
      - AWS S3 SDK wrapper
      - MinIO client wrapper
      - Yerel dosya sistemi (test/dev)

    Idempotency: Aynı key'e yazma üzerine yazar (overwrite semantics).
    Retry: Transient hatalarda exponential backoff ile yeniden denenir.
    """

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------
    @abstractmethod
    async def upload_blob(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> BlobMetadata:
        """Blob'u storage'a yükle.

        Args:
            bucket: Hedef bucket adı.
            key: Object key (path). Ör: datasets/2026/01/mission-xxx.tar.gz
            content: İkili içerik.
            content_type: MIME tipi.
            metadata: Ek key-value metadata.

        Returns:
            BlobMetadata: Yüklenen blob'un metadata bilgisi.

        Raises:
            TimeoutError: Storage servisi yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------
    @abstractmethod
    async def download_blob(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bytes:
        """Blob içeriğini indir.

        Args:
            bucket: Kaynak bucket adı.
            key: Object key (path).

        Returns:
            bytes: Blob'un ikili içeriği.

        Raises:
            TimeoutError: Storage servisi yanıt vermediğinde.
            KeyError: Blob bulunamadığında.
        """

    # ------------------------------------------------------------------
    # Metadata sorgulama
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_blob_metadata(
        self,
        *,
        bucket: str,
        key: str,
    ) -> Optional[BlobMetadata]:
        """Blob metadata bilgisini sorgula (içerik indirmeden).

        Args:
            bucket: Kaynak bucket adı.
            key: Object key (path).

        Returns:
            BlobMetadata: Blob metadata (varsa).
            None: Blob bulunamadığında.

        Raises:
            TimeoutError: Storage servisi yanıt vermediğinde.
        """

    # ------------------------------------------------------------------
    # Presigned URL
    # ------------------------------------------------------------------
    @abstractmethod
    async def generate_presigned_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in_seconds: int = 3600,
        http_method: str = "GET",
    ) -> PresignedUrl:
        """Sınırlı süreli erişim URL'i oluştur.

        Dekont görüntüleme, rapor indirme vb. için kullanılır.
        Varsayılan süre 1 saat.

        Args:
            bucket: Kaynak bucket adı.
            key: Object key (path).
            expires_in_seconds: URL geçerlilik süresi (saniye).
            http_method: HTTP metodu (GET: indirme, PUT: yükleme).

        Returns:
            PresignedUrl: Süreli erişim URL'i.

        Raises:
            TimeoutError: Storage servisi yanıt vermediğinde.
            KeyError: Blob bulunamadığında (GET için).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete_blob(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """Blob'u sil.

        Args:
            bucket: Kaynak bucket adı.
            key: Object key (path).

        Returns:
            True: Başarıyla silindi.
            False: Blob zaten mevcut değildi.

        Raises:
            TimeoutError: Storage servisi yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Varlık kontrolü
    # ------------------------------------------------------------------
    @abstractmethod
    async def blob_exists(
        self,
        *,
        bucket: str,
        key: str,
    ) -> bool:
        """Blob'un varlığını kontrol et (HEAD isteği).

        Args:
            bucket: Kaynak bucket adı.
            key: Object key (path).

        Returns:
            True: Blob mevcut.
            False: Blob mevcut değil.

        Raises:
            TimeoutError: Storage servisi yanıt vermediğinde.
        """

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    @abstractmethod
    async def health_check(self) -> bool:
        """Storage servisinin erişilebilirliğini kontrol et.

        Returns:
            True: Servis sağlıklı ve erişilebilir.
            False: Servis erişilemez veya hata durumunda.
        """
