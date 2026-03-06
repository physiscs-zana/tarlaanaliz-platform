# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: SDLC gate tests for admin payments endpoints.
# KR-033: RBAC roles CENTRAL_ADMIN/BILLING_ADMIN, mark-paid with admin_note, refund.
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.presentation.api.dependencies import PaymentIntentCreateRequest, PaymentIntentResponse, PaymentStatus
from src.presentation.api.v1.endpoints.admin_payments import router as admin_router
from src.presentation.api.v1.endpoints.payments import router as payments_router


class StubPaymentService:
    def __init__(self) -> None:
        self.intent_id = uuid4()

    def create_intent(
        self, *, actor_user_id: str, payload: PaymentIntentCreateRequest, corr_id: str | None
    ) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=self.intent_id,
            status=PaymentStatus.PENDING_RECEIPT,
            amount=payload.amount,
            season=payload.season,
            package_code=payload.package_code,
            field_ids=payload.field_ids,
            created_at=datetime.now(timezone.utc),
        )

    def upload_receipt(
        self,
        *,
        actor_user_id: str,
        intent_id: UUID,
        filename: str,
        content_type: str | None,
        content: bytes,
        corr_id: str | None,
    ) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=intent_id,
            status=PaymentStatus.PENDING_ADMIN_REVIEW,
            amount=1,
            season="2026",
            package_code="STD",
            field_ids=[uuid4()],
            created_at=datetime.now(timezone.utc),
        )

    def get_intent(self, *, actor_user_id: str, intent_id: UUID, corr_id: str | None) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=intent_id,
            status=PaymentStatus.PENDING_ADMIN_REVIEW,
            amount=1,
            season="2026",
            package_code="STD",
            field_ids=[uuid4()],
            created_at=datetime.now(timezone.utc),
        )

    def cancel_intent(
        self, *, actor_user_id: str, intent_id: UUID, reason: str, corr_id: str | None
    ) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=intent_id,
            status=PaymentStatus.REJECTED,
            amount=1,
            season="2026",
            package_code="STD",
            field_ids=[uuid4()],
            created_at=datetime.now(timezone.utc),
        )

    def list_pending_payments(self, *, corr_id: str | None) -> list[PaymentIntentResponse]:
        return []

    def list_intents(
        self, *, status_filter: str | None, field_id: UUID | None, corr_id: str | None
    ) -> list[PaymentIntentResponse]:
        return []

    def approve_payment(
        self, *, actor_user_id: str, payment_id: UUID, admin_note: str, corr_id: str | None
    ) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=payment_id,
            status=PaymentStatus.PAID,
            amount=1,
            season="2026",
            package_code="STD",
            field_ids=[uuid4()],
            created_at=datetime.now(timezone.utc),
        )

    def reject_payment(
        self, *, actor_user_id: str, payment_id: UUID, reason: str, corr_id: str | None
    ) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=payment_id,
            status=PaymentStatus.REJECTED,
            amount=1,
            season="2026",
            package_code="STD",
            field_ids=[uuid4()],
            created_at=datetime.now(timezone.utc),
        )

    def refund_payment(
        self, *, actor_user_id: str, payment_id: UUID, refund_amount_kurus: int, reason: str, corr_id: str | None
    ) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=payment_id,
            status=PaymentStatus.REJECTED,
            amount=1,
            season="2026",
            package_code="STD",
            field_ids=[uuid4()],
            created_at=datetime.now(timezone.utc),
        )

    def get_payment_instructions(self, *, actor_user_id: str, intent_id: UUID, corr_id: str | None) -> dict:
        return {}


def _build_app(user: dict[str, object]) -> FastAPI:
    app = FastAPI()
    app.include_router(payments_router)
    app.include_router(admin_router)
    app.state.payment_service = StubPaymentService()

    @app.middleware("http")
    async def add_state(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.user = user
        request.state.corr_id = "corr-test"
        return await call_next(request)

    return app


def test_create_payment_intent_sets_corr_id_header() -> None:
    app = _build_app({"user_id": "u-1", "roles": ["farmer"], "permissions": []})
    client = TestClient(app)

    response = client.post(
        "/payments/intents",
        json={"amount": 100.0, "season": "2026", "package_code": "STD", "field_ids": [str(uuid4())]},
    )

    assert response.status_code == 201
    assert response.headers["X-Correlation-Id"] == "corr-test"


def test_admin_mark_paid_requires_ssot_roles() -> None:
    """KR-063: 'admin' generic rolü yerine CENTRAL_ADMIN/BILLING_ADMIN gerekli."""
    app = _build_app({"user_id": "admin-1", "roles": ["admin"], "permissions": ["payments:approve"]})
    client = TestClient(app)

    # Generic 'admin' rolü → 403
    response = client.post(
        f"/admin/payments/intents/{uuid4()}/mark-paid",
        json={"admin_note": "Dekont kontrol edildi"},
    )
    assert response.status_code == 403


def test_admin_mark_paid_with_central_admin_role() -> None:
    """KR-033: CENTRAL_ADMIN rolü ile mark-paid çalışır, admin_note zorunlu."""
    app = _build_app({"user_id": "admin-1", "roles": ["CENTRAL_ADMIN"], "permissions": ["payments:approve"]})
    client = TestClient(app)

    response = client.post(
        f"/admin/payments/intents/{uuid4()}/mark-paid",
        json={"admin_note": "Dekont doğrulandı"},
    )
    assert response.status_code == 200


def test_admin_mark_paid_requires_admin_note() -> None:
    """KR-033 §8: admin_note boş olamaz."""
    app = _build_app({"user_id": "admin-1", "roles": ["CENTRAL_ADMIN"], "permissions": ["payments:approve"]})
    client = TestClient(app)

    response = client.post(
        f"/admin/payments/intents/{uuid4()}/mark-paid",
        json={"admin_note": ""},
    )
    assert response.status_code == 422


def test_admin_mark_paid_with_billing_admin_role() -> None:
    """KR-033 §10: BILLING_ADMIN dekont onayı yapabilir."""
    app = _build_app({"user_id": "billing-1", "roles": ["BILLING_ADMIN"], "permissions": ["payments:approve"]})
    client = TestClient(app)

    response = client.post(
        f"/admin/payments/intents/{uuid4()}/mark-paid",
        json={"admin_note": "IBAN dekont eşleşti"},
    )
    assert response.status_code == 200


def test_admin_reject_requires_ssot_roles() -> None:
    """KR-063: reject de SSOT rolü gerektirir."""
    app = _build_app({"user_id": "admin-1", "roles": ["admin"], "permissions": ["payments:reject"]})
    client = TestClient(app)

    response = client.post(
        f"/admin/payments/intents/{uuid4()}/reject",
        json={"reason": "Dekont uyumsuz"},
    )
    assert response.status_code == 403


def test_admin_reject_with_central_admin() -> None:
    app = _build_app({"user_id": "admin-1", "roles": ["CENTRAL_ADMIN"], "permissions": ["payments:reject"]})
    client = TestClient(app)

    response = client.post(
        f"/admin/payments/intents/{uuid4()}/reject",
        json={"reason": "Dekont uyumsuz"},
    )
    assert response.status_code == 200


def test_admin_refund_endpoint_exists() -> None:
    """KR-033 §5: Refund endpoint mevcut olmalı."""
    app = _build_app({"user_id": "admin-1", "roles": ["CENTRAL_ADMIN"], "permissions": ["payments:refund"]})
    client = TestClient(app)

    response = client.post(
        f"/admin/payments/intents/{uuid4()}/refund",
        json={"refund_amount_kurus": 10000, "reason": "Çiftçi iade talebi"},
    )
    assert response.status_code == 200


def test_admin_refund_over_500tl_requires_central_admin() -> None:
    """KR-033 §10: >500 TL iade CENTRAL_ADMIN gerektirir."""
    # BILLING_ADMIN ile 600 TL (60000 kuruş) iade → 403
    app = _build_app({"user_id": "billing-1", "roles": ["BILLING_ADMIN"], "permissions": ["payments:refund"]})
    client = TestClient(app)

    response = client.post(
        f"/admin/payments/intents/{uuid4()}/refund",
        json={"refund_amount_kurus": 60000, "reason": "Yüksek tutarlı iade"},
    )
    assert response.status_code == 403


def test_admin_refund_under_500tl_billing_admin_ok() -> None:
    """KR-033 §10: ≤500 TL iade BILLING_ADMIN tek imzayla yapabilir."""
    app = _build_app({"user_id": "billing-1", "roles": ["BILLING_ADMIN"], "permissions": ["payments:refund"]})
    client = TestClient(app)

    response = client.post(
        f"/admin/payments/intents/{uuid4()}/refund",
        json={"refund_amount_kurus": 40000, "reason": "Kısmi iade"},
    )
    assert response.status_code == 200


def test_admin_list_intents_with_filters() -> None:
    """KR-033 §5: GET /admin/payments/intents?status=PAYMENT_PENDING&field_id=..."""
    app = _build_app({"user_id": "admin-1", "roles": ["CENTRAL_ADMIN"], "permissions": ["payments:review"]})
    client = TestClient(app)

    response = client.get("/admin/payments/intents?status=PAYMENT_PENDING")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
