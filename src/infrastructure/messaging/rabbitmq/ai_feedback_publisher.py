# PATH: src/infrastructure/messaging/rabbitmq/ai_feedback_publisher.py
# DESC: AI feedback publisher adapter.
"""
AI Feedback Publisher: RabbitMQ üzerinden AI feedback event'lerini yayınlar.

Amaç: AIWorkerFeedback portunun RabbitMQ-tabanlı mesajlaşma implementasyonu.
Sorumluluk: Event bus ve kuyruk altyapısı implementasyonu; publish/consume ve dayanıklılık.
  Uzman geri bildirimlerini AI model training pipeline'ına kuyruk üzerinden iletir.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (feedback kayıtları, export parametreleri).
  Çıktı: IO sonuçları (kuyruğa gönderim onayı, pipeline durumu).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: feedback kayıtlarında kişisel veri bulunmaz (KR-019).

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). Mesaj publish idempotent (message_id ile dedup).

Observability (log fields/metrics/traces):
  latency, error_code, retries, queue depth, confirmation_id, routing_key.

Testler: Contract test (port), integration test (RabbitMQ stub), e2e (kritik akış).
Bağımlılıklar: aio-pika (AMQP client), structlog.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional

import structlog

from src.core.ports.external.ai_worker_feedback import (
    AIWorkerFeedback,
    FeedbackPipelineStatus,
    FeedbackSubmissionResult,
    TrainingDatasetExport,
)
from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)

# Exchange ve routing key sabitleri
_FEEDBACK_EXCHANGE = "ai.feedback"
_FEEDBACK_ROUTING_KEY = "feedback.submit"
_EXPORT_ROUTING_KEY = "feedback.export"
_STATUS_ROUTING_KEY = "feedback.status"

# Retry sabitleri (kuyruk bağlantısı için)
_MAX_RECONNECT_ATTEMPTS = 3
_RECONNECT_DELAY_SECONDS = 2


class AIFeedbackPublisher(AIWorkerFeedback):
    """AIWorkerFeedback port implementasyonu (RabbitMQ publisher).

    aio-pika AMQP client ile RabbitMQ'ya bağlanır. Feedback kayıtları
    durable exchange üzerinden training pipeline kuyruğuna publish edilir.

    Idempotency: Aynı feedback_id ile tekrar publish duplicate oluşturmaz
      (consumer tarafında message_id bazlı dedup).
    Retry: Bağlantı kopuşunda exponential backoff ile yeniden bağlanır.
    Delivery: Publisher confirms aktif; mesaj broker'a ulaşana kadar
      publish ACK beklenir.

    Kuyruk topolojisi:
      Exchange: ai.feedback (topic, durable)
      Queue: ai.feedback.submit (durable, dead-letter enabled)
      Queue: ai.feedback.export (durable)
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._rabbitmq_url = settings.rabbitmq_url
        self._connection: Any = None
        self._channel: Any = None

    async def _ensure_connection(self) -> None:
        """RabbitMQ bağlantısını sağlar (lazy initialization)."""
        if self._connection is not None and not self._connection.is_closed:
            return

        try:
            import aio_pika

            self._connection = await aio_pika.connect_robust(
                self._rabbitmq_url,
                timeout=10,
            )
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=10)

            # Exchange ve kuyruk tanımlama (idempotent)
            exchange = await self._channel.declare_exchange(
                _FEEDBACK_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            # Feedback submit kuyruğu (durable + DLX)
            submit_queue = await self._channel.declare_queue(
                "ai.feedback.submit",
                durable=True,
                arguments={
                    "x-dead-letter-exchange": f"{_FEEDBACK_EXCHANGE}.dlx",
                    "x-message-ttl": 86400000,  # 24 saat TTL
                },
            )
            await submit_queue.bind(exchange, _FEEDBACK_ROUTING_KEY)

            # Export kuyruğu
            export_queue = await self._channel.declare_queue(
                "ai.feedback.export",
                durable=True,
            )
            await export_queue.bind(exchange, _EXPORT_ROUTING_KEY)

            logger.info("rabbitmq_connected", exchange=_FEEDBACK_EXCHANGE)

        except Exception:
            logger.error("rabbitmq_connection_failed")
            self._connection = None
            self._channel = None
            raise

    async def _publish_message(
        self,
        routing_key: str,
        body: dict[str, Any],
        message_id: str,
    ) -> None:
        """Mesajı RabbitMQ exchange'ine publish eder."""
        import aio_pika

        await self._ensure_connection()

        exchange = await self._channel.get_exchange(_FEEDBACK_EXCHANGE)

        message = aio_pika.Message(
            body=json.dumps(body, default=str).encode("utf-8"),
            content_type="application/json",
            message_id=message_id,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            timestamp=datetime.utcnow(),
        )

        await exchange.publish(message, routing_key=routing_key)

        logger.info(
            "rabbitmq_message_published",
            routing_key=routing_key,
            message_id=message_id,
        )

    # ------------------------------------------------------------------
    # Feedback gönderim
    # ------------------------------------------------------------------
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
        """Uzman feedback'ini RabbitMQ kuyruğuna publish et (KR-029)."""
        confirmation_id = f"fb-{feedback_id}"

        logger.info(
            "ai_feedback_submit_request",
            feedback_id=str(feedback_id),
            review_id=str(review_id),
            mission_id=str(mission_id),
            model_id=model_id,
            verdict=verdict,
            training_grade=training_grade,
        )

        body: dict[str, Any] = {
            "feedback_id": str(feedback_id),
            "review_id": str(review_id),
            "mission_id": str(mission_id),
            "model_id": model_id,
            "verdict": verdict,
            "training_grade": training_grade,
            "submitted_at": datetime.utcnow().isoformat() + "Z",
        }
        if corrected_class is not None:
            body["corrected_class"] = corrected_class
        if notes is not None:
            body["notes"] = notes
        if expert_confidence is not None:
            body["expert_confidence"] = expert_confidence

        try:
            await self._publish_message(
                routing_key=_FEEDBACK_ROUTING_KEY,
                body=body,
                message_id=confirmation_id,
            )

            logger.info(
                "ai_feedback_submit_success",
                confirmation_id=confirmation_id,
                feedback_id=str(feedback_id),
            )

            return FeedbackSubmissionResult(
                confirmation_id=confirmation_id,
                accepted=True,
                message="Feedback kuyruğa alındı",
            )

        except Exception as exc:
            logger.error(
                "ai_feedback_submit_failed",
                feedback_id=str(feedback_id),
                error=str(exc),
            )
            return FeedbackSubmissionResult(
                confirmation_id=confirmation_id,
                accepted=False,
                message=f"Feedback gönderilemedi: {type(exc).__name__}",
            )

    # ------------------------------------------------------------------
    # Training dataset export
    # ------------------------------------------------------------------
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
        """Training dataset export isteğini kuyruğa gönder (KR-029)."""
        export_id = uuid.uuid4()
        message_id = f"export-{export_id}"

        logger.info(
            "ai_feedback_export_request",
            export_id=str(export_id),
            model_id=model_id,
            format=format,
        )

        body: dict[str, Any] = {
            "export_id": str(export_id),
            "format": format,
        }
        if model_id:
            body["model_id"] = model_id
        if min_grade:
            body["min_grade"] = min_grade
        if verdict_filter:
            body["verdict_filter"] = verdict_filter
        if date_from:
            body["date_from"] = date_from.isoformat() + "Z"
        if date_to:
            body["date_to"] = date_to.isoformat() + "Z"

        await self._publish_message(
            routing_key=_EXPORT_ROUTING_KEY,
            body=body,
            message_id=message_id,
        )

        logger.info(
            "ai_feedback_export_queued",
            export_id=str(export_id),
        )

        # Export asenkron olarak işlenir; blob_id consumer tarafından atanır
        return TrainingDatasetExport(
            export_id=export_id,
            blob_id=f"exports/feedback/{export_id}.{format}",
            record_count=0,  # Consumer tarafından güncellenir
            exported_at=datetime.utcnow(),
            format=format,
        )

    # ------------------------------------------------------------------
    # Durum sorgulama
    # ------------------------------------------------------------------
    async def get_feedback_status(
        self,
        confirmation_id: str,
    ) -> FeedbackPipelineStatus:
        """Gönderilen feedback'in pipeline durumunu sorgula.

        RabbitMQ üzerinden durum sorgulama için HTTP management API veya
        özel status kuyruğu kullanılır.
        """
        logger.info(
            "ai_feedback_status_request",
            confirmation_id=confirmation_id,
        )

        try:
            import httpx

            management_url = f"http://{self._settings.rabbitmq_host}:15672/api/queues/%2F/ai.feedback.submit"

            async with httpx.AsyncClient(
                auth=(
                    self._settings.rabbitmq_user,
                    self._settings.rabbitmq_password.get_secret_value(),
                ),
                timeout=httpx.Timeout(5),
            ) as client:
                response = await client.get(management_url)

                if response.status_code == 200:
                    data = response.json()
                    queue_depth = data.get("messages", 0)

                    logger.info(
                        "ai_feedback_status_result",
                        confirmation_id=confirmation_id,
                        queue_depth=queue_depth,
                    )

                    # Kuyrukta mesaj varsa QUEUED, yoksa PROCESSING
                    status = "QUEUED" if queue_depth > 0 else "PROCESSING"
                    return FeedbackPipelineStatus(
                        confirmation_id=confirmation_id,
                        status=status,
                        detail=f"Kuyruk derinliği: {queue_depth}",
                    )

        except Exception as exc:
            logger.warning(
                "ai_feedback_status_check_failed",
                confirmation_id=confirmation_id,
                error=str(exc),
            )

        # Durum belirlenemezse PROCESSING döner
        return FeedbackPipelineStatus(
            confirmation_id=confirmation_id,
            status="PROCESSING",
            detail="Durum bilgisi alınamadı",
        )

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        """RabbitMQ bağlantısını kontrol et."""
        try:
            await self._ensure_connection()
            return self._connection is not None and not self._connection.is_closed
        except Exception:
            logger.warning("rabbitmq_health_check_failed")
            return False

    # ------------------------------------------------------------------
    # Kaynak temizliği
    # ------------------------------------------------------------------
    async def close(self) -> None:
        """RabbitMQ bağlantısını kapat."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("rabbitmq_connection_closed")
