# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Payment application service orchestration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from src.application.payments.dtos import (
    ApprovePaymentInput,
    CreatePaymentIntentInput,
    PaymentOperationResult,
    RejectPaymentInput,
    UploadReceiptInput,
)
from src.core.domain.entities.payment_intent import PaymentIntent, PaymentStatus


class PaymentIntentRepositoryPort(Protocol):
    async def save(self, intent: PaymentIntent) -> None: ...
    async def find_by_id(self, payment_intent_id: uuid.UUID) -> PaymentIntent | None: ...


class PaymentAuditPort(Protocol):
    async def record(self, *, event: str, payment_intent_id: str, actor_id: str | None) -> None: ...


@dataclass(slots=True)
class PaymentService:
    """Orchestrates payment intent lifecycle transitions."""

    payment_intent_repository: PaymentIntentRepositoryPort
    audit_port: PaymentAuditPort

    # KR-033: intent must exist before any paid state transition.
    async def create_intent(self, payload: CreatePaymentIntentInput) -> PaymentOperationResult:
        now = datetime.now(timezone.utc)
        intent = PaymentIntent(
            payment_intent_id=uuid.uuid4(),
            payer_user_id=uuid.UUID(payload.payer_user_id),
            target_type=payload.target_type,
            target_id=uuid.UUID(payload.target_id),
            amount_kurus=payload.amount_kurus,
            currency=payload.currency,
            method=payload.method,
            status=PaymentStatus.PAYMENT_PENDING,
            payment_ref=_build_payment_ref(),
            price_snapshot_id=uuid.UUID(payload.price_snapshot_id),
            provider=payload.provider,
            created_at=now,
            updated_at=now,
        )
        await self.payment_intent_repository.save(intent)
        await self.audit_port.record(
            event="PAYMENT_INTENT_CREATED",
            payment_intent_id=str(intent.payment_intent_id),
            actor_id=payload.payer_user_id,
        )
        return _result(intent)

    async def attach_receipt(self, payload: UploadReceiptInput) -> PaymentOperationResult:
        intent = await self._get_intent(payload.payment_intent_id)
        intent.attach_receipt(
            receipt_blob_id=payload.receipt_blob_id,
            receipt_meta={"receipt_ref": payload.receipt_ref} if payload.receipt_ref else None,
        )
        await self.payment_intent_repository.save(intent)
        await self.audit_port.record(
            event="RECEIPT_ATTACHED",
            payment_intent_id=payload.payment_intent_id,
            actor_id=None,
        )
        return _result(intent)

    async def approve_intent(self, payload: ApprovePaymentInput) -> PaymentOperationResult:
        intent = await self._get_intent(payload.payment_intent_id)
        intent.mark_paid(
            approved_by_admin_user_id=uuid.UUID(payload.approved_by_admin_user_id),
            admin_note=payload.admin_note or "Manual approval",
        )
        await self.payment_intent_repository.save(intent)
        await self.audit_port.record(
            event="PAYMENT_APPROVED",
            payment_intent_id=payload.payment_intent_id,
            actor_id=payload.approved_by_admin_user_id,
        )
        return _result(intent)

    async def reject_intent(self, payload: RejectPaymentInput) -> PaymentOperationResult:
        intent = await self._get_intent(payload.payment_intent_id)
        intent.reject(reason=payload.reason)
        await self.payment_intent_repository.save(intent)
        await self.audit_port.record(
            event="PAYMENT_REJECTED",
            payment_intent_id=payload.payment_intent_id,
            actor_id=payload.rejected_by_admin_user_id,
        )
        return _result(intent)

    async def _get_intent(self, payment_intent_id: str) -> PaymentIntent:
        intent = await self.payment_intent_repository.find_by_id(uuid.UUID(payment_intent_id))
        if intent is None:
            raise ValueError(f"payment_intent_id not found: {payment_intent_id}")
        return intent


def _build_payment_ref() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    token = uuid.uuid4().hex[:8].upper()
    return f"PAY-{stamp}-{token}"


def _result(intent: PaymentIntent) -> PaymentOperationResult:
    return PaymentOperationResult(
        payment_intent_id=str(intent.payment_intent_id),
        status=intent.status.value,
        updated_at=intent.updated_at,
    )
