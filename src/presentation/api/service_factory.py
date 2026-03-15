# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.  # noqa: RUF003
# KR-081: Service container wiring for dependency injection.
"""Service factory: creates real service instances at startup."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ServiceContainer:
    """Holds all application service instances.

    Created during lifespan and assigned to app.state.services.
    Endpoint dependencies retrieve services from this container.
    """

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service
        logger.debug("service_registered", service_name=name)

    def get(self, name: str) -> Any | None:
        return self._services.get(name)

    def get_or_raise(self, name: str) -> Any:
        svc = self._services.get(name)
        if svc is None:
            raise RuntimeError(f"Service not found: {name}")
        return svc

    @property
    def registered(self) -> list[str]:
        return list(self._services.keys())


async def create_service_container(
    *,
    db_session_factory: Any = None,
    event_bus: Any = None,
    storage: Any = None,
) -> ServiceContainer:
    """Create application services and register them in the container.

    Args:
        db_session_factory: SQLAlchemy async session factory (None means in-memory).
        event_bus: EventBus instance (None means stub).
        storage: StorageService instance (None means stub).

    Returns:
        Populated ServiceContainer.
    """
    container = ServiceContainer()

    # Register core application service CLASSES — these require Protocol-based
    # dependencies (repos, event buses) that are injected at endpoint level,
    # so we store the class references for lazy instantiation.
    from src.application.services.field_service import FieldService
    from src.application.services.mission_service import MissionService
    from src.application.services.audit_log_service import AuditLogService
    from src.application.services.expert_review_service import ExpertReviewService
    from src.application.services.weather_block_service import WeatherBlockService
    from src.application.services.pricebook_service import PricebookService
    from src.application.services.subscription_scheduler import SubscriptionScheduler
    from src.application.services.training_feedback_service import TrainingFeedbackService

    container.register("field_service", FieldService)
    container.register("mission_service", MissionService)
    container.register("audit_log_service", AuditLogService)
    container.register("expert_review_service", ExpertReviewService)
    container.register("weather_block_service", WeatherBlockService)
    container.register("pricebook_service", PricebookService)
    container.register("subscription_scheduler", SubscriptionScheduler)
    container.register("training_feedback_service", TrainingFeedbackService)

    # Store raw infrastructure dependencies for endpoint-level injection
    container.register("db_session_factory", db_session_factory)
    container.register("event_bus", event_bus)
    container.register("storage", storage)

    logger.info(
        "service_container_created",
        db_available=db_session_factory is not None,
        event_bus_available=event_bus is not None,
        storage_available=storage is not None,
        services=container.registered,
    )

    return container
