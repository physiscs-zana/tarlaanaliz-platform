# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: locustfile.py dosyasının rolünü tanımlar.
Sorumluluk: Bağlamına göre beklenen sorumlulukları yerine getirir; SSOT v1.0.0 ile uyumlu kalır.
Girdi/Çıktı (Contract/DTO/Event): N/A
Güvenlik (RBAC/PII/Audit): N/A
Hata Modları (idempotency/retry/rate limit): N/A
Observability (log fields/metrics/traces): N/A
Testler: N/A
Bağımlılıklar: N/A
Notlar/SSOT: Tek referans: SSOT v1.0.0. Aynı kavram başka yerde tekrar edilmez.
"""

from __future__ import annotations

try:
    from locust import HttpUser, between, task
except Exception:  # pragma: no cover - optional dependency

    class HttpUser:  # type: ignore[no-redef]
        pass

    def task(*_args, **_kwargs):  # type: ignore[no-redef]
        def _decorator(func):
            return func

        return _decorator

    def between(_a: int, _b: int):  # type: ignore[no-redef]
        return None


class PlatformUser(HttpUser):
    """KR-081 contract smoke traffic; disabled unless Locust is installed."""

    wait_time = between(1, 2)

    @task
    def health(self) -> None:
        client = getattr(self, "client", None)
        if client is not None:
            client.get("/health", name="health")
