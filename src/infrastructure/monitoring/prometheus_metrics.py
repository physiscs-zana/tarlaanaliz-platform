# PATH: src/infrastructure/monitoring/prometheus_metrics.py
# DESC: Prometheus metrics adapter.
"""
Prometheus Metrics: uygulama metrik toplama ve export adapter'ı.

Amaç: Platform metriklerini Prometheus formatında toplar ve /metrics
  endpoint'i üzerinden sunar. HTTP istek süreleri, RabbitMQ kuyruk
  derinlikleri, veritabanı bağlantı havuzu, hata oranları ve iş
  mantığı metrikleri izlenir.

Sorumluluk: Metrik tanımlama, toplama, export.

Güvenlik (RBAC/PII/Audit):
  Metrics endpoint'i hassas bilgi döndürmez. PII metrik label'larında
  bulunmaz (sadece aggregate counter/histogram/gauge).

Observability (log fields/metrics/traces):
  Bu dosyanın kendisi observability altyapısıdır.

Testler: Unit test (metrik kayıt doğrulaması).
Bağımlılıklar: prometheus_client, structlog.
Notlar/SSOT: Tek referans: tarlaanaliz_platform_tree v3.2.2 FINAL.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)

# prometheus_client opsiyonel bağımlılık (test ortamında olmayabilir)
try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False


# ------------------------------------------------------------------
# Metrik sabitleri
# ------------------------------------------------------------------
_APP_PREFIX = "tarlaanaliz"

# HTTP istek metrikleri
_HTTP_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

# Kuyruk metrik sabitleri
_QUEUE_OPERATIONS = ("publish", "consume", "reject", "requeue")


class PrometheusMetrics:
    """Prometheus metrik yöneticisi.

    Uygulama metriklerini tanımlar, toplar ve Prometheus formatında
    export eder. Singleton olarak kullanılması önerilir.

    Özellikler:
      - HTTP istek metrikleri (latency, count, errors)
      - RabbitMQ kuyruk metrikleri (publish, consume, depth)
      - Veritabanı bağlantı metrikleri
      - İş mantığı metrikleri (analysis, mission, payment)
      - Prometheus /metrics endpoint desteği

    Kullanım:
        metrics = PrometheusMetrics()
        metrics.http_request_total.labels(method="GET", path="/api/v1/health").inc()
        metrics.http_request_duration.labels(method="GET", path="/api/v1/health").observe(0.05)
    """

    def __init__(
        self,
        *,
        registry: Optional[Any] = None,
        enabled: bool = True,
    ) -> None:
        self._enabled = enabled and _PROMETHEUS_AVAILABLE

        if not self._enabled:
            logger.info("prometheus_metrics_disabled")
            return

        self._registry = registry or CollectorRegistry()

        # ------------------------------------------------------------------
        # HTTP metrikleri
        # ------------------------------------------------------------------
        self.http_request_total = Counter(
            f"{_APP_PREFIX}_http_requests_total",
            "Toplam HTTP istek sayısı",
            labelnames=["method", "path", "status_code"],
            registry=self._registry,
        )

        self.http_request_duration = Histogram(
            f"{_APP_PREFIX}_http_request_duration_seconds",
            "HTTP istek süresi (saniye)",
            labelnames=["method", "path"],
            buckets=_HTTP_BUCKETS,
            registry=self._registry,
        )

        self.http_request_errors = Counter(
            f"{_APP_PREFIX}_http_request_errors_total",
            "Toplam HTTP hata sayısı",
            labelnames=["method", "path", "error_type"],
            registry=self._registry,
        )

        # ------------------------------------------------------------------
        # RabbitMQ metrikleri
        # ------------------------------------------------------------------
        self.rabbitmq_messages_total = Counter(
            f"{_APP_PREFIX}_rabbitmq_messages_total",
            "Toplam RabbitMQ mesaj sayısı",
            labelnames=["operation", "exchange", "routing_key"],
            registry=self._registry,
        )

        self.rabbitmq_message_duration = Histogram(
            f"{_APP_PREFIX}_rabbitmq_message_duration_seconds",
            "RabbitMQ mesaj işlem süresi (saniye)",
            labelnames=["operation", "exchange"],
            buckets=_HTTP_BUCKETS,
            registry=self._registry,
        )

        self.rabbitmq_queue_depth = Gauge(
            f"{_APP_PREFIX}_rabbitmq_queue_depth",
            "RabbitMQ kuyruk derinliği",
            labelnames=["queue_name"],
            registry=self._registry,
        )

        self.rabbitmq_connection_status = Gauge(
            f"{_APP_PREFIX}_rabbitmq_connection_status",
            "RabbitMQ bağlantı durumu (1=bağlı, 0=kopuk)",
            registry=self._registry,
        )

        # ------------------------------------------------------------------
        # Veritabanı metrikleri
        # ------------------------------------------------------------------
        self.db_query_duration = Histogram(
            f"{_APP_PREFIX}_db_query_duration_seconds",
            "Veritabanı sorgu süresi (saniye)",
            labelnames=["query_type"],
            buckets=_HTTP_BUCKETS,
            registry=self._registry,
        )

        self.db_connection_pool_size = Gauge(
            f"{_APP_PREFIX}_db_connection_pool_size",
            "Veritabanı bağlantı havuzu boyutu",
            labelnames=["state"],  # active, idle, total
            registry=self._registry,
        )

        # ------------------------------------------------------------------
        # İş mantığı metrikleri
        # ------------------------------------------------------------------
        self.analysis_jobs_total = Counter(
            f"{_APP_PREFIX}_analysis_jobs_total",
            "Toplam analiz iş sayısı",
            labelnames=["status"],  # requested, completed, failed
            registry=self._registry,
        )

        self.missions_total = Counter(
            f"{_APP_PREFIX}_missions_total",
            "Toplam görev sayısı",
            labelnames=["status"],  # assigned, completed, cancelled
            registry=self._registry,
        )

        self.payments_total = Counter(
            f"{_APP_PREFIX}_payments_total",
            "Toplam ödeme sayısı",
            labelnames=["status", "provider"],
            registry=self._registry,
        )

        self.expert_reviews_total = Counter(
            f"{_APP_PREFIX}_expert_reviews_total",
            "Toplam uzman değerlendirme sayısı",
            labelnames=["status"],  # requested, completed, escalated
            registry=self._registry,
        )

        self.training_feedback_total = Counter(
            f"{_APP_PREFIX}_training_feedback_total",
            "Toplam eğitim geri bildirim sayısı",
            labelnames=["grade"],  # A, B, C, D, REJECT
            registry=self._registry,
        )

        # ------------------------------------------------------------------
        # WebSocket metrikleri
        # ------------------------------------------------------------------
        self.websocket_connections = Gauge(
            f"{_APP_PREFIX}_websocket_connections",
            "Aktif WebSocket bağlantı sayısı",
            registry=self._registry,
        )

        self.websocket_messages_sent = Counter(
            f"{_APP_PREFIX}_websocket_messages_sent_total",
            "Gönderilen WebSocket mesaj sayısı",
            labelnames=["notification_type"],
            registry=self._registry,
        )

        logger.info("prometheus_metrics_initialized")

    def generate_metrics(self) -> bytes:
        """Prometheus formatında metrik çıktısı üret.

        Returns:
            Prometheus text format metrik çıktısı (bytes).
        """
        if not self._enabled:
            return b""
        return generate_latest(self._registry)

    def is_enabled(self) -> bool:
        """Prometheus metrik toplama etkin mi?"""
        return self._enabled


# ------------------------------------------------------------------
# Singleton instance
# ------------------------------------------------------------------
_metrics_instance: Optional[PrometheusMetrics] = None


def get_metrics(*, enabled: bool = True) -> PrometheusMetrics:
    """Singleton PrometheusMetrics instance döner.

    Args:
        enabled: Metrik toplama etkin mi?

    Returns:
        PrometheusMetrics instance.
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics(enabled=enabled)
    return _metrics_instance
