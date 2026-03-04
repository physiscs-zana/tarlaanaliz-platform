# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-041: SDLC gate tests for admin payments endpoints.
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

    def create_intent(self, *, actor_user_id: str, payload: PaymentIntentCreateRequest, corr_id: str | None) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=self.intent_id,
            status=PaymentStatus.PENDING_RECEIPT,
            amount=payload.amount,
            season=payload.season,
            package_code=payload.package_code,
            field_ids=payload.field_ids,
            created_at=datetime.now(timezone.utc),
        )

    def upload_receipt(self, *, actor_user_id: str, intent_id: UUID, filename: str, content_type: str | None, content: bytes, corr_id: str | None) -> PaymentIntentResponse:
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

    def list_pending_payments(self, *, corr_id: str | None) -> list[PaymentIntentResponse]:
        return []

    def approve_payment(self, *, actor_user_id: str, payment_id: UUID, corr_id: str | None) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=payment_id,
            status=PaymentStatus.PAID,
            amount=1,
            season="2026",
            package_code="STD",
            field_ids=[uuid4()],
            created_at=datetime.now(timezone.utc),
        )

    def reject_payment(self, *, actor_user_id: str, payment_id: UUID, reason: str, corr_id: str | None) -> PaymentIntentResponse:
        return PaymentIntentResponse(
            intent_id=payment_id,
            status=PaymentStatus.REJECTED,
            amount=1,
            season="2026",
            package_code="STD",
            field_ids=[uuid4()],
            created_at=datetime.now(timezone.utc),
        )


def _build_app(user: dict[str, object]) -> FastAPI:
    app = FastAPI()
    app.include_router(payments_router)
    app.include_router(admin_router)
    app.state.payment_service = StubPaymentService()

    @app.middleware("http")
    async def add_state(request: Request, call_next):
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


def test_admin_approve_requires_permission() -> None:
    app = _build_app({"user_id": "admin-1", "roles": ["admin"], "permissions": []})
    client = TestClient(app)

    response = client.post(f"/admin/payments/{uuid4()}/approve")

    assert response.status_code == 403
