# PATH: src/infrastructure/monitoring/security_events.py
# DESC: Security event logging adapter.
"""
Security Event Logger: güvenlik olaylarını yapılandırılmış loglarla kaydeder.

Amaç: Güvenlik açısından önemli olayları (kimlik doğrulama, yetkilendirme,
  şüpheli aktivite, rate limit aşımı, veri erişim) yapılandırılmış
  loglar ile kaydeder. SIEM entegrasyonu ve güvenlik denetimi için
  standart format kullanır.

Sorumluluk: Güvenlik olayı loglama, PII redaction, audit trail.

Güvenlik (RBAC/PII/Audit):
  PII loglanmaz (IP adresi hariç, maskelenebilir).
  Olay detayları güvenlik denetimi için yeterli seviyede.
  Hassas veriler (token, password) asla loglanmaz.

Observability (log fields/metrics/traces):
  event_category, event_action, user_id, source_ip, severity, correlation_id.

Testler: Unit test (log format doğrulaması).
Bağımlılıklar: structlog.
Notlar/SSOT: Tek referans: tarlaanaliz_platform_tree v3.2.2 FINAL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import structlog

logger = structlog.get_logger("security")


class SecuritySeverity(str, Enum):
    """Güvenlik olay ciddiyeti."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SecurityCategory(str, Enum):
    """Güvenlik olay kategorisi."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    DATA_ACCESS = "data_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    INPUT_VALIDATION = "input_validation"
    CONFIGURATION = "configuration"


class SecurityEventLogger:
    """Güvenlik olaylarını yapılandırılmış loglarla kaydeden adapter.

    Tüm güvenlik olayları standart format ile loglanır:
      - event_category: Olay kategorisi (authentication, authorization, vb.)
      - event_action: Yapılan eylem (login_success, login_failed, vb.)
      - severity: Ciddiyet (info, warning, critical)
      - user_id: İlgili kullanıcı ID'si (varsa)
      - source_ip: İstek kaynağı IP adresi (maskelenmiş)
      - correlation_id: Distributed tracing ID
      - timestamp: ISO 8601 format

    Kullanım:
        sec_logger = SecurityEventLogger()
        sec_logger.log_authentication("login_success", user_id="u-123", source_ip="1.2.3.4")
        sec_logger.log_authorization_failure(user_id="u-123", resource="/admin", action="access")
    """

    def _mask_ip(self, ip: str) -> str:
        """IP adresinin son oktetini maskeler (PII minimizasyonu).

        Args:
            ip: Orijinal IP adresi.

        Returns:
            Maskelenmiş IP (ör: "192.168.1.***").
        """
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
        # IPv6 veya beklenmeyen format
        return "***"

    def _log_event(
        self,
        *,
        category: SecurityCategory,
        action: str,
        severity: SecuritySeverity,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        correlation_id: Optional[str] = None,
        detail: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        """Güvenlik olayını loglar (internal).

        Args:
            category: Olay kategorisi.
            action: Olay eylemi.
            severity: Ciddiyet seviyesi.
            user_id: İlgili kullanıcı ID.
            source_ip: Kaynak IP adresi.
            correlation_id: Tracing ID.
            detail: Ek detay.
            extra: Ek log alanları.
        """
        log_data: dict[str, Any] = {
            "security_event": True,
            "event_category": category.value,
            "event_action": action,
            "severity": severity.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if user_id:
            log_data["user_id"] = user_id
        if source_ip:
            log_data["source_ip"] = self._mask_ip(source_ip)
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        if detail:
            log_data["detail"] = detail
        if extra:
            log_data.update(extra)

        if severity == SecuritySeverity.CRITICAL:
            logger.critical("security_event", **log_data)
        elif severity == SecuritySeverity.WARNING:
            logger.warning("security_event", **log_data)
        else:
            logger.info("security_event", **log_data)

    # ------------------------------------------------------------------
    # Authentication olayları
    # ------------------------------------------------------------------
    def log_authentication(
        self,
        action: str,
        *,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        correlation_id: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        """Kimlik doğrulama olayını logla.

        Args:
            action: Eylem (login_success, login_failed, token_refresh, logout).
            user_id: Kullanıcı ID.
            source_ip: Kaynak IP.
            correlation_id: Tracing ID.
            detail: Ek detay.
        """
        severity = SecuritySeverity.INFO
        if "failed" in action or "invalid" in action:
            severity = SecuritySeverity.WARNING

        self._log_event(
            category=SecurityCategory.AUTHENTICATION,
            action=action,
            severity=severity,
            user_id=user_id,
            source_ip=source_ip,
            correlation_id=correlation_id,
            detail=detail,
        )

    def log_login_success(
        self,
        user_id: str,
        *,
        source_ip: Optional[str] = None,
    ) -> None:
        """Başarılı giriş logla."""
        self.log_authentication(
            "login_success",
            user_id=user_id,
            source_ip=source_ip,
        )

    def log_login_failed(
        self,
        *,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        reason: str = "",
    ) -> None:
        """Başarısız giriş logla."""
        self.log_authentication(
            "login_failed",
            user_id=user_id,
            source_ip=source_ip,
            detail=reason,
        )

    # ------------------------------------------------------------------
    # Authorization olayları
    # ------------------------------------------------------------------
    def log_authorization_failure(
        self,
        *,
        user_id: str,
        resource: str,
        action: str,
        source_ip: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Yetkilendirme hatası logla.

        Args:
            user_id: Kullanıcı ID.
            resource: Erişilmeye çalışılan kaynak.
            action: Yapılmaya çalışılan eylem.
            source_ip: Kaynak IP.
            correlation_id: Tracing ID.
        """
        self._log_event(
            category=SecurityCategory.AUTHORIZATION,
            action="access_denied",
            severity=SecuritySeverity.WARNING,
            user_id=user_id,
            source_ip=source_ip,
            correlation_id=correlation_id,
            detail=f"Resource: {resource}, Action: {action}",
        )

    # ------------------------------------------------------------------
    # Rate limit olayları
    # ------------------------------------------------------------------
    def log_rate_limit_exceeded(
        self,
        *,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        endpoint: str,
        limit: int,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Rate limit aşımı logla.

        Args:
            user_id: Kullanıcı ID.
            source_ip: Kaynak IP.
            endpoint: Aşılan endpoint.
            limit: Aşılan limit değeri.
            correlation_id: Tracing ID.
        """
        self._log_event(
            category=SecurityCategory.RATE_LIMIT,
            action="rate_limit_exceeded",
            severity=SecuritySeverity.WARNING,
            user_id=user_id,
            source_ip=source_ip,
            correlation_id=correlation_id,
            detail=f"Endpoint: {endpoint}, Limit: {limit}/min",
        )

    # ------------------------------------------------------------------
    # Suspicious activity
    # ------------------------------------------------------------------
    def log_suspicious_activity(
        self,
        action: str,
        *,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        detail: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Şüpheli aktivite logla.

        Args:
            action: Aktivite türü.
            user_id: Kullanıcı ID.
            source_ip: Kaynak IP.
            detail: Detay.
            correlation_id: Tracing ID.
        """
        self._log_event(
            category=SecurityCategory.SUSPICIOUS_ACTIVITY,
            action=action,
            severity=SecuritySeverity.CRITICAL,
            user_id=user_id,
            source_ip=source_ip,
            correlation_id=correlation_id,
            detail=detail,
        )

    # ------------------------------------------------------------------
    # Data access olayları
    # ------------------------------------------------------------------
    def log_data_access(
        self,
        *,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Veri erişim olayı logla (audit trail).

        Args:
            user_id: Erişen kullanıcı ID.
            resource_type: Kaynak türü (ör: "mission", "analysis").
            resource_id: Kaynak ID.
            action: Eylem (read, update, delete).
            correlation_id: Tracing ID.
        """
        self._log_event(
            category=SecurityCategory.DATA_ACCESS,
            action=action,
            severity=SecuritySeverity.INFO,
            user_id=user_id,
            correlation_id=correlation_id,
            detail=f"{resource_type}:{resource_id}",
        )

    # ------------------------------------------------------------------
    # Input validation olayları
    # ------------------------------------------------------------------
    def log_input_validation_failure(
        self,
        *,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        endpoint: str,
        violation: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Girdi doğrulama hatası logla (potansiyel injection girişimi).

        Args:
            user_id: Kullanıcı ID.
            source_ip: Kaynak IP.
            endpoint: Hedef endpoint.
            violation: İhlal açıklaması.
            correlation_id: Tracing ID.
        """
        self._log_event(
            category=SecurityCategory.INPUT_VALIDATION,
            action="validation_failed",
            severity=SecuritySeverity.WARNING,
            user_id=user_id,
            source_ip=source_ip,
            correlation_id=correlation_id,
            detail=f"Endpoint: {endpoint}, Violation: {violation}",
        )
