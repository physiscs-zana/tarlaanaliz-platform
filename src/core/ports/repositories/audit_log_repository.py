# PATH: src/core/ports/repositories/audit_log_repository.py
# DESC: AuditLogEntry yazma/okuma için repository portu.
# SSOT: BOLUM 3 (gözlemlenebilirlik standardı), KR-062 (denetlenebilirlik)
"""
AuditLogRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  AuditLogEntry entity'sinin WORM (Write Once Read Many) depolama erişimini soyutlar.
  Append-only: güncelleme ve silme işlemi YOKTUR.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (AuditLogEntry, correlation_id, filtreler).
  Çıktı: IO sonuçları (DB kayıt, List[AuditLogEntry]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: loglar PII İÇERMEZ; actor_id_hash tek yönlü kimliktir (BOLUM 3).

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel).

Observability (log fields/metrics/traces):
  latency, error_code, retries; DB query time.

Testler: Contract test (port), integration test (DB/external stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.core.domain.entities.audit_log_entry import AuditLogEntry


class AuditLogRepository(ABC):
    """AuditLogEntry persistence port (BOLUM 3, KR-062).

    WORM (append-only) denetim logu deposu.
    Infrastructure katmanı bu interface'i implemente eder.

    WORM garantisi: update ve delete metodu YOKTUR.
    Idempotency: audit_log_id benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Yazma (append-only)
    # ------------------------------------------------------------------
    @abstractmethod
    async def append(self, entry: AuditLogEntry) -> None:
        """Yeni denetim logu ekle (WORM: yalnızca yazma).

        Args:
            entry: Eklenecek AuditLogEntry (frozen/immutable).

        Raises:
            IntegrityError: audit_log_id benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, audit_log_id: uuid.UUID) -> Optional[AuditLogEntry]:
        """audit_log_id ile AuditLogEntry getir.

        Args:
            audit_log_id: Aranacak log ID'si.

        Returns:
            AuditLogEntry veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_correlation_id(self, correlation_id: str) -> List[AuditLogEntry]:
        """Bir correlation_id'ye ait tüm logları getir.

        İstek izleme (request tracing) için tüm servislerdeki logları toplar.

        Args:
            correlation_id: İzlenecek korelasyon ID'si.

        Returns:
            AuditLogEntry listesi, created_at'e göre sıralı.
        """

    @abstractmethod
    async def list_by_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
    ) -> List[AuditLogEntry]:
        """Belirli bir kaynağa ait tüm logları getir.

        Args:
            resource_type: Kaynak türü (ör. "Mission", "Field").
            resource_id: Kaynak ID'si.

        Returns:
            AuditLogEntry listesi, created_at'e göre sıralı.
        """

    @abstractmethod
    async def list_by_actor(
        self,
        actor_id_hash: str,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """Bir aktöre ait logları getir (zaman aralığı opsiyonel).

        Args:
            actor_id_hash: Aktör kimlik hash'i (PII değil).
            since: Başlangıç tarihi (dahil, opsiyonel).
            until: Bitiş tarihi (dahil değil, opsiyonel).

        Returns:
            AuditLogEntry listesi, created_at'e göre sıralı.
        """

    @abstractmethod
    async def list_by_event_type(
        self,
        event_type: str,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """Belirli event_type'a göre logları getir.

        Args:
            event_type: Olay türü (INGEST|AUTH|RBAC|PRICING|JOB|RESULT|SECURITY|SYSTEM).
            since: Başlangıç tarihi (dahil, opsiyonel).
            until: Bitiş tarihi (dahil değil, opsiyonel).

        Returns:
            AuditLogEntry listesi, created_at'e göre sıralı.
        """
