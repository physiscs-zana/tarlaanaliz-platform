# PATH: src/core/domain/value_objects/__init__.py
# DESC: Domain value object module: __init__.py.
"""Domain Value Objects public API."""

from src.core.domain.value_objects.money import CurrencyCode, Money
from src.core.domain.value_objects.spectral_tier import (
    BandClass,
    ReportTier,
    SpectralTier,
    classify_bands,
    derive_available_indices,
    derive_enabled_pipelines,
    determine_report_tier,
    has_thermal_capability,
)
from src.core.domain.value_objects.parcel_ref import ParcelRef
from src.core.domain.value_objects.payment_status import (
    PaymentStatus,
    TERMINAL_PAYMENT_STATUSES,
    VALID_PAYMENT_TRANSITIONS,
    is_valid_payment_transition,
    requires_payment_intent,
)
from src.core.domain.value_objects.price_snapshot import PriceSnapshotRef
from src.core.domain.value_objects.province import Province, VALID_PROVINCE_CODES
from src.core.domain.value_objects.qc_flag import QCFlag, QCFlagSeverity, QCFlagType
from src.core.domain.value_objects.qc_report import QCReport
from src.core.domain.value_objects.qc_status import (
    QCRecommendedAction,
    QCStatus,
    is_qc_blocking,
    is_qc_passable,
)
from src.core.domain.value_objects.recommended_action import (
    RecommendedAction,
    RecommendedActionError,
)
from src.core.domain.value_objects.role import Role, RoleError
from src.core.domain.value_objects.sla_metrics import SLAMetrics, SLAMetricsError
from src.core.domain.value_objects.sla_threshold import SLAThreshold, SLAThresholdError
from src.core.domain.value_objects.specialization import (
    Specialization,
    SPECIALIZATION_DISPLAY_NAMES,
    SPECIALIZATION_LAYER_MAPPINGS,
    get_related_layer_codes,
    get_specialization_display_name,
    matches_finding_code,
)
from src.core.domain.value_objects.subscription_plan import (
    SubscriptionPlan,
    SubscriptionPlanError,
)
from src.core.domain.value_objects.training_grade import TrainingGrade, TrainingGradeError
from src.core.domain.value_objects.weather_block_status import (
    WeatherBlockStatus,
    TERMINAL_WEATHER_BLOCK_STATUSES,
    VALID_WEATHER_BLOCK_TRANSITIONS,
    is_blocking_mission,
    is_force_majeure,
    is_valid_weather_block_transition,
)

__all__: list[str] = [
    # spectral_tier (v1.2.0)
    "BandClass",
    "ReportTier",
    "SpectralTier",
    "classify_bands",
    "derive_available_indices",
    "derive_enabled_pipelines",
    "determine_report_tier",
    "has_thermal_capability",
    # money
    "CurrencyCode",
    "Money",
    # parcel_ref
    "ParcelRef",
    # payment_status
    "PaymentStatus",
    "TERMINAL_PAYMENT_STATUSES",
    "VALID_PAYMENT_TRANSITIONS",
    "is_valid_payment_transition",
    "requires_payment_intent",
    # price_snapshot
    "PriceSnapshotRef",
    # province
    "Province",
    "VALID_PROVINCE_CODES",
    # qc_flag
    "QCFlag",
    "QCFlagSeverity",
    "QCFlagType",
    # qc_report
    "QCReport",
    # qc_status
    "QCRecommendedAction",
    "QCStatus",
    "is_qc_blocking",
    "is_qc_passable",
    # recommended_action
    "RecommendedAction",
    "RecommendedActionError",
    # role
    "Role",
    "RoleError",
    # sla_metrics
    "SLAMetrics",
    "SLAMetricsError",
    # sla_threshold
    "SLAThreshold",
    "SLAThresholdError",
    # specialization
    "Specialization",
    "SPECIALIZATION_DISPLAY_NAMES",
    "SPECIALIZATION_LAYER_MAPPINGS",
    "get_related_layer_codes",
    "get_specialization_display_name",
    "matches_finding_code",
    # subscription_plan
    "SubscriptionPlan",
    "SubscriptionPlanError",
    # training_grade
    "TrainingGrade",
    "TrainingGradeError",
    # weather_block_status
    "WeatherBlockStatus",
    "TERMINAL_WEATHER_BLOCK_STATUSES",
    "VALID_WEATHER_BLOCK_TRANSITIONS",
    "is_blocking_mission",
    "is_force_majeure",
    "is_valid_weather_block_transition",
]
