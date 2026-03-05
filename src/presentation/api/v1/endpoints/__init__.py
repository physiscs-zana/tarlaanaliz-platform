# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
"""Endpoints package exports for API v1."""

from src.presentation.api.v1.endpoints.admin_payments import router as admin_payments_router
from src.presentation.api.v1.endpoints.admin_audit import router as admin_audit_router
from src.presentation.api.v1.endpoints.admin_pricing import router as admin_pricing_router
from src.presentation.api.v1.endpoints.auth import router as auth_router
from src.presentation.api.v1.endpoints.calibration import router as calibration_router
from src.presentation.api.v1.endpoints.expert_portal import router as expert_portal_router
from src.presentation.api.v1.endpoints.experts import router as experts_router
from src.presentation.api.v1.endpoints.fields import router as fields_router
from src.presentation.api.v1.endpoints.missions import router as missions_router
from src.presentation.api.v1.endpoints.parcels import router as parcels_router
from src.presentation.api.v1.endpoints.payment_webhooks import router as payment_webhooks_router
from src.presentation.api.v1.endpoints.payments import router as payments_router
from src.presentation.api.v1.endpoints.pilots import router as pilots_router
from src.presentation.api.v1.endpoints.pricing import router as pricing_router
from src.presentation.api.v1.endpoints.qc import router as qc_router
from src.presentation.api.v1.endpoints.results import router as results_router
from src.presentation.api.v1.endpoints.sla_metrics import router as sla_metrics_router
from src.presentation.api.v1.endpoints.subscriptions import router as subscriptions_router
from src.presentation.api.v1.endpoints.training_feedback import router as training_feedback_router
from src.presentation.api.v1.endpoints.weather_block_reports import router as weather_block_reports_router
from src.presentation.api.v1.endpoints.weather_blocks import router as weather_blocks_router

__all__: list[str] = [
    "admin_payments_router",
    "admin_audit_router",
    "admin_pricing_router",
    "auth_router",
    "calibration_router",
    "expert_portal_router",
    "experts_router",
    "fields_router",
    "missions_router",
    "parcels_router",
    "payment_webhooks_router",
    "payments_router",
    "pilots_router",
    "pricing_router",
    "qc_router",
    "results_router",
    "sla_metrics_router",
    "subscriptions_router",
    "training_feedback_router",
    "weather_block_reports_router",
    "weather_blocks_router",
]
