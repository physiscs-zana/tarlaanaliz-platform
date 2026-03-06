# PATH: src/infrastructure/messaging/rabbitmq_config.py
# DESC: RabbitMQ bağlantı ve topoloji konfigürasyonu.
"""
RabbitMQ Konfigürasyonu: exchange, kuyruk ve bağlantı parametreleri.

Amaç: RabbitMQ topoloji tanımlarını (exchange, queue, routing key, DLX)
  merkezi bir yerde toplar. Tüm publisher/consumer adapter'ları bu
  konfigürasyonu kullanır.

Sorumluluk: Event bus ve kuyruk altyapısı konfigürasyonu; topoloji SSOT.

Güvenlik (RBAC/PII/Audit):
  Secret'lar env/secret manager üzerinden Settings'ten alınır.
  Bu dosyada secret barındırılmaz.

Hata Modları (idempotency/retry/rate limit):
  Exchange ve queue declare işlemleri idempotent'tir.

Observability (log fields/metrics/traces):
  Topoloji değişiklikleri structlog ile loglanır.

Testler: Unit test (config doğrulaması).
Bağımlılıklar: aio-pika, Settings.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ------------------------------------------------------------------
# Exchange sabitleri
# ------------------------------------------------------------------
DOMAIN_EVENTS_EXCHANGE = "domain.events"
TRAINING_FEEDBACK_EXCHANGE = "training.feedback"
NOTIFICATION_EXCHANGE = "notifications"

# Dead letter exchange suffix
DLX_SUFFIX = ".dlx"


# ------------------------------------------------------------------
# Queue sabitleri
# ------------------------------------------------------------------
# Domain event kuyrukları
DOMAIN_EVENTS_QUEUE = "domain.events.general"
ANALYSIS_EVENTS_QUEUE = "domain.events.analysis"
MISSION_EVENTS_QUEUE = "domain.events.mission"
PAYMENT_EVENTS_QUEUE = "domain.events.payment"

# Training feedback kuyrukları
TRAINING_FEEDBACK_SUBMIT_QUEUE = "training.feedback.submit"
TRAINING_FEEDBACK_EXPORT_QUEUE = "training.feedback.export"

# Notification kuyrukları
NOTIFICATION_EXPERT_QUEUE = "notifications.expert"

# ------------------------------------------------------------------
# Routing key sabitleri
# ------------------------------------------------------------------
ANALYSIS_ROUTING_KEY = "event.analysis.#"
MISSION_ROUTING_KEY = "event.mission.#"
PAYMENT_ROUTING_KEY = "event.payment.#"
TRAINING_SUBMIT_ROUTING_KEY = "feedback.submit"
TRAINING_EXPORT_ROUTING_KEY = "feedback.export"
NOTIFICATION_ROUTING_KEY = "notification.#"

# ------------------------------------------------------------------
# Varsayılan parametreler
# ------------------------------------------------------------------
DEFAULT_MESSAGE_TTL_MS = 86_400_000  # 24 saat
DEFAULT_PREFETCH_COUNT = 10
DEFAULT_CONNECT_TIMEOUT = 10  # saniye
DEFAULT_HEARTBEAT = 60  # saniye
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_MULTIPLIER = 1
RETRY_MIN_WAIT = 1  # saniye
RETRY_MAX_WAIT = 10  # saniye


@dataclass(frozen=True)
class QueueConfig:
    """Tek bir kuyruk konfigürasyonu.

    Durable, TTL, DLX ve diğer AMQP kuyruk parametrelerini taşır.
    """

    name: str
    routing_key: str
    durable: bool = True
    message_ttl_ms: int = DEFAULT_MESSAGE_TTL_MS
    dead_letter_exchange: str = ""
    extra_arguments: dict[str, Any] = field(default_factory=dict)

    @property
    def arguments(self) -> dict[str, Any]:
        """AMQP declare_queue arguments parametresi."""
        args: dict[str, Any] = {}
        if self.message_ttl_ms > 0:
            args["x-message-ttl"] = self.message_ttl_ms
        if self.dead_letter_exchange:
            args["x-dead-letter-exchange"] = self.dead_letter_exchange
        args.update(self.extra_arguments)
        return args


@dataclass(frozen=True)
class ExchangeConfig:
    """Tek bir exchange konfigürasyonu."""

    name: str
    exchange_type: str = "topic"  # topic | direct | fanout | headers
    durable: bool = True
    queues: list[QueueConfig] = field(default_factory=list)


def get_default_topology() -> list[ExchangeConfig]:
    """Platform varsayılan RabbitMQ topolojisini döner.

    Returns:
        Exchange ve kuyruk tanımları listesi.
    """
    return [
        # -- Domain Events Exchange --
        ExchangeConfig(
            name=DOMAIN_EVENTS_EXCHANGE,
            exchange_type="topic",
            durable=True,
            queues=[
                QueueConfig(
                    name=DOMAIN_EVENTS_QUEUE,
                    routing_key="event.#",
                    dead_letter_exchange=f"{DOMAIN_EVENTS_EXCHANGE}{DLX_SUFFIX}",
                ),
                QueueConfig(
                    name=ANALYSIS_EVENTS_QUEUE,
                    routing_key=ANALYSIS_ROUTING_KEY,
                    dead_letter_exchange=f"{DOMAIN_EVENTS_EXCHANGE}{DLX_SUFFIX}",
                ),
                QueueConfig(
                    name=MISSION_EVENTS_QUEUE,
                    routing_key=MISSION_ROUTING_KEY,
                    dead_letter_exchange=f"{DOMAIN_EVENTS_EXCHANGE}{DLX_SUFFIX}",
                ),
                QueueConfig(
                    name=PAYMENT_EVENTS_QUEUE,
                    routing_key=PAYMENT_ROUTING_KEY,
                    dead_letter_exchange=f"{DOMAIN_EVENTS_EXCHANGE}{DLX_SUFFIX}",
                ),
            ],
        ),
        # -- Training Feedback Exchange --
        ExchangeConfig(
            name=TRAINING_FEEDBACK_EXCHANGE,
            exchange_type="topic",
            durable=True,
            queues=[
                QueueConfig(
                    name=TRAINING_FEEDBACK_SUBMIT_QUEUE,
                    routing_key=TRAINING_SUBMIT_ROUTING_KEY,
                    dead_letter_exchange=f"{TRAINING_FEEDBACK_EXCHANGE}{DLX_SUFFIX}",
                ),
                QueueConfig(
                    name=TRAINING_FEEDBACK_EXPORT_QUEUE,
                    routing_key=TRAINING_EXPORT_ROUTING_KEY,
                ),
            ],
        ),
        # -- Notification Exchange --
        ExchangeConfig(
            name=NOTIFICATION_EXCHANGE,
            exchange_type="topic",
            durable=True,
            queues=[
                QueueConfig(
                    name=NOTIFICATION_EXPERT_QUEUE,
                    routing_key=NOTIFICATION_ROUTING_KEY,
                ),
            ],
        ),
    ]


async def declare_topology(channel: Any) -> None:
    """Tüm exchange ve kuyrukları RabbitMQ üzerinde declare eder.

    Idempotent: mevcut tanımları bozmaz; eksik olanları oluşturur.

    Args:
        channel: aio-pika channel nesnesi.
    """
    import aio_pika

    topology = get_default_topology()

    exchange_type_map = {
        "topic": aio_pika.ExchangeType.TOPIC,
        "direct": aio_pika.ExchangeType.DIRECT,
        "fanout": aio_pika.ExchangeType.FANOUT,
        "headers": aio_pika.ExchangeType.HEADERS,
    }

    for exchange_config in topology:
        # DLX exchange oluştur
        dlx_name = f"{exchange_config.name}{DLX_SUFFIX}"
        await channel.declare_exchange(
            dlx_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Ana exchange oluştur
        ex_type = exchange_type_map.get(
            exchange_config.exchange_type,
            aio_pika.ExchangeType.TOPIC,
        )
        exchange = await channel.declare_exchange(
            exchange_config.name,
            ex_type,
            durable=exchange_config.durable,
        )

        # Kuyrukları oluştur ve bağla
        for queue_config in exchange_config.queues:
            queue = await channel.declare_queue(
                queue_config.name,
                durable=queue_config.durable,
                arguments=queue_config.arguments,
            )
            await queue.bind(exchange, queue_config.routing_key)

        logger.info(
            "rabbitmq_topology_declared",
            exchange=exchange_config.name,
            queue_count=len(exchange_config.queues),
        )
