# PATH: src/infrastructure/messaging/rabbitmq_event_bus_impl.py
# DESC: EventBus portunun RabbitMQ implementasyonu.
"""
RabbitMQ EventBus: core EventBus portunun RabbitMQ implementasyonu.

Amaç: EventBus soyut sınıfının tam implementasyonunu sağlar. Publisher ve
  Consumer adapter'larını compose ederek publish/subscribe mekanizmasını
  RabbitMQ üzerinde gerçekleştirir.

Sorumluluk: Event bus ve kuyruk altyapısı implementasyonu; publish/consume ve dayanıklılık.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (DomainEvent publish, EventHandler subscribe).
  Çıktı: IO sonuçları (event broker'a gönderim, handler tetikleme).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: event payload'larında PII bulunmaz.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve DLQ. event_id ile dedup.

Observability (log fields/metrics/traces):
  latency, error_code, retries, queue_depth, event_type, message_id.

Testler: Contract test (port), integration test (RabbitMQ stub), e2e (kritik akış).
Bağımlılıklar: RabbitMQPublisher, RabbitMQConsumer, structlog, domain events.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Awaitable, Callable, Optional

import structlog

from src.core.domain.events.base import DomainEvent
from src.core.ports.messaging.event_bus import EventBus, EventHandler
from src.infrastructure.config.settings import Settings
from src.infrastructure.messaging.event_publisher import EventPublisher
from src.infrastructure.messaging.rabbitmq.consumer import RabbitMQConsumer
from src.infrastructure.messaging.rabbitmq_config import DOMAIN_EVENTS_QUEUE

logger = structlog.get_logger(__name__)


class RabbitMQEventBus(EventBus):
    """EventBus portunun RabbitMQ implementasyonu.

    Publisher ve Consumer adapter'larını compose ederek tam bir
    publish/subscribe mekanizması sağlar.

    Özellikler:
      - event_type bazlı routing (topic exchange)
      - event_id ile idempotent publish/consume
      - Consumer group desteği (competing consumers)
      - DLQ ile başarısız event yönetimi
      - Graceful connect/disconnect lifecycle

    Kuyruk topolojisi:
      Exchange: domain.events (topic, durable)
      Exchange: training.feedback (topic, durable)
      Queue: domain.events.general (tüm event'ler)
      Queue: domain.events.analysis (analiz event'leri)
      Queue: domain.events.mission (görev event'leri)
      Queue: domain.events.payment (ödeme event'leri)
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._event_publisher = EventPublisher(settings)
        self._consumer = RabbitMQConsumer(settings)

        # event_type -> handler listesi (local dispatch)
        self._handlers: dict[str, list[tuple[str, EventHandler]]] = {}

        # subscription_id -> (event_type, consumer_sub_id)
        self._subscriptions: dict[str, tuple[str, Optional[str]]] = {}

        self._connected = False

    # ------------------------------------------------------------------
    # Publish
    # ------------------------------------------------------------------
    async def publish(self, event: DomainEvent) -> None:
        """Tek bir domain event'i yayınla.

        Event, event_type property'sine göre ilgili exchange/topic'e
        yönlendirilir. event_id ile idempotency sağlanır.

        Args:
            event: Yayınlanacak domain event'i.

        Raises:
            TimeoutError: Broker yanıt vermediğinde.
            ConnectionError: Broker'a bağlantı kurulamadığında.
        """
        await self._event_publisher.publish(event)

    # ------------------------------------------------------------------
    # Toplu publish
    # ------------------------------------------------------------------
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Birden fazla event'i toplu yayınla.

        Sıralama korunur.

        Args:
            events: Yayınlanacak event listesi (sıralı).

        Raises:
            TimeoutError: Broker yanıt vermediğinde.
            ConnectionError: Broker'a bağlantı kurulamadığında.
        """
        await self._event_publisher.publish_batch(events)

    # ------------------------------------------------------------------
    # Subscribe
    # ------------------------------------------------------------------
    async def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        *,
        group_id: Optional[str] = None,
    ) -> str:
        """Belirli bir event tipine handler kaydet.

        Her event_type için birden fazla handler kaydedilebilir.
        group_id ile competing consumers pattern desteklenir.

        Args:
            event_type: Dinlenecek event tipi (sınıf adı, ör: 'MissionAssigned').
            handler: Async handler fonksiyonu.
            group_id: Consumer group ID (opsiyonel; load balancing için).

        Returns:
            str: Subscription ID (unsubscribe için kullanılır).

        Raises:
            ValueError: Geçersiz event_type.
        """
        if not event_type or not event_type.strip():
            raise ValueError("event_type boş olamaz.")

        subscription_id = f"ebus-{uuid.uuid4().hex[:12]}"

        # Handler'ı event_type listesine ekle
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append((subscription_id, handler))

        # Consumer'a dispatcher callback kaydet (ilk subscription'da)
        consumer_sub_id: Optional[str] = None
        if self._connected:
            consumer_sub_id = await self._consumer.subscribe(
                queue_name=DOMAIN_EVENTS_QUEUE,
                handler=self._make_dispatcher(),
                group_id=group_id,
            )

        self._subscriptions[subscription_id] = (event_type, consumer_sub_id)

        logger.info(
            "event_bus_subscribed",
            subscription_id=subscription_id,
            event_type=event_type,
            group_id=group_id,
        )

        return subscription_id

    # ------------------------------------------------------------------
    # Unsubscribe
    # ------------------------------------------------------------------
    async def unsubscribe(self, subscription_id: str) -> None:
        """Event dinlemeyi durdur.

        Args:
            subscription_id: subscribe'dan dönen subscription ID.

        Raises:
            KeyError: subscription_id bulunamadığında.
        """
        if subscription_id not in self._subscriptions:
            raise KeyError(f"Subscription bulunamadı: {subscription_id}")

        event_type, consumer_sub_id = self._subscriptions[subscription_id]

        # Handler listesinden kaldır
        if event_type in self._handlers:
            self._handlers[event_type] = [(sid, h) for sid, h in self._handlers[event_type] if sid != subscription_id]
            if not self._handlers[event_type]:
                del self._handlers[event_type]

        # Consumer subscription'ı kaldır
        if consumer_sub_id:
            try:
                await self._consumer.unsubscribe(consumer_sub_id)
            except KeyError:
                pass

        del self._subscriptions[subscription_id]

        logger.info(
            "event_bus_unsubscribed",
            subscription_id=subscription_id,
            event_type=event_type,
        )

    # ------------------------------------------------------------------
    # Bağlantı yaşam döngüsü
    # ------------------------------------------------------------------
    async def connect(self) -> None:
        """Broker'a bağlan.

        Publisher ve consumer bağlantılarını başlatır.
        Genel dispatch kuyruğunu dinlemeye başlar.

        Raises:
            ConnectionError: Bağlantı kurulamadığında.
        """
        if self._connected:
            return

        # Genel domain events kuyruğuna dispatcher kaydet
        await self._consumer.subscribe(
            queue_name=DOMAIN_EVENTS_QUEUE,
            handler=self._make_dispatcher(),
        )

        # Consumer'ı başlat
        await self._consumer.start_consuming()

        self._connected = True
        logger.info("event_bus_connected")

    async def disconnect(self) -> None:
        """Broker bağlantısını kapat.

        Graceful shutdown: bekleyen mesajlar tamamlanır veya requeue edilir.
        """
        self._connected = False

        await self._consumer.close()
        await self._event_publisher.close()

        self._handlers.clear()
        self._subscriptions.clear()

        logger.info("event_bus_disconnected")

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        """Broker'ın erişilebilirliğini kontrol et.

        Returns:
            True: Broker sağlıklı ve erişilebilir.
            False: Broker erişilemez veya hata durumunda.
        """
        publisher_ok = await self._event_publisher.health_check()
        consumer_ok = await self._consumer.health_check()
        return publisher_ok and consumer_ok

    # ------------------------------------------------------------------
    # Internal: event dispatcher
    # ------------------------------------------------------------------
    def _make_dispatcher(self) -> Callable[[dict[str, Any]], Awaitable[None]]:
        """RabbitMQ mesajını event_type'a göre handler'lara dispatch eden callback.

        Returns:
            MessageHandler callback fonksiyonu.
        """

        async def _dispatch(body: dict[str, Any]) -> None:
            event_type = body.get("event_type")
            if not event_type:
                logger.warning(
                    "event_bus_missing_event_type",
                    body_keys=list(body.keys()),
                )
                return

            handlers = self._handlers.get(event_type, [])
            if not handlers:
                logger.debug(
                    "event_bus_no_handlers",
                    event_type=event_type,
                )
                return

            for sub_id, handler in handlers:
                try:
                    await handler(body)  # type: ignore[arg-type]
                    logger.debug(
                        "event_bus_handler_invoked",
                        event_type=event_type,
                        subscription_id=sub_id,
                    )
                except Exception as exc:
                    logger.error(
                        "event_bus_handler_error",
                        event_type=event_type,
                        subscription_id=sub_id,
                        error=str(exc),
                    )
                    raise

        return _dispatch
