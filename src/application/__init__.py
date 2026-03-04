# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Python paket başlangıcı; modül dışa aktarım (exports) ve namespace düzeni.
Sorumluluk: Python paket başlangıcı; import yüzeyini (public API) düzenler.
Girdi/Çıktı (Contract/DTO/Event): Girdi: method çağrıları. Çıktı: domain nesneleri, domain event’leri (gereken yerde).
Güvenlik (RBAC/PII/Audit): PII minimizasyonu; domain core’da dış dünya erişimi yok; audit gerektiren kararlar üst katmana taşınır.
Hata Modları (idempotency/retry/rate limit): Validation error; invariant violation; concurrency -> üst katmanda 409/Retry stratejisi.
Observability (log fields/metrics/traces): Domain core log tutmaz (tercihen); correlation_id üst katmanda taşınır.
Testler: Unit test (invariants), property-based (opsiyonel), serialization (gerekirse).
Bağımlılıklar: Sadece core/value objects ve standart kütüphane; harici IO bağımlılığı yok.
Notlar/SSOT: KR-015 (kapasite/planlama), KR-018 (kalibrasyon hard gate), KR-033 (payment flow), KR-081 (contract-first) ile tutarlı kalır.
"""

from . import commands, dto, event_handlers, jobs, payments, queries, services, workers

__all__ = [
    "commands",
    "dto",
    "event_handlers",
    "jobs",
    "payments",
    "queries",
    "services",
    "workers",
]
