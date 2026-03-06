# PATH: src/core/ports/messaging/event_bus.py
# DESC: EventBus portu: event publish/subscribe mekanizması.
# SSOT: Tüm domain event'leri (KR-015, KR-017, KR-019, KR-033)
"""
EventBus portu: event publish/subscribe mekanizması.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  Domain event'lerinin publish ve subscribe mekanizmasını soyutlar.
  Application katmanı event handler'ları bu port üzerinden kayıt olur.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (DomainEvent publish, handler subscribe).
  Çıktı: IO sonuçları (event broker'a gönderim, handler tetikleme).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: event payload'larında PII bulunmaz (domain event tasarım kuralı).

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). Dead letter queue destekli.

Observability (log fields/metrics/traces):
  latency, error_code, retries, queue depth, event_type, correlation_id.

Testler: Contract test (port), integration test (broker stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional

from src.core.domain.events.base import DomainEvent


# ------------------------------------------------------------------
# Type aliases
# ------------------------------------------------------------------
EventHandler = Callable[[DomainEvent], Awaitable[None]]
"""Async event handler fonksiyonu tipi.

Her handler tek bir DomainEvent alır ve None döner.
Hata durumunda exception fırlatır (EventBus impl retry/DLQ yönetir).
"""


# ------------------------------------------------------------------
# Port Interface
# ------------------------------------------------------------------
class EventBus(ABC):
    """Event Bus portu.

    Domain event'lerinin publish/subscribe mekanizmasını soyutlar.
    Tüm domain event'leri DomainEvent taban sınıfından türer ve
    event_type property'si ile routing yapılır.

    Infrastructure katmanı bu interface'i implemente eder:
      - RabbitMQ (AMQP) tabanlı event bus
      - Redis Streams tabanlı event bus
      - In-memory event bus (test/dev)

    Idempotency: event_id (UUID) ile duplicate tespit edilir.
    Retry: Consumer tarafında exponential backoff ile yeniden denenir.
    Dead Letter Queue: Başarısız event'ler DLQ'ya yönlendirilir.
    Ordering: Aynı aggregate_id için sıralı teslim garanti edilir (best-effort).
    """

    # ------------------------------------------------------------------
    # Publish
    # ------------------------------------------------------------------
    @abstractmethod
    async def publish(
        self,
        event: DomainEvent,
    ) -> None:
        """Tek bir domain event'i yayınla.

        Event, event_type property'sine göre ilgili exchange/topic'e
        yönlendirilir. event_id ile idempotency sağlanır.

        Args:
            event: Yayınlanacak domain event'i.

        Raises:
            TimeoutError: Broker yanıt vermediğinde.
            ConnectionError: Broker'a bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Toplu publish
    # ------------------------------------------------------------------
    @abstractmethod
    async def publish_batch(
        self,
        events: list[DomainEvent],
    ) -> None:
        """Birden fazla event'i toplu yayınla.

        Mümkünse atomik olarak gönderilir (broker desteğine bağlı).
        Sıralama korunur.

        Args:
            events: Yayınlanacak event listesi (sıralı).

        Raises:
            TimeoutError: Broker yanıt vermediğinde.
            ConnectionError: Broker'a bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Subscribe
    # ------------------------------------------------------------------
    @abstractmethod
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

    # ------------------------------------------------------------------
    # Unsubscribe
    # ------------------------------------------------------------------
    @abstractmethod
    async def unsubscribe(
        self,
        subscription_id: str,
    ) -> None:
        """Event dinlemeyi durdur.

        Args:
            subscription_id: subscribe'dan dönen subscription ID.

        Raises:
            KeyError: subscription_id bulunamadığında.
        """

    # ------------------------------------------------------------------
    # Bağlantı yaşam döngüsü
    # ------------------------------------------------------------------
    @abstractmethod
    async def connect(self) -> None:
        """Broker'a bağlan.

        Uygulama başlangıcında çağrılır.

        Raises:
            ConnectionError: Bağlantı kurulamadığında.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Broker bağlantısını kapat.

        Uygulama kapanışında çağrılır. Graceful shutdown.
        Bekleyen mesajlar tamamlanır veya requeue edilir.
        """

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    @abstractmethod
    async def health_check(self) -> bool:
        """Broker'ın erişilebilirliğini kontrol et.

        Returns:
            True: Broker sağlıklı ve erişilebilir.
            False: Broker erişilemez veya hata durumunda.
        """
