# PATH: src/infrastructure/integrations/cloudflare/ddos_protection.py
# DESC: Cloudflare DDoS protection adapter.
"""
Cloudflare DDoS protection adapter: Cloudflare API v4 implementasyonu.

Amaç: DDoSProtection portunun Cloudflare-spesifik implementasyonu.
Sorumluluk: Zone güvenlik seviyesi yönetimi, IP erişim kuralları,
  güvenlik olayları sorgulama ve zone analitikleri.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (zone_id, IP adresi, kural tanımları).
  Çıktı: Port DTO'ları (ProtectionStatus, IPAccessRuleResult, SecurityEventsPage, vb.).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; API token env/secret manager üzerinden; TLS zorunlu.
  IP adresi PII kabul edilir; loglanırken maskelenir.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff).
  Cloudflare API rate limit: 1200 req/5min.
  Tüm işlemler idempotent; retry güvenlidir.

Observability (log fields/metrics/traces):
  latency, error_code, retries, zone_id, action, rule_id.

Testler: Contract test (port), integration test (Cloudflare sandbox/stub), e2e.
Bağımlılıklar: httpx, tenacity, structlog.
Notlar/SSOT: Tek referans: tarlaanaliz_platform_tree v3.2.2 FINAL.
  Aynı kavram başka yerde tekrar edilmez.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, cast

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

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
from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)

_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


def _mask_ip(ip: str) -> str:
    """IP adresini maskeler (PII koruma).

    IPv4: 192.168.1.100 -> 192.168.***
    IPv6: kısaltılarak maskelenir.
    CIDR: prefix korunur, host kısmı maskelenir.
    """
    if "/" in ip:
        base, prefix = ip.split("/", 1)
        return f"{_mask_ip(base)}/{prefix}"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***"
    # IPv6 veya bilinmeyen format
    if len(ip) > 8:
        return ip[:8] + "***"
    return "***"


class CloudflareDDoSAdapter(DDoSProtection):
    """DDoSProtection port implementasyonu (Cloudflare API v4).

    httpx async HTTP client ile Cloudflare API'ye bağlanır.
    Tüm sorgu ve durum değiştirme işlemlerinde retry uygulanır
    (tüm Cloudflare zone operasyonları idempotent'tir).

    API token, zone_id ve diğer ayarlar Settings üzerinden yüklenir.
    Rate limit: Cloudflare API 1200 req/5min; burst koruması için
    exponential backoff yeterlidir.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.cloudflare_api_url
        self._timeout = httpx.Timeout(settings.cloudflare_timeout_seconds)
        self._api_token = settings.cloudflare_api_token.get_secret_value()
        self._default_zone_id = settings.cloudflare_zone_id

    def _get_client(self) -> httpx.AsyncClient:
        """Her istek için taze httpx client oluşturur."""
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={
                "Authorization": f"Bearer {self._api_token}",
                "Content-Type": "application/json",
            },
        )

    def _resolve_zone_id(self, zone_id: str) -> str:
        """Zone ID boş ise default'u kullanır."""
        resolved = zone_id or self._default_zone_id
        if not resolved:
            raise ValueError("zone_id belirtilmeli veya TARLA_CLOUDFLARE_ZONE_ID ayarlanmalı")
        return resolved

    # ------------------------------------------------------------------
    # Koruma durumu sorgulama
    # ------------------------------------------------------------------
    @_RETRY_DECORATOR
    async def get_protection_status(
        self,
        *,
        zone_id: str,
    ) -> ProtectionStatus:
        """Zone'un mevcut DDoS koruma durumunu sorgula."""
        resolved_zone = self._resolve_zone_id(zone_id)

        logger.info("cf_protection_status_request", zone_id=resolved_zone)

        async with self._get_client() as client:
            # Güvenlik seviyesi bilgisi
            settings_resp = await client.get(
                f"/zones/{resolved_zone}/settings/security_level",
            )
            settings_resp.raise_for_status()
            settings_data = settings_resp.json()

            # DDoS L7 managed ruleset durumu
            ddos_resp = await client.get(
                f"/zones/{resolved_zone}/rulesets",
            )
            ddos_resp.raise_for_status()
            ddos_data = ddos_resp.json()

        security_value = settings_data.get("result", {}).get("value", "medium")
        security_level = SecurityLevel(security_value)

        # DDoS L7 ruleset'in aktif olup olmadığını kontrol et
        rulesets = ddos_data.get("result", [])
        ddos_l7_enabled = any(rs.get("phase") == "ddos_l7" and rs.get("enabled", True) for rs in rulesets)
        active_rule_count = sum(
            len(rs.get("rules", [])) for rs in rulesets if rs.get("phase") in ("ddos_l7", "http_ratelimit")
        )

        status = ProtectionStatus(
            zone_id=resolved_zone,
            security_level=security_level,
            under_attack_mode=security_level == SecurityLevel.UNDER_ATTACK,
            ddos_l7_enabled=ddos_l7_enabled,
            active_rule_count=active_rule_count,
            last_checked_at=datetime.utcnow().isoformat() + "Z",
        )

        logger.info(
            "cf_protection_status_result",
            zone_id=resolved_zone,
            security_level=status.security_level.value,
            under_attack=status.under_attack_mode,
            ddos_l7_enabled=status.ddos_l7_enabled,
        )
        return status

    # ------------------------------------------------------------------
    # Güvenlik seviyesi ayarlama
    # ------------------------------------------------------------------
    @_RETRY_DECORATOR
    async def set_security_level(
        self,
        *,
        zone_id: str,
        level: SecurityLevel,
    ) -> ProtectionStatus:
        """Zone güvenlik seviyesini değiştir (under-attack dahil)."""
        resolved_zone = self._resolve_zone_id(zone_id)

        logger.info(
            "cf_set_security_level_request",
            zone_id=resolved_zone,
            target_level=level.value,
        )

        async with self._get_client() as client:
            response = await client.patch(
                f"/zones/{resolved_zone}/settings/security_level",
                json={"value": level.value},
            )
            response.raise_for_status()

        logger.info(
            "cf_set_security_level_success",
            zone_id=resolved_zone,
            level=level.value,
        )

        return await self.get_protection_status(zone_id=resolved_zone)

    # ------------------------------------------------------------------
    # IP erişim kuralları
    # ------------------------------------------------------------------
    @_RETRY_DECORATOR
    async def create_ip_access_rule(
        self,
        *,
        zone_id: str,
        ip_address: str,
        action: IPAccessAction,
        notes: str = "",
    ) -> IPAccessRuleResult:
        """IP erişim kuralı oluştur."""
        resolved_zone = self._resolve_zone_id(zone_id)
        masked_ip = _mask_ip(ip_address)

        logger.info(
            "cf_ip_rule_create_request",
            zone_id=resolved_zone,
            ip_masked=masked_ip,
            action=action.value,
        )

        payload: dict[str, Any] = {
            "mode": action.value,
            "configuration": {
                "target": "ip",
                "value": ip_address,
            },
        }
        if notes:
            payload["notes"] = notes

        async with self._get_client() as client:
            response = await client.post(
                f"/zones/{resolved_zone}/firewall/access_rules/rules",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        result_data = data.get("result", {})
        result = IPAccessRuleResult(
            rule_id=result_data.get("id", ""),
            success=data.get("success", False),
            action=action,
            ip_address_masked=masked_ip,
            message=f"IP erişim kuralı oluşturuldu: {action.value}",
        )

        logger.info(
            "cf_ip_rule_create_result",
            zone_id=resolved_zone,
            rule_id=result.rule_id,
            success=result.success,
            ip_masked=masked_ip,
        )
        return result

    @_RETRY_DECORATOR
    async def delete_ip_access_rule(
        self,
        *,
        zone_id: str,
        rule_id: str,
    ) -> IPAccessRuleResult:
        """IP erişim kuralını sil."""
        resolved_zone = self._resolve_zone_id(zone_id)

        logger.info(
            "cf_ip_rule_delete_request",
            zone_id=resolved_zone,
            rule_id=rule_id,
        )

        async with self._get_client() as client:
            response = await client.delete(
                f"/zones/{resolved_zone}/firewall/access_rules/rules/{rule_id}",
            )
            # 404 idempotent kabul edilir: kural zaten silinmiş
            if response.status_code == 404:
                logger.info(
                    "cf_ip_rule_delete_not_found",
                    zone_id=resolved_zone,
                    rule_id=rule_id,
                )
                return IPAccessRuleResult(
                    rule_id=rule_id,
                    success=True,
                    action=IPAccessAction.BLOCK,
                    message="Kural zaten mevcut değil (idempotent)",
                )
            response.raise_for_status()
            data = response.json()

        result = IPAccessRuleResult(
            rule_id=data.get("result", {}).get("id", rule_id),
            success=data.get("success", False),
            action=IPAccessAction.BLOCK,
            message="IP erişim kuralı silindi",
        )

        logger.info(
            "cf_ip_rule_delete_result",
            zone_id=resolved_zone,
            rule_id=result.rule_id,
            success=result.success,
        )
        return result

    @_RETRY_DECORATOR
    async def list_ip_access_rules(
        self,
        *,
        zone_id: str,
        action: Optional[IPAccessAction] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[IPAccessRule], int]:
        """Zone'daki IP erişim kurallarını listele."""
        resolved_zone = self._resolve_zone_id(zone_id)

        params: dict[str, Any] = {
            "page": page,
            "per_page": min(per_page, 100),
        }
        if action is not None:
            params["mode"] = action.value

        async with self._get_client() as client:
            response = await client.get(
                f"/zones/{resolved_zone}/firewall/access_rules/rules",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        result_list = data.get("result", [])
        total_count = data.get("result_info", {}).get("total_count", len(result_list))

        rules = [
            IPAccessRule(
                rule_id=r.get("id", ""),
                ip_address=r.get("configuration", {}).get("value", ""),
                action=IPAccessAction(r.get("mode", "block")),
                notes=r.get("notes", ""),
                created_at=r.get("created_on"),
            )
            for r in result_list
        ]

        logger.info(
            "cf_ip_rules_list",
            zone_id=resolved_zone,
            returned=len(rules),
            total_count=total_count,
        )
        return rules, total_count

    # ------------------------------------------------------------------
    # Güvenlik olayları
    # ------------------------------------------------------------------
    @_RETRY_DECORATOR
    async def get_security_events(
        self,
        *,
        zone_id: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50,
        cursor: str = "",
    ) -> SecurityEventsPage:
        """Zone'daki güvenlik olaylarını listele."""
        resolved_zone = self._resolve_zone_id(zone_id)

        params: dict[str, Any] = {
            "per_page": min(limit, 100),
        }
        if since is not None:
            params["since"] = since.isoformat() + "Z"
        if until is not None:
            params["until"] = until.isoformat() + "Z"
        if cursor:
            params["cursor"] = cursor

        logger.info(
            "cf_security_events_request",
            zone_id=resolved_zone,
            limit=limit,
        )

        async with self._get_client() as client:
            response = await client.get(
                f"/zones/{resolved_zone}/security/events",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        result_list = data.get("result", [])
        result_info = data.get("result_info", {})

        events = tuple(
            SecurityEvent(
                event_id=e.get("rayName", e.get("id", "")),
                action=SecurityEventAction(e.get("action", "log")),
                source_ip_masked=_mask_ip(e.get("clientIP", "")),
                country=e.get("country", ""),
                uri=e.get("clientRequestHTTPHost", "") + e.get("clientRequestPath", ""),
                user_agent=e.get("userAgent", ""),
                rule_id=e.get("ruleId", ""),
                occurred_at=e.get("datetime"),
            )
            for e in result_list
        )

        page = SecurityEventsPage(
            events=events,
            total_count=result_info.get("total_count", len(events)),
            has_more=bool(result_info.get("cursors", {}).get("after")),
            cursor=result_info.get("cursors", {}).get("after", ""),
        )

        logger.info(
            "cf_security_events_result",
            zone_id=resolved_zone,
            event_count=len(events),
            total_count=page.total_count,
            has_more=page.has_more,
        )
        return page

    # ------------------------------------------------------------------
    # Zone analitikleri
    # ------------------------------------------------------------------
    @_RETRY_DECORATOR
    async def get_zone_analytics(
        self,
        *,
        zone_id: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> ZoneAnalytics:
        """Zone güvenlik analitiklerini al."""
        resolved_zone = self._resolve_zone_id(zone_id)

        params: dict[str, Any] = {}
        since_str = since.isoformat() + "Z" if since else "-1440"  # default: son 24 saat
        until_str = until.isoformat() + "Z" if until else ""

        params["since"] = since_str
        if until_str:
            params["until"] = until_str

        logger.info(
            "cf_zone_analytics_request",
            zone_id=resolved_zone,
        )

        async with self._get_client() as client:
            response = await client.get(
                f"/zones/{resolved_zone}/analytics/dashboard",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        totals = data.get("result", {}).get("totals", {})
        requests_data = totals.get("requests", {})
        threats_data = totals.get("threats", {})

        threats_by_country: dict[str, int] = {}
        for entry in threats_data.get("country", []):
            if isinstance(entry, dict):
                threats_by_country[entry.get("id", "unknown")] = entry.get("count", 0)

        top_threat_types: dict[str, int] = {}
        for entry in threats_data.get("type", []):
            if isinstance(entry, dict):
                top_threat_types[entry.get("id", "unknown")] = entry.get("count", 0)

        now_iso = datetime.utcnow().isoformat() + "Z"
        analytics = ZoneAnalytics(
            zone_id=resolved_zone,
            period_start=since.isoformat() + "Z" if since else now_iso,
            period_end=until.isoformat() + "Z" if until else now_iso,
            total_requests=requests_data.get("all", 0),
            blocked_requests=threats_data.get("all", 0),
            challenged_requests=requests_data.get("ssl", {}).get("encrypted", 0),
            threats_by_country=threats_by_country,
            top_threat_types=top_threat_types,
        )

        logger.info(
            "cf_zone_analytics_result",
            zone_id=resolved_zone,
            total_requests=analytics.total_requests,
            blocked_requests=analytics.blocked_requests,
        )
        return analytics

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        """Cloudflare API erişilebilirliğini kontrol et.

        /user/tokens/verify endpoint'ini kullanarak API token'ın
        geçerli olduğunu ve API'nin erişilebilir olduğunu doğrular.
        """
        try:
            async with self._get_client() as client:
                response = await client.get("/user/tokens/verify")
                if response.status_code == 200:
                    data = response.json()
                    return bool(data.get("success", False))
                return False
        except (httpx.HTTPError, Exception):
            logger.warning("cf_health_check_failed")
            return False
