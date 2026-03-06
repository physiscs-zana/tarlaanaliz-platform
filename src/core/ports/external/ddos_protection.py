# PATH: src/core/ports/external/ddos_protection.py
# DESC: DDoSProtection portu: DDoS koruma sağlayıcısı.
"""
DDoSProtection portu: DDoS koruma sağlayıcısı.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  DDoS koruma sağlayıcısını (Cloudflare, AWS Shield vb.) soyutlar.
  Zone güvenlik durumunu sorgulama, under-attack modu yönetimi,
  IP erişim kuralları ve güvenlik olayları raporlama.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (zone_id, IP adresi, kural tanımları).
  Çıktı: IO sonuçları (koruma durumu, güvenlik olayları, kural sonuçları).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  IP adresi PII kabul edilebilir; loglanırken maskelenir.
  API key/token'lar SecretStr ile saklanır.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel). Sorgu işlemleri retry-safe;
  durum değiştiren işlemler (under-attack toggle, IP block) idempotent.

Observability (log fields/metrics/traces):
  latency, error_code, retries, zone_id, action, rule_id.

Testler: Contract test (port), integration test (provider stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon taşır.
  Tek referans: tarlaanaliz_platform_tree v3.2.2 FINAL.
  Aynı kavram başka yerde tekrar edilmez.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ------------------------------------------------------------------
# Port-specific DTOs (Contract nesneleri)
# ------------------------------------------------------------------
class SecurityLevel(str, Enum):
    """Cloudflare zone güvenlik seviyesi."""

    OFF = "off"
    ESSENTIALLY_OFF = "essentially_off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNDER_ATTACK = "under_attack"


class IPAccessAction(str, Enum):
    """IP erişim kuralı aksiyonu."""

    BLOCK = "block"
    CHALLENGE = "challenge"
    JS_CHALLENGE = "js_challenge"
    MANAGED_CHALLENGE = "managed_challenge"
    ALLOW = "whitelist"


class SecurityEventAction(str, Enum):
    """Güvenlik olayında alınan aksiyon."""

    BLOCK = "block"
    CHALLENGE = "challenge"
    JS_CHALLENGE = "js_challenge"
    MANAGED_CHALLENGE = "managed_challenge"
    LOG = "log"
    SKIP = "skip"


@dataclass(frozen=True)
class ProtectionStatus:
    """Zone DDoS koruma durumu.

    Zone'un mevcut güvenlik seviyesini ve aktif kural sayısını gösterir.
    """

    zone_id: str
    security_level: SecurityLevel
    under_attack_mode: bool
    ddos_l7_enabled: bool
    active_rule_count: int = 0
    last_checked_at: Optional[str] = None  # ISO-8601


@dataclass(frozen=True)
class IPAccessRule:
    """IP erişim kuralı (block/allow/challenge).

    PII: IP adresi loglanırken maskelenir.
    """

    rule_id: str
    ip_address: str
    action: IPAccessAction
    notes: str = ""
    created_at: Optional[str] = None  # ISO-8601


@dataclass(frozen=True)
class IPAccessRuleResult:
    """IP erişim kuralı oluşturma/silme sonucu."""

    rule_id: str
    success: bool
    action: IPAccessAction
    ip_address_masked: str = ""
    message: str = ""


@dataclass(frozen=True)
class SecurityEvent:
    """Güvenlik olayı (DDoS saldırı, bot tespiti, vb.).

    PII: Kaynak IP maskelenir.
    """

    event_id: str
    action: SecurityEventAction
    source_ip_masked: str
    country: str = ""
    uri: str = ""
    user_agent: str = ""
    rule_id: str = ""
    occurred_at: Optional[str] = None  # ISO-8601


@dataclass(frozen=True)
class SecurityEventsPage:
    """Sayfalanmış güvenlik olayları listesi."""

    events: tuple[SecurityEvent, ...] = ()
    total_count: int = 0
    has_more: bool = False
    cursor: str = ""


@dataclass(frozen=True)
class ZoneAnalytics:
    """Zone güvenlik analitikleri (özet).

    Belirli zaman aralığındaki güvenlik metriklerini içerir.
    """

    zone_id: str
    period_start: str  # ISO-8601
    period_end: str  # ISO-8601
    total_requests: int = 0
    blocked_requests: int = 0
    challenged_requests: int = 0
    threats_by_country: dict[str, int] = field(default_factory=dict)
    top_threat_types: dict[str, int] = field(default_factory=dict)


# ------------------------------------------------------------------
# Port Interface
# ------------------------------------------------------------------
class DDoSProtection(ABC):
    """DDoS Protection portu.

    DDoS koruma sağlayıcısını (Cloudflare, AWS Shield vb.) soyutlar.
    Zone güvenlik durumunu yönetir; saldırı anında under-attack modu
    açılır, IP bazlı engelleme/challenge uygulanır.

    Infrastructure katmanı bu interface'i implemente eder:
      - Cloudflare API v4 wrapper
      - Mock/test provider

    Idempotency: Under-attack toggle ve IP kuralları idempotent.
    Retry: Tüm sorgu işlemleri retry-safe (exponential backoff).
      Durum değiştiren işlemler de idempotent olduğu için retry edilir.
    Rate limit: Cloudflare API 1200 req/5min limiti.
    """

    # ------------------------------------------------------------------
    # Koruma durumu sorgulama
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_protection_status(
        self,
        *,
        zone_id: str,
    ) -> ProtectionStatus:
        """Zone'un mevcut DDoS koruma durumunu sorgula.

        Args:
            zone_id: Cloudflare zone ID'si.

        Returns:
            ProtectionStatus: Güncel koruma durumu.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Under-attack modu yönetimi
    # ------------------------------------------------------------------
    @abstractmethod
    async def set_security_level(
        self,
        *,
        zone_id: str,
        level: SecurityLevel,
    ) -> ProtectionStatus:
        """Zone güvenlik seviyesini değiştir.

        Under-attack modu dahil tüm güvenlik seviyeleri ayarlanabilir.
        Bu işlem idempotent'tir: aynı seviye tekrar ayarlanabilir.

        Args:
            zone_id: Cloudflare zone ID'si.
            level: Hedef güvenlik seviyesi.

        Returns:
            ProtectionStatus: Güncelleme sonrası durum.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # IP erişim kuralları
    # ------------------------------------------------------------------
    @abstractmethod
    async def create_ip_access_rule(
        self,
        *,
        zone_id: str,
        ip_address: str,
        action: IPAccessAction,
        notes: str = "",
    ) -> IPAccessRuleResult:
        """IP erişim kuralı oluştur (block/allow/challenge).

        Aynı IP için mevcut kural varsa güncellenir (idempotent).

        Args:
            zone_id: Cloudflare zone ID'si.
            ip_address: Hedef IP adresi veya CIDR bloğu.
            action: Uygulanacak aksiyon (block, challenge, allow).
            notes: Kural notu (audit amaçlı).

        Returns:
            IPAccessRuleResult: Kural oluşturma sonucu.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
            ValueError: Geçersiz IP adresi formatı.
        """

    @abstractmethod
    async def delete_ip_access_rule(
        self,
        *,
        zone_id: str,
        rule_id: str,
    ) -> IPAccessRuleResult:
        """IP erişim kuralını sil.

        Mevcut olmayan kural için hata fırlatmaz (idempotent).

        Args:
            zone_id: Cloudflare zone ID'si.
            rule_id: Silinecek kuralın ID'si.

        Returns:
            IPAccessRuleResult: Silme işlemi sonucu.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    @abstractmethod
    async def list_ip_access_rules(
        self,
        *,
        zone_id: str,
        action: Optional[IPAccessAction] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[IPAccessRule], int]:
        """Zone'daki IP erişim kurallarını listele.

        Args:
            zone_id: Cloudflare zone ID'si.
            action: Filtreleme aksiyonu (opsiyonel).
            page: Sayfa numarası.
            per_page: Sayfa başına kayıt sayısı.

        Returns:
            tuple: (kurallar listesi, toplam kayıt sayısı).

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Güvenlik olayları
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_security_events(
        self,
        *,
        zone_id: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50,
        cursor: str = "",
    ) -> SecurityEventsPage:
        """Zone'daki güvenlik olaylarını listele.

        Zaman aralığına göre filtreleme desteklenir.

        Args:
            zone_id: Cloudflare zone ID'si.
            since: Başlangıç zamanı (opsiyonel, ISO-8601).
            until: Bitiş zamanı (opsiyonel, ISO-8601).
            limit: Döndürülecek maksimum olay sayısı.
            cursor: Sayfalama cursor'ı (sonraki sayfa için).

        Returns:
            SecurityEventsPage: Sayfalanmış güvenlik olayları.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Zone analitikleri
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_zone_analytics(
        self,
        *,
        zone_id: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> ZoneAnalytics:
        """Zone güvenlik analitiklerini al.

        Belirli zaman aralığındaki tehditleri, engellemeleri ve
        ülke bazlı istatistikleri döner.

        Args:
            zone_id: Cloudflare zone ID'si.
            since: Başlangıç zamanı (opsiyonel).
            until: Bitiş zamanı (opsiyonel).

        Returns:
            ZoneAnalytics: Güvenlik analitikleri.

        Raises:
            TimeoutError: Provider yanıt vermediğinde.
            ConnectionError: Bağlantı kurulamadığında.
        """

    # ------------------------------------------------------------------
    # Sağlık kontrolü
    # ------------------------------------------------------------------
    @abstractmethod
    async def health_check(self) -> bool:
        """DDoS koruma sağlayıcısının erişilebilirliğini kontrol et.

        Returns:
            True: Servis sağlıklı ve erişilebilir.
            False: Servis erişilemez veya hata durumunda.
        """
