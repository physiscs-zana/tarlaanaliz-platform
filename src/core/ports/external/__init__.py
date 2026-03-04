# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-033: External ports module — dış servis entegrasyonları.
"""External service ports public API."""

from src.core.ports.external.ai_worker_feedback import (
    AIWorkerFeedback,
    FeedbackPipelineStatus,
    FeedbackSubmissionResult,
    TrainingDatasetExport,
)
from src.core.ports.external.ddos_protection import (
    DDoSProtection,
    IPAccessAction,
    IPAccessRule,
    IPAccessRuleResult,
    ProtectionStatus,
    SecurityEvent,
    SecurityEventAction,
    SecurityEventsPage,
    SecurityLevel,
    ZoneAnalytics,
)
from src.core.ports.external.parcel_geometry_provider import (
    ParcelGeometry,
    ParcelGeometryProvider,
    ParcelValidationResult,
)
from src.core.ports.external.payment_gateway import (
    PaymentGateway,
    PaymentSessionResponse,
    PaymentVerificationResult,
    RefundResult,
)
from src.core.ports.external.sms_gateway import (
    SMSGateway,
    SmsBatchResult,
    SmsDeliveryStatus,
    SmsResult,
)
from src.core.ports.external.av_scanner_port import (
    AVScannerPort,
    AVScanReport,
    AVScanResult,
)
from src.core.ports.external.storage_service import (
    BlobMetadata,
    PresignedUrl,
    StorageService,
)

__all__: list[str] = [
    # AI Worker Feedback (KR-019, KR-029)
    "AIWorkerFeedback",
    "FeedbackSubmissionResult",
    "TrainingDatasetExport",
    "FeedbackPipelineStatus",
    # DDoS Protection
    "DDoSProtection",
    "ProtectionStatus",
    "IPAccessAction",
    "IPAccessRule",
    "IPAccessRuleResult",
    "SecurityEvent",
    "SecurityEventAction",
    "SecurityEventsPage",
    "SecurityLevel",
    "ZoneAnalytics",
    # Parcel Geometry (KR-013, KR-016)
    "ParcelGeometryProvider",
    "ParcelGeometry",
    "ParcelValidationResult",
    # Payment Gateway (KR-033)
    "PaymentGateway",
    "PaymentSessionResponse",
    "PaymentVerificationResult",
    "RefundResult",
    # SMS Gateway
    "SMSGateway",
    "SmsResult",
    "SmsBatchResult",
    "SmsDeliveryStatus",
    # AV Scanner (KR-073)
    "AVScannerPort",
    "AVScanReport",
    "AVScanResult",
    # Storage Service
    "StorageService",
    "BlobMetadata",
    "PresignedUrl",
]
