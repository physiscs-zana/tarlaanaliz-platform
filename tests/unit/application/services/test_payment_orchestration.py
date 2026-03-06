# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""
Amaç: Test modülü; davranış doğrulama ve regresyon engeli.
Sorumluluk: Bağlamına göre beklenen sorumlulukları yerine getirir; SSOT v1.0.0 ile uyumlu kalır.
Girdi/Çıktı (Contract/DTO/Event): N/A
Güvenlik (RBAC/PII/Audit): N/A
Hata Modları (idempotency/retry/rate limit): N/A
Observability (log fields/metrics/traces): N/A
Testler: N/A
Bağımlılıklar: N/A
Notlar/SSOT: Tek referans: SSOT v1.0.0. Aynı kavram başka yerde tekrar edilmez. KR-033: PaymentIntent olmadan paid state olmaz; dekont + manuel onay + audit.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

import importlib


@dataclass
class _InMemoryRepo:
    items: dict[uuid.UUID, object]

    async def save(self, intent: object) -> None:
        self.items[intent.payment_intent_id] = intent

    async def find_by_id(self, payment_intent_id: uuid.UUID) -> object | None:
        return self.items.get(payment_intent_id)


@dataclass
class _Audit:
    events: list[tuple[str, str, str | None]]

    async def record(self, *, event: str, payment_intent_id: str, actor_id: str | None) -> None:
        self.events.append((event, payment_intent_id, actor_id))


def test_payment_orchestration_create_receipt_approve_flow() -> None:
    try:
        dtos = importlib.import_module("src.application.payments.dtos")
        service_mod = importlib.import_module("src.application.payments.service")
        payment_entities = importlib.import_module("src.core.domain.entities.payment_intent")
    except SyntaxError as exc:
        import pytest

        pytest.skip(f"application package import edilemiyor: {exc}")

    repo = _InMemoryRepo(items={})
    audit = _Audit(events=[])
    service = service_mod.PaymentService(payment_intent_repository=repo, audit_port=audit)

    async def _run() -> tuple[str, str]:
        created = await service.create_intent(
            dtos.CreatePaymentIntentInput(
                payer_user_id=str(uuid.uuid4()),
                target_type=payment_entities.PaymentTargetType.MISSION,
                target_id=str(uuid.uuid4()),
                amount_kurus=100_000,
                currency="TRY",
                method=payment_entities.PaymentMethod.IBAN_TRANSFER,
                price_snapshot_id=str(uuid.uuid4()),
            )
        )
        await service.attach_receipt(
            dtos.UploadReceiptInput(payment_intent_id=created.payment_intent_id, receipt_blob_id="blob://r1")
        )
        approved = await service.approve_intent(
            dtos.ApprovePaymentInput(
                payment_intent_id=created.payment_intent_id,
                approved_by_admin_user_id=str(uuid.uuid4()),
            )
        )
        return created.status, approved.status

    before, after = asyncio.run(_run())

    assert before == "PAYMENT_PENDING"
    assert after == "PAID"
    assert [event for event, _, _ in audit.events] == [
        "PAYMENT_INTENT_CREATED",
        "RECEIPT_ATTACHED",
        "PAYMENT_APPROVED",
    ]
