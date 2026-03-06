# PATH: src/infrastructure/messaging/rabbitmq/training_feedback_publisher.py
# DESC: Training feedback publisher adapter.
"""
Training Feedback Publisher: eğitim geri bildirim event'lerini RabbitMQ'ya yayınlar.

Amaç: TrainingFeedbackSubmitted, TrainingFeedbackAccepted, TrainingFeedbackRejected
  ve TrainingDataExported domain event'lerini training feedback exchange'ine
  publish eder. AI model training pipeline'ına veri akışını sağlar.

Sorumluluk: Event bus ve kuyruk altyapısı implementasyonu; publish ve dayanıklılık.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (TrainingFeedback domain event'leri).
  Çıktı: IO sonuçları (kuyruğa gönderim onayı).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: feedback kayıtlarında kişisel veri bulunmaz (KR-019).

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). event_id ile dedup.

Observability (log fields/metrics/traces):
  latency, error_code, retries, feedback_id, training_grade, event_type.

Testler: Contract test (port), integration test (RabbitMQ stub), e2e (kritik akış).
Bağımlılıklar: RabbitMQPublisher, structlog, domain events.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import structlog

from src.core.domain.events.base import DomainEvent
from src.core.domain.events.training_feedback_events import (
    TrainingDataExported,
    TrainingFeedbackAccepted,
    TrainingFeedbackRejected,
    TrainingFeedbackSubmitted,
)
from src.infrastructure.config.settings import Settings
from src.infrastructure.messaging.rabbitmq.publisher import RabbitMQPublisher
from src.infrastructure.messaging.rabbitmq_config import (
    TRAINING_EXPORT_ROUTING_KEY,
    TRAINING_FEEDBACK_EXCHANGE,
    TRAINING_SUBMIT_ROUTING_KEY,
)

logger = structlog.get_logger(__name__)

# Event tipi -> routing key eşlemesi
_EVENT_ROUTING_MAP: dict[str, str] = {
    "TrainingFeedbackSubmitted": TRAINING_SUBMIT_ROUTING_KEY,
    "TrainingFeedbackAccepted": TRAINING_SUBMIT_ROUTING_KEY,
    "TrainingFeedbackRejected": TRAINING_SUBMIT_ROUTING_KEY,
    "TrainingDataExported": TRAINING_EXPORT_ROUTING_KEY,
}


class TrainingFeedbackPublisher:
    """Training feedback event'lerini RabbitMQ'ya publish eden adapter.

    RabbitMQPublisher'ı compose ederek training feedback exchange'ine
    domain event'lerini yayınlar. Her event, event_id ile idempotent
    olarak publish edilir.

    Kuyruk topolojisi:
      Exchange: training.feedback (topic, durable)
      Queue: training.feedback.submit (durable, DLX enabled)
      Queue: training.feedback.export (durable)
    """

    def __init__(self, settings: Settings) -> None:
        self._publisher = RabbitMQPublisher(settings)

    async def publish_feedback_event(self, event: DomainEvent) -> None:
        """Training feedback domain event'ini kuyruğa publish eder.

        Event tipi otomatik olarak routing key'e çevrilir.

        Args:
            event: TrainingFeedback domain event'i.

        Raises:
            ValueError: Desteklenmeyen event tipi.
            ConnectionError: Broker bağlantısı yoksa.
        """
        routing_key = _EVENT_ROUTING_MAP.get(event.event_type)
        if routing_key is None:
            raise ValueError(f"Desteklenmeyen training feedback event tipi: {event.event_type}")

        body = event.to_dict()
        message_id = f"tf-{body['event_id']}"

        logger.info(
            "training_feedback_publish_request",
            event_type=event.event_type,
            event_id=body["event_id"],
        )

        try:
            await self._publisher.publish(
                exchange_name=TRAINING_FEEDBACK_EXCHANGE,
                routing_key=routing_key,
                body=body,
                message_id=message_id,
            )

            logger.info(
                "training_feedback_published",
                event_type=event.event_type,
                event_id=body["event_id"],
                routing_key=routing_key,
            )

        except Exception as exc:
            logger.error(
                "training_feedback_publish_failed",
                event_type=event.event_type,
                event_id=body["event_id"],
                error=str(exc),
            )
            raise

    async def publish_submitted(
        self,
        event: TrainingFeedbackSubmitted,
    ) -> None:
        """TrainingFeedbackSubmitted event'ini publish et (KR-019).

        Args:
            event: Uzman geri bildirim gönderim event'i.
        """
        await self.publish_feedback_event(event)

    async def publish_accepted(
        self,
        event: TrainingFeedbackAccepted,
    ) -> None:
        """TrainingFeedbackAccepted event'ini publish et.

        Args:
            event: Geri bildirim kabul event'i.
        """
        await self.publish_feedback_event(event)

    async def publish_rejected(
        self,
        event: TrainingFeedbackRejected,
    ) -> None:
        """TrainingFeedbackRejected event'ini publish et.

        Args:
            event: Geri bildirim red event'i.
        """
        await self.publish_feedback_event(event)

    async def publish_exported(
        self,
        event: TrainingDataExported,
    ) -> None:
        """TrainingDataExported event'ini publish et (KR-019).

        Args:
            event: Eğitim verisi export event'i.
        """
        await self.publish_feedback_event(event)

    async def health_check(self) -> bool:
        """Publisher bağlantı sağlığını kontrol eder."""
        return await self._publisher.health_check()

    async def close(self) -> None:
        """Publisher bağlantısını kapatır."""
        await self._publisher.close()
