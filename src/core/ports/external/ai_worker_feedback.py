# PATH: src/core/ports/external/ai_worker_feedback.py
# DESC: AIWorkerFeedback portu: feedback loop dış bağımlılığı (KR-019).
# SSOT: KR-019 (expert review), KR-029 (training feedback loop)
"""
AIWorkerFeedback portu: feedback loop dış bağımlılığı (KR-019).

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  Uzman geri bildirimlerini AI model training pipeline'ına iletmek ve
  training dataset export işlemlerini soyutlamak.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (FeedbackRecord, export filtreleri).
  Çıktı: IO sonuçları (pipeline'a gönderim onayı, export blob referansı).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: feedback kayıtlarında kişisel veri bulunmaz (KR-019).

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel).

Observability (log fields/metrics/traces):
  latency, error_code, retries, submission_count, export_record_count.

Testler: Contract test (port), integration test (external stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


# ------------------------------------------------------------------
# Port-specific DTOs (Contract nesneleri)
# ------------------------------------------------------------------
@dataclass(frozen=True)
class FeedbackSubmissionResult:
    """AI worker'a gönderilen feedback'in onay sonucu.

    PII içermez; yalnızca referans ID'leri ve durum bilgisi taşır.
    """

    confirmation_id: str
    accepted: bool
    message: str = ""


@dataclass(frozen=True)
class TrainingDatasetExport:
    """Export edilen training dataset'inin metadata'sı.

    blob_id: StorageService'de saklanan export dosyasının referansı.
    record_count: Export edilen feedback kaydı sayısı.
    """

    export_id: uuid.UUID
    blob_id: str
    record_count: int
    exported_at: datetime
    format: str = "jsonl"  # jsonl | csv | arrow


@dataclass(frozen=True)
class FeedbackPipelineStatus:
    """Gönderilen feedback'in pipeline'daki durumu."""

    confirmation_id: str
    status: str  # QUEUED | PROCESSING | ACCEPTED | REJECTED | FAILED
    detail: str = ""


# ------------------------------------------------------------------
# Port Interface
# ------------------------------------------------------------------
class AIWorkerFeedback(ABC):
    """AI Worker Feedback portu (KR-019, KR-029).

    Uzman incelemesi sonrası oluşan feedback kayıtlarını AI model
    training pipeline'ına iletir ve training dataset export'u sağlar.

    Infrastructure katmanı bu interface'i implemente eder:
      - HTTP/gRPC tabanlı AI worker servisi
      - Message queue (RabbitMQ/Kafka) tabanlı async pipeline
      - Batch export için storage + queue kombinasyonu

    Idempotency: Aynı feedback_id ile tekrar gönderim duplicate oluşturmaz.
    Retry: Transient hatalarda exponential backoff ile yeniden denenir.
    """

    # ------------------------------------------------------------------
    # Feedback gönderim
    # ------------------------------------------------------------------
    @abstractmethod
    async def submit_feedback(
        self,
        *,
        feedback_id: uuid.UUID,
        review_id: uuid.UUID,
        mission_id: uuid.UUID,
        model_id: str,
        verdict: str,
        training_grade: str,
        corrected_class: Optional[str] = None,
        notes: Optional[str] = None,
        expert_confidence: Optional[float] = None,
    ) -> FeedbackSubmissionResult:
        """Uzman feedback'ini AI training pipeline'ına gönder (KR-029).

        Idempotent: Aynı feedback_id tekrar gönderildiğinde mevcut sonuç döner.

        Args:
            feedback_id: FeedbackRecord benzersiz ID'si.
            review_id: İlişkili ExpertReview ID'si.
            mission_id: İlişkili Mission ID'si.
            model_id: Feedback'in hedeflediği AI model sürümü.
            verdict: confirmed | corrected | rejected | needs_more_expert.
            training_grade: A | B | C | D | REJECT.
            corrected_class: verdict=corrected ise düzeltilmiş sınıf.
            notes: Uzman notları (PII içermez).
            expert_confidence: Uzman güven skoru (0.0-1.0).

        Returns:
            FeedbackSubmissionResult: Gönderim onay bilgisi.

        Raises:
            TimeoutError: Dış servis yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Training dataset export
    # ------------------------------------------------------------------
    @abstractmethod
    async def export_training_dataset(
        self,
        *,
        model_id: Optional[str] = None,
        min_grade: Optional[str] = None,
        verdict_filter: Optional[list[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        format: str = "jsonl",
    ) -> TrainingDatasetExport:
        """Training dataset'ini filtreli olarak export et (KR-029).

        Admin yetkisi gerektirir (RBAC application katmanında uygulanır).
        Export edilen veri PII içermez.

        Args:
            model_id: Belirli bir model sürümüne ait feedback'ler.
            min_grade: Minimum training grade filtresi (A/B/C/D).
            verdict_filter: Kabul edilen verdict'ler listesi.
            date_from: Başlangıç tarihi (inclusive).
            date_to: Bitiş tarihi (inclusive).
            format: Çıktı formatı (jsonl | csv | arrow).

        Returns:
            TrainingDatasetExport: Export metadata (blob_id, record_count).

        Raises:
            TimeoutError: Export işlemi zaman aşımına uğradığında.
            ValueError: Geçersiz filtre parametresi.
        """

    # ------------------------------------------------------------------
    # Durum sorgulama
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_feedback_status(
        self,
        confirmation_id: str,
    ) -> FeedbackPipelineStatus:
        """Gönderilen feedback'in pipeline durumunu sorgula.

        Args:
            confirmation_id: submit_feedback'ten dönen onay ID'si.

        Returns:
            FeedbackPipelineStatus: Pipeline'daki güncel durum.

        Raises:
            TimeoutError: Dış servis yanıt vermediğinde.
            KeyError: confirmation_id bulunamadığında.
        """

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    @abstractmethod
    async def health_check(self) -> bool:
        """AI worker servisinin erişilebilirliğini kontrol et.

        Returns:
            True: Servis sağlıklı ve erişilebilir.
            False: Servis erişilemez veya hata durumunda.
        """
