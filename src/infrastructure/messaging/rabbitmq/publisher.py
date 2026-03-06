# PATH: src/infrastructure/messaging/rabbitmq/publisher.py
# DESC: RabbitMQ publisher adapter.
"""
RabbitMQ Publisher: genel amaçlı mesaj yayınlama adapter'ı.

Amaç: RabbitMQ üzerinden mesaj publish etmek için yeniden kullanılabilir
  altyapı bileşeni. EventBus, TrainingFeedbackPublisher ve diğer
  publisher'lar bu sınıfı compose eder.

Sorumluluk: Event bus ve kuyruk altyapısı implementasyonu; publish ve dayanıklılık.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (exchange, routing_key, body).
  Çıktı: IO sonuçları (publish onayı, hata bildirimi).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: event payload'larında PII bulunmaz.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). message_id ile dedup.

Observability (log fields/metrics/traces):
  latency, error_code, retries, routing_key, message_id.

Testler: Contract test (port), integration test (RabbitMQ stub), e2e (kritik akış).
Bağımlılıklar: aio-pika (AMQP client), structlog, rabbitmq_config.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

import structlog

from src.infrastructure.config.settings import Settings
from src.infrastructure.messaging.rabbitmq_config import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_PREFETCH_COUNT,
    declare_topology,
)

logger = structlog.get_logger(__name__)


class RabbitMQPublisher:
    """Genel amaçlı RabbitMQ publisher.

    Tek bir AMQP bağlantısı üzerinden birden fazla exchange'e mesaj
    publish eder. Lazy initialization ile bağlantı ilk kullanımda kurulur.

    Özellikler:
      - aio_pika.connect_robust ile otomatik yeniden bağlanma
      - Publisher confirms ile güvenilir teslimat
      - Persistent delivery mode (mesajlar disk'e yazılır)
      - message_id ile idempotent publish
      - Yapılandırılabilir prefetch ve timeout

    Kullanım:
        publisher = RabbitMQPublisher(settings)
        await publisher.publish("domain.events", "event.mission.assigned", body, msg_id)
        await publisher.close()
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._rabbitmq_url = settings.rabbitmq_url
        self._connection: Any = None
        self._channel: Any = None
        self._exchanges: dict[str, Any] = {}
        self._topology_declared = False

    async def _ensure_connection(self) -> None:
        """RabbitMQ bağlantısını sağlar (lazy initialization).

        Mevcut bağlantı açık ise tekrar bağlanmaz.
        Bağlantı kopmuşsa connect_robust otomatik reconnect sağlar.

        Raises:
            ConnectionError: Broker'a bağlantı kurulamadığında.
        """
        if self._connection is not None and not self._connection.is_closed:
            return

        try:
            import aio_pika

            self._connection = await aio_pika.connect_robust(
                self._rabbitmq_url,
                timeout=DEFAULT_CONNECT_TIMEOUT,
            )
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=DEFAULT_PREFETCH_COUNT)

            # Topolojiyi declare et (idempotent)
            if not self._topology_declared:
                await declare_topology(self._channel)
                self._topology_declared = True

            # Exchange cache'ini temizle (yeni channel)
            self._exchanges.clear()

            logger.info("rabbitmq_publisher_connected")

        except Exception as exc:
            logger.error(
                "rabbitmq_publisher_connection_failed",
                error=str(exc),
            )
            self._connection = None
            self._channel = None
            raise ConnectionError(f"RabbitMQ bağlantısı kurulamadı: {type(exc).__name__}") from exc

    async def _get_exchange(self, exchange_name: str) -> Any:
        """Exchange referansını cache'den döner veya alır.

        Args:
            exchange_name: Exchange adı.

        Returns:
            aio-pika Exchange nesnesi.
        """
        if exchange_name not in self._exchanges:
            self._exchanges[exchange_name] = await self._channel.get_exchange(
                exchange_name,
            )
        return self._exchanges[exchange_name]

    async def publish(
        self,
        exchange_name: str,
        routing_key: str,
        body: dict[str, Any],
        message_id: str,
        *,
        headers: Optional[dict[str, Any]] = None,
        content_type: str = "application/json",
        correlation_id: Optional[str] = None,
    ) -> None:
        """Mesajı belirtilen exchange'e publish eder.

        Args:
            exchange_name: Hedef exchange adı.
            routing_key: Mesaj routing key'i.
            body: JSON-serializable mesaj gövdesi.
            message_id: Idempotency için benzersiz mesaj ID.
            headers: Opsiyonel AMQP mesaj header'ları.
            content_type: Mesaj content type (varsayılan: application/json).
            correlation_id: Distributed tracing için correlation ID.

        Raises:
            ConnectionError: Broker bağlantısı yoksa.
            TimeoutError: Publish timeout'u aşılırsa.
        """
        import aio_pika

        start_time = time.monotonic()

        await self._ensure_connection()

        exchange = await self._get_exchange(exchange_name)

        message = aio_pika.Message(
            body=json.dumps(body, default=str).encode("utf-8"),
            content_type=content_type,
            message_id=message_id,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            timestamp=datetime.now(timezone.utc),
            headers=headers or {},
            correlation_id=correlation_id,
        )

        await exchange.publish(message, routing_key=routing_key)

        latency_ms = (time.monotonic() - start_time) * 1000

        logger.info(
            "rabbitmq_message_published",
            exchange=exchange_name,
            routing_key=routing_key,
            message_id=message_id,
            latency_ms=round(latency_ms, 2),
        )

    async def publish_batch(
        self,
        exchange_name: str,
        messages: list[tuple[str, dict[str, Any], str]],
    ) -> None:
        """Birden fazla mesajı sıralı olarak publish eder.

        Args:
            exchange_name: Hedef exchange adı.
            messages: (routing_key, body, message_id) tuple listesi.

        Raises:
            ConnectionError: Broker bağlantısı yoksa.
        """
        start_time = time.monotonic()
        published = 0

        for routing_key, body, message_id in messages:
            await self.publish(exchange_name, routing_key, body, message_id)
            published += 1

        latency_ms = (time.monotonic() - start_time) * 1000

        logger.info(
            "rabbitmq_batch_published",
            exchange=exchange_name,
            count=published,
            latency_ms=round(latency_ms, 2),
        )

    async def health_check(self) -> bool:
        """RabbitMQ bağlantı sağlığını kontrol eder.

        Returns:
            True: Bağlantı sağlıklı.
            False: Bağlantı kopuk veya hatalı.
        """
        try:
            await self._ensure_connection()
            return self._connection is not None and not self._connection.is_closed
        except Exception:
            logger.warning("rabbitmq_publisher_health_check_failed")
            return False

    async def close(self) -> None:
        """RabbitMQ bağlantısını kapatır (graceful shutdown)."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("rabbitmq_publisher_connection_closed")
        self._connection = None
        self._channel = None
        self._exchanges.clear()
