# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-070: RabbitMQ message consumer with retry and DLQ.
# PATH: src/infrastructure/messaging/rabbitmq/consumer.py
# DESC: RabbitMQ consumer adapter.
"""
RabbitMQ Consumer: mesaj tüketme ve handler dispatch adapter'ı.

Amaç: RabbitMQ kuyruklarından mesaj consume etmek, deserialize etmek
  ve kayıtlı handler'lara dispatch etmek. EventBus subscribe/consume
  mekanizmasının altyapı implementasyonu.

Sorumluluk: Event bus ve kuyruk altyapısı implementasyonu; consume ve dayanıklılık.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: RabbitMQ kuyruk mesajları (JSON body).
  Çıktı: Handler çağrıları, ACK/NACK/requeue kararları.

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: mesaj payload'larında PII loglanmaz.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve DLQ (dead letter queue). message_id ile dedup.

Observability (log fields/metrics/traces):
  latency, error_code, retries, queue_depth, event_type, message_id.

Testler: Contract test (port), integration test (RabbitMQ stub), e2e (kritik akış).
Bağımlılıklar: aio-pika (AMQP client), structlog, rabbitmq_config.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Awaitable, Callable, Optional

import structlog

from src.infrastructure.config.settings import Settings
from src.infrastructure.messaging.rabbitmq_config import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_PREFETCH_COUNT,
    MAX_RETRY_ATTEMPTS,
    declare_topology,
)

logger = structlog.get_logger(__name__)

# Handler tipi: mesaj body dict'i alır, None döner
MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]


class RabbitMQConsumer:
    """Genel amaçlı RabbitMQ consumer.

    Belirtilen kuyrukları dinler, gelen mesajları deserialize eder
    ve kayıtlı handler'lara dispatch eder.

    Özellikler:
      - aio_pika.connect_robust ile otomatik yeniden bağlanma
      - Prefetch (QoS) ile akış kontrolü
      - message_id bazlı idempotency (dedup cache)
      - Başarısız mesajlar için retry + DLQ
      - Graceful shutdown desteği

    Kullanım:
        consumer = RabbitMQConsumer(settings)
        sub_id = await consumer.subscribe("domain.events.general", handler)
        await consumer.start_consuming()
        # ...
        await consumer.unsubscribe(sub_id)
        await consumer.close()
    """

    def __init__(
        self,
        settings: Settings,
        *,
        prefetch_count: int = DEFAULT_PREFETCH_COUNT,
        max_retry_attempts: int = MAX_RETRY_ATTEMPTS,
    ) -> None:
        self._settings = settings
        self._rabbitmq_url = settings.rabbitmq_url
        self._prefetch_count = prefetch_count
        self._max_retry_attempts = max_retry_attempts
        self._connection: Any = None
        self._channel: Any = None
        self._topology_declared = False

        # subscription_id -> (queue_name, handler, consumer_tag)
        self._subscriptions: dict[str, tuple[str, MessageHandler, Optional[str]]] = {}

        # Idempotency dedup cache: son N mesaj ID'si
        self._processed_ids: set[str] = set()
        self._max_dedup_size = 10_000

        # Consuming state
        self._consuming = False

    async def _ensure_connection(self) -> None:
        """RabbitMQ bağlantısını sağlar (lazy initialization).

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
            await self._channel.set_qos(prefetch_count=self._prefetch_count)

            if not self._topology_declared:
                await declare_topology(self._channel)
                self._topology_declared = True

            logger.info("rabbitmq_consumer_connected")

        except Exception as exc:
            logger.error(
                "rabbitmq_consumer_connection_failed",
                error=str(exc),
            )
            self._connection = None
            self._channel = None
            raise ConnectionError(f"RabbitMQ bağlantısı kurulamadı: {type(exc).__name__}") from exc

    def _is_duplicate(self, message_id: str) -> bool:
        """Mesaj daha önce işlendi mi kontrol et (idempotency).

        Args:
            message_id: Kontrol edilecek mesaj ID.

        Returns:
            True: Duplicate mesaj.
            False: Yeni mesaj.
        """
        if message_id in self._processed_ids:
            return True

        # Cache boyut kontrolü
        if len(self._processed_ids) >= self._max_dedup_size:
            # En eski %20'sini kaldır (basit eviction)
            evict_count = self._max_dedup_size // 5
            for _ in range(evict_count):
                self._processed_ids.pop()

        self._processed_ids.add(message_id)
        return False

    async def subscribe(
        self,
        queue_name: str,
        handler: MessageHandler,
        *,
        group_id: Optional[str] = None,
    ) -> str:
        """Belirtilen kuyruğa handler kaydet.

        Args:
            queue_name: Dinlenecek kuyruk adı.
            handler: Async handler fonksiyonu (dict alır, None döner).
            group_id: Consumer group ID (opsiyonel; load balancing için).

        Returns:
            Subscription ID (unsubscribe için kullanılır).
        """
        subscription_id = f"sub-{uuid.uuid4().hex[:12]}"

        self._subscriptions[subscription_id] = (queue_name, handler, None)

        logger.info(
            "rabbitmq_consumer_subscribed",
            subscription_id=subscription_id,
            queue_name=queue_name,
            group_id=group_id,
        )

        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """Event dinlemeyi durdur.

        Args:
            subscription_id: subscribe'dan dönen subscription ID.

        Raises:
            KeyError: subscription_id bulunamadığında.
        """
        if subscription_id not in self._subscriptions:
            raise KeyError(f"Subscription bulunamadı: {subscription_id}")

        queue_name, _handler, consumer_tag = self._subscriptions[subscription_id]

        if consumer_tag and self._channel:
            try:
                queue = await self._channel.get_queue(queue_name)
                await queue.cancel(consumer_tag)
            except Exception as exc:
                logger.warning(
                    "rabbitmq_consumer_cancel_failed",
                    subscription_id=subscription_id,
                    error=str(exc),
                )

        del self._subscriptions[subscription_id]

        logger.info(
            "rabbitmq_consumer_unsubscribed",
            subscription_id=subscription_id,
            queue_name=queue_name,
        )

    async def start_consuming(self) -> None:
        """Tüm kayıtlı kuyrukları dinlemeye başla.

        Her subscription için aio-pika consumer başlatır.
        Bu metod non-blocking'tir; consume işlemi arka planda devam eder.
        """
        await self._ensure_connection()

        self._consuming = True

        for sub_id, (queue_name, handler, _tag) in self._subscriptions.items():
            queue = await self._channel.get_queue(queue_name)

            consumer_tag = await queue.consume(
                callback=self._make_callback(sub_id, handler),
            )

            self._subscriptions[sub_id] = (queue_name, handler, consumer_tag)

            logger.info(
                "rabbitmq_consumer_started",
                subscription_id=sub_id,
                queue_name=queue_name,
                consumer_tag=consumer_tag,
            )

    def _make_callback(
        self,
        subscription_id: str,
        handler: MessageHandler,
    ) -> Callable[..., Awaitable[None]]:
        """Her subscription için aio-pika callback oluşturur.

        Args:
            subscription_id: Subscription ID (loglama için).
            handler: Asıl iş mantığı handler'ı.

        Returns:
            aio-pika IncomingMessage callback fonksiyonu.
        """

        async def _on_message(message: Any) -> None:
            start_time = time.monotonic()
            message_id = message.message_id or str(uuid.uuid4())

            # Idempotency kontrolü
            if self._is_duplicate(message_id):
                logger.warning(
                    "rabbitmq_consumer_duplicate_message",
                    message_id=message_id,
                    subscription_id=subscription_id,
                )
                await message.ack()
                return

            try:
                body = json.loads(message.body.decode("utf-8"))

                # SEC-FIX: Temel message yapısı doğrulama — injection/malformed önleme
                if not isinstance(body, dict):
                    raise ValueError("Message body must be a JSON object")
                event_type = body.get("event_type")
                if not isinstance(event_type, str) or not event_type:
                    raise ValueError("Missing or invalid event_type field")

                logger.debug(
                    "rabbitmq_consumer_message_received",
                    message_id=message_id,
                    subscription_id=subscription_id,
                    event_type=event_type,
                )

                await handler(body)

                await message.ack()

                latency_ms = (time.monotonic() - start_time) * 1000
                logger.info(
                    "rabbitmq_consumer_message_processed",
                    message_id=message_id,
                    subscription_id=subscription_id,
                    event_type=body.get("event_type", "unknown"),
                    latency_ms=round(latency_ms, 2),
                )

            except json.JSONDecodeError as exc:
                logger.error(
                    "rabbitmq_consumer_invalid_json",
                    message_id=message_id,
                    error=str(exc),
                )
                # Geçersiz JSON tekrar denenirse de başarısız olur -> reject
                await message.reject(requeue=False)

            except Exception as exc:
                latency_ms = (time.monotonic() - start_time) * 1000

                # Retry sayısını kontrol et
                retry_count = (message.headers or {}).get("x-retry-count", 0)

                if retry_count < self._max_retry_attempts:
                    logger.warning(
                        "rabbitmq_consumer_message_requeued",
                        message_id=message_id,
                        subscription_id=subscription_id,
                        error=str(exc),
                        retry_count=retry_count,
                        latency_ms=round(latency_ms, 2),
                    )
                    # Exponential backoff delay
                    delay = min(2**retry_count, 30)
                    await asyncio.sleep(delay)

                    # Republish with incremented x-retry-count instead of
                    # bare nack(requeue=True) which preserves old headers
                    # and causes an infinite retry loop.
                    import aio_pika

                    updated_headers = dict(message.headers or {})
                    updated_headers["x-retry-count"] = retry_count + 1

                    republish_msg = aio_pika.Message(
                        body=message.body,
                        headers=updated_headers,
                        message_id=message_id,
                        content_type=message.content_type,
                        delivery_mode=message.delivery_mode,
                    )

                    exchange = await self._channel.get_exchange(
                        message.exchange or "",
                    )
                    await exchange.publish(
                        republish_msg,
                        routing_key=message.routing_key or "",
                    )
                    await message.ack()
                else:
                    logger.error(
                        "rabbitmq_consumer_message_rejected",
                        message_id=message_id,
                        subscription_id=subscription_id,
                        error=str(exc),
                        retry_count=retry_count,
                        latency_ms=round(latency_ms, 2),
                    )
                    # DLQ'ya gönder (reject + requeue=False -> DLX)
                    await message.reject(requeue=False)

                # Dedup cache'den kaldır (retry'a izin ver)
                self._processed_ids.discard(message_id)

        return _on_message

    async def health_check(self) -> bool:
        """RabbitMQ consumer bağlantı sağlığını kontrol eder.

        Returns:
            True: Bağlantı sağlıklı.
            False: Bağlantı kopuk veya hatalı.
        """
        try:
            await self._ensure_connection()
            return self._connection is not None and not self._connection.is_closed
        except Exception:
            logger.warning("rabbitmq_consumer_health_check_failed")
            return False

    async def close(self) -> None:
        """RabbitMQ bağlantısını kapatır (graceful shutdown).

        Aktif consumer'ları durdurur, bekleyen mesajları requeue eder.
        """
        self._consuming = False

        # Tüm consumer'ları durdur
        for sub_id in list(self._subscriptions.keys()):
            try:
                await self.unsubscribe(sub_id)
            except Exception as exc:
                logger.warning(
                    "rabbitmq_consumer_close_error",
                    subscription_id=sub_id,
                    error=str(exc),
                )

        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("rabbitmq_consumer_connection_closed")

        self._connection = None
        self._channel = None
        self._processed_ids.clear()
