# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-081: Contract-first schema validation is enforced before orchestration.
# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Contract-first (KR-081) JSON Schema doğrulaması.
Sorumluluk: Use-case orkestrasyonu; domain service + ports birleşimi; policy enforcement.
Girdi/Çıktı (Contract/DTO/Event): Girdi: API/Job/Worker tetiklemesi. Çıktı: DTO, event, state transition.
Güvenlik (RBAC/PII/Audit): RBAC burada; PII redaction; audit log; rate limit (gereken yerde).
Hata Modları (idempotency/retry/rate limit): 400/403/409/429/5xx mapping; retry-safe tasarım; idempotency key/hard gate’ler.
Observability (log fields/metrics/traces): correlation_id, latency, error_code; use-case metric sayaçları.
Testler: Unit + integration; kritik akış için e2e (özellikle ödeme/planlama/kalibrasyon).
Bağımlılıklar: Domain + ports + infra implementasyonları + event bus.
Notlar/SSOT: Contract-first (KR-081) ve kritik kapılar (KR-018/KR-033/KR-015) application katmanında enforce edilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class SchemaRegistry(Protocol):
    def get_schema(self, schema_id: str) -> dict[str, Any]: ...


class ContractValidationError(ValueError):
    def __init__(self, message: str, *, schema_id: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.schema_id = schema_id
        self.details = details or {}


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    schema_id: str
    error: ContractValidationError | None = None


class ContractValidatorService:
    def __init__(self, registry: SchemaRegistry) -> None:
        self._registry = registry

    def validate(self, *, schema_id: str, payload: Any, correlation_id: str) -> ValidationResult:
        _ = correlation_id
        schema = self._registry.get_schema(schema_id)
        try:
            import jsonschema
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("jsonschema dependency is required for KR-081 validation") from exc

        try:
            jsonschema.validate(instance=payload, schema=schema)
            return ValidationResult(ok=True, schema_id=schema_id)
        except jsonschema.ValidationError as exc:
            error = ContractValidationError(
                "Contract validation failed",
                schema_id=schema_id,
                details={"message": str(exc), "path": list(exc.path), "schema_path": list(exc.schema_path)},
            )
            return ValidationResult(ok=False, schema_id=schema_id, error=error)
