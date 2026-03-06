# PATH: src/infrastructure/messaging/event_publisher.py
# DESC: Genel domain event publisher adapter.
"""
Event Publisher: domain event'lerini RabbitMQ'ya yayınlayan genel adapter.

Amaç: Tüm domain event'lerini (analysis, mission, payment, expert, field,
  subscription, training feedback) event tipine göre doğru exchange ve
  routing key'e yönlendirir. Application layer'daki use-case'ler bu
  publisher'ı kullanarak event yayınlar.

Sorumluluk: Event bus ve kuyruk altyapısı implementasyonu; publish ve dayanıklılık.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (DomainEvent nesneleri).
  Çıktı: IO sonuçları (kuyruğa gönderim onayı).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: event payload'larında PII bulunmaz.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). event_id ile dedup.

Observability (log fields/metrics/traces):
  latency, error_code, retries, event_type, routing_key, message_id.

Testler: Contract test (port), integration test (RabbitMQ stub), e2e (kritik akış).
Bağımlılıklar: RabbitMQPublisher, structlog, domain events.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

from typing import Any

import structlog

from src.core.domain.events.base import DomainEvent
from src.infrastructure.config.settings import Settings
from src.infrastructure.messaging.rabbitmq.publisher import RabbitMQPublisher
from src.infrastructure.messaging.rabbitmq_config import (
    DOMAIN_EVENTS_EXCHANGE,
    TRAINING_FEEDBACK_EXCHANGE,
)

logger = structlog.get_logger(__name__)


# Event tipi -> (exchange, routing_key) eşlemesi
_EVENT_CATEGORY_MAP: dict[str, tuple[str, str]] = {
    # Analysis events -> domain.events exchange, event.analysis.* routing
    "AnalysisRequested": (DOMAIN_EVENTS_EXCHANGE, "event.analysis.requested"),
    "AnalysisStarted": (DOMAIN_EVENTS_EXCHANGE, "event.analysis.started"),
    "AnalysisCompleted": (DOMAIN_EVENTS_EXCHANGE, "event.analysis.completed"),
    "AnalysisFailed": (DOMAIN_EVENTS_EXCHANGE, "event.analysis.failed"),
    "CalibrationValidated": (DOMAIN_EVENTS_EXCHANGE, "event.analysis.calibration_validated"),
    "LowConfidenceDetected": (DOMAIN_EVENTS_EXCHANGE, "event.analysis.low_confidence"),
    # Mission events -> domain.events exchange, event.mission.* routing
    "MissionAssigned": (DOMAIN_EVENTS_EXCHANGE, "event.mission.assigned"),
    "MissionStarted": (DOMAIN_EVENTS_EXCHANGE, "event.mission.started"),
    "DataUploaded": (DOMAIN_EVENTS_EXCHANGE, "event.mission.data_uploaded"),
    "MissionAnalysisRequested": (DOMAIN_EVENTS_EXCHANGE, "event.mission.analysis_requested"),
    "MissionCompleted": (DOMAIN_EVENTS_EXCHANGE, "event.mission.completed"),
    "MissionCancelled": (DOMAIN_EVENTS_EXCHANGE, "event.mission.cancelled"),
    "MissionReplanQueued": (DOMAIN_EVENTS_EXCHANGE, "event.mission.replan_queued"),
    # Payment events -> domain.events exchange, event.payment.* routing
    "PaymentIntentCreated": (DOMAIN_EVENTS_EXCHANGE, "event.payment.intent_created"),
    "ReceiptUploaded": (DOMAIN_EVENTS_EXCHANGE, "event.payment.receipt_uploaded"),
    "PaymentApproved": (DOMAIN_EVENTS_EXCHANGE, "event.payment.approved"),
    "PaymentRejected": (DOMAIN_EVENTS_EXCHANGE, "event.payment.rejected"),
    # Expert events
    "ExpertRegistered": (DOMAIN_EVENTS_EXCHANGE, "event.expert.registered"),
    "ExpertActivated": (DOMAIN_EVENTS_EXCHANGE, "event.expert.activated"),
    "ExpertDeactivated": (DOMAIN_EVENTS_EXCHANGE, "event.expert.deactivated"),
    "FeedbackProvided": (DOMAIN_EVENTS_EXCHANGE, "event.expert.feedback_provided"),
    # Expert review events
    "ExpertReviewRequested": (DOMAIN_EVENTS_EXCHANGE, "event.expert_review.requested"),
    "ExpertReviewAssigned": (DOMAIN_EVENTS_EXCHANGE, "event.expert_review.assigned"),
    "ExpertReviewCompleted": (DOMAIN_EVENTS_EXCHANGE, "event.expert_review.completed"),
    "ExpertReviewEscalated": (DOMAIN_EVENTS_EXCHANGE, "event.expert_review.escalated"),
    # Field events
    "FieldCreated": (DOMAIN_EVENTS_EXCHANGE, "event.field.created"),
    "FieldUpdated": (DOMAIN_EVENTS_EXCHANGE, "event.field.updated"),
    "FieldCropUpdated": (DOMAIN_EVENTS_EXCHANGE, "event.field.crop_updated"),
    "FieldDeleted": (DOMAIN_EVENTS_EXCHANGE, "event.field.deleted"),
    # Subscription events
    "SubscriptionCreated": (DOMAIN_EVENTS_EXCHANGE, "event.subscription.created"),
    "SubscriptionActivated": (DOMAIN_EVENTS_EXCHANGE, "event.subscription.activated"),
    "MissionScheduled": (DOMAIN_EVENTS_EXCHANGE, "event.subscription.mission_scheduled"),
    "SubscriptionCompleted": (DOMAIN_EVENTS_EXCHANGE, "event.subscription.completed"),
    "SubscriptionRescheduled": (DOMAIN_EVENTS_EXCHANGE, "event.subscription.rescheduled"),
    # Training feedback events -> dedicated exchange
    "TrainingFeedbackSubmitted": (TRAINING_FEEDBACK_EXCHANGE, "feedback.submit"),
    "TrainingFeedbackAccepted": (TRAINING_FEEDBACK_EXCHANGE, "feedback.submit"),
    "TrainingFeedbackRejected": (TRAINING_FEEDBACK_EXCHANGE, "feedback.submit"),
    "TrainingDataExported": (TRAINING_FEEDBACK_EXCHANGE, "feedback.export"),
}


class EventPublisher:
    """Genel domain event publisher.

    Tüm domain event'lerini event_type'a göre doğru RabbitMQ exchange
    ve routing key'e yönlendirir. Application layer'daki use-case'ler
    tek bir publish noktası üzerinden event yayınlar.

    Özellikler:
      - event_type bazlı otomatik routing
      - Bilinmeyen event tipleri için fallback (domain.events exchange)
      - event_id ile idempotent publish
      - Batch publish desteği
    """

    def __init__(self, settings: Settings) -> None:
        self._publisher = RabbitMQPublisher(settings)

    def _resolve_routing(
        self,
        event: DomainEvent,
    ) -> tuple[str, str]:
        """Event tipine göre exchange ve routing key belirler.

        Args:
            event: Domain event'i.

        Returns:
            (exchange_name, routing_key) tuple.
        """
        event_type = event.event_type
        if event_type in _EVENT_CATEGORY_MAP:
            return _EVENT_CATEGORY_MAP[event_type]

        # Bilinmeyen event tipleri -> genel domain events exchange
        logger.warning(
            "event_publisher_unknown_event_type",
            event_type=event_type,
        )
        return (DOMAIN_EVENTS_EXCHANGE, f"event.unknown.{event_type.lower()}")

    async def publish(self, event: DomainEvent) -> None:
        """Tek bir domain event'i yayınla.

        Args:
            event: Yayınlanacak domain event'i.

        Raises:
            ConnectionError: Broker'a bağlantı kurulamadığında.
            TimeoutError: Broker yanıt vermediğinde.
        """
        exchange_name, routing_key = self._resolve_routing(event)
        body = event.to_dict()
        message_id = f"evt-{body['event_id']}"

        logger.info(
            "event_publisher_publish_request",
            event_type=event.event_type,
            event_id=body["event_id"],
            exchange=exchange_name,
            routing_key=routing_key,
        )

        await self._publisher.publish(
            exchange_name=exchange_name,
            routing_key=routing_key,
            body=body,
            message_id=message_id,
        )

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Birden fazla event'i sıralı yayınla.

        Args:
            events: Yayınlanacak event listesi (sıralı).

        Raises:
            ConnectionError: Broker'a bağlantı kurulamadığında.
        """
        if not events:
            return

        # Exchange'e göre grupla
        grouped: dict[str, list[tuple[str, dict[str, Any], str]]] = {}

        for event in events:
            exchange_name, routing_key = self._resolve_routing(event)
            body = event.to_dict()
            message_id = f"evt-{body['event_id']}"

            if exchange_name not in grouped:
                grouped[exchange_name] = []
            grouped[exchange_name].append((routing_key, body, message_id))

        # Her exchange grubu için batch publish
        for exchange_name, messages in grouped.items():
            await self._publisher.publish_batch(exchange_name, messages)

        logger.info(
            "event_publisher_batch_published",
            total_count=len(events),
            exchange_count=len(grouped),
        )

    async def health_check(self) -> bool:
        """Publisher bağlantı sağlığını kontrol eder."""
        return await self._publisher.health_check()

    async def close(self) -> None:
        """Publisher bağlantısını kapatır."""
        await self._publisher.close()
