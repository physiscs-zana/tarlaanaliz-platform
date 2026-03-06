# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/value_objects/role.py
# DESC: Role VO; RBAC rolleri ve yetki kapsamları.
# SSOT: TARLAANALIZ_SSOT_v1_2_0.txt — KR-063 (13 rol, v1.2.0)
"""
Role value object.

KR-063 kanonik RBAC rol matrisini temsil eder (v1.2.0: 13 rol).
Entity katmanındaki UserRole enum'u ile SSOT uyumludur;
bu VO domain genelinde taşınabilir referans noktasıdır.
Roller ve yetki kapsamları platform genelinde tutarlıdır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


class RoleError(Exception):
    """Role domain invariant ihlali."""


@dataclass(frozen=True)
class Role:
    """RBAC rol değer nesnesi (KR-063).

    Immutable (frozen=True); oluşturulduktan sonra değiştirilemez.
    Domain core'da dış dünya erişimi yoktur (IO, log yok).

    KR-063 kanonik roller (v1.2.0 — 13 rol):
    - FARMER_SINGLE: Bireysel çiftçi
    - FARMER_MEMBER: Kurum üyesi çiftçi (KR-014)
    - COOP_OWNER: Kooperatif sahibi
    - COOP_ADMIN: Kooperatif yöneticisi
    - COOP_AGRONOMIST: Kooperatif ziraat mühendisi
    - COOP_VIEWER: Kooperatif izleyicisi (salt okunur)
    - PILOT: Drone pilotu
    - STATION_OPERATOR: İstasyon operatörü
    - IL_OPERATOR: İl operatörü
    - BILLING_ADMIN: Ödeme yöneticisi (KR-033, KR-083)
    - CENTRAL_ADMIN: Merkez yönetici
    - AI_SERVICE: AI servis hesabı
    - EXPERT: Uzman (KR-019 expert review)

    Invariants:
    - code, tanımlı geçerli rol kodlarından biri olmalıdır.
    """

    code: str

    # Sabit rol kodları (KR-063 v1.2.0 — 13 rol)
    FARMER_SINGLE: ClassVar[str] = "FARMER_SINGLE"
    FARMER_MEMBER: ClassVar[str] = "FARMER_MEMBER"
    COOP_OWNER: ClassVar[str] = "COOP_OWNER"
    COOP_ADMIN: ClassVar[str] = "COOP_ADMIN"
    COOP_AGRONOMIST: ClassVar[str] = "COOP_AGRONOMIST"
    COOP_VIEWER: ClassVar[str] = "COOP_VIEWER"
    PILOT: ClassVar[str] = "PILOT"
    STATION_OPERATOR: ClassVar[str] = "STATION_OPERATOR"
    IL_OPERATOR: ClassVar[str] = "IL_OPERATOR"
    BILLING_ADMIN: ClassVar[str] = "BILLING_ADMIN"
    CENTRAL_ADMIN: ClassVar[str] = "CENTRAL_ADMIN"
    AI_SERVICE: ClassVar[str] = "AI_SERVICE"
    EXPERT: ClassVar[str] = "EXPERT"

    _VALID_CODES: ClassVar[frozenset[str]] = frozenset(
        {
            "FARMER_SINGLE",
            "FARMER_MEMBER",
            "COOP_OWNER",
            "COOP_ADMIN",
            "COOP_AGRONOMIST",
            "COOP_VIEWER",
            "PILOT",
            "STATION_OPERATOR",
            "IL_OPERATOR",
            "BILLING_ADMIN",
            "CENTRAL_ADMIN",
            "AI_SERVICE",
            "EXPERT",
        }
    )

    # Rol -> Türkçe görünen ad eşlemesi
    _DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        "FARMER_SINGLE": "Bireysel Çiftçi",
        "FARMER_MEMBER": "Kurum Üyesi Çiftçi",
        "COOP_OWNER": "Kooperatif Sahibi",
        "COOP_ADMIN": "Kooperatif Yöneticisi",
        "COOP_AGRONOMIST": "Kooperatif Ziraat Mühendisi",
        "COOP_VIEWER": "Kooperatif İzleyicisi",
        "PILOT": "Drone Pilotu",
        "STATION_OPERATOR": "İstasyon Operatörü",
        "IL_OPERATOR": "İl Operatörü",
        "BILLING_ADMIN": "Ödeme Yöneticisi",
        "CENTRAL_ADMIN": "Merkez Yönetici",
        "AI_SERVICE": "AI Servis Hesabı",
        "EXPERT": "Uzman",
    }

    # Yetki grupları
    _FARMER_ROLES: ClassVar[frozenset[str]] = frozenset(
        {
            "FARMER_SINGLE",
            "FARMER_MEMBER",
        }
    )

    _COOP_ROLES: ClassVar[frozenset[str]] = frozenset(
        {
            "COOP_OWNER",
            "COOP_ADMIN",
            "COOP_AGRONOMIST",
            "COOP_VIEWER",
        }
    )

    _OPERATOR_ROLES: ClassVar[frozenset[str]] = frozenset(
        {
            "STATION_OPERATOR",
            "IL_OPERATOR",
            "CENTRAL_ADMIN",
        }
    )

    _ADMIN_ROLES: ClassVar[frozenset[str]] = frozenset(
        {
            "COOP_ADMIN",
            "BILLING_ADMIN",
            "CENTRAL_ADMIN",
        }
    )

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise RoleError(f"code str olmalıdır, alınan tip: {type(self.code).__name__}")
        normalized = self.code.strip().upper()
        if normalized != self.code:
            object.__setattr__(self, "code", normalized)
        if self.code not in self._VALID_CODES:
            raise RoleError(f"Geçersiz rol: '{self.code}'. Geçerli değerler: {sorted(self._VALID_CODES)}")

    # ------------------------------------------------------------------
    # Domain queries
    # ------------------------------------------------------------------
    @property
    def display_name(self) -> str:
        """Türkçe görünen ad."""
        return self._DISPLAY_NAMES[self.code]

    @property
    def is_farmer(self) -> bool:
        """Çiftçi rolü mü?"""
        return self.code in self._FARMER_ROLES

    @property
    def is_coop_member(self) -> bool:
        """Kooperatif üyesi rolü mü?"""
        return self.code in self._COOP_ROLES

    @property
    def is_operator(self) -> bool:
        """Operatör rolü mü?"""
        return self.code in self._OPERATOR_ROLES

    @property
    def is_admin(self) -> bool:
        """Yönetici rolü mü?"""
        return self.code in self._ADMIN_ROLES

    @property
    def is_system_account(self) -> bool:
        """Sistem hesabı mı? (AI_SERVICE)."""
        return self.code == self.AI_SERVICE

    @property
    def requires_coop_context(self) -> bool:
        """Bu rol kooperatif bağlamı gerektiriyor mu?"""
        return self.code in self._COOP_ROLES

    def can_manage_role(self, target: Role) -> bool:
        """Bu rol, hedef rolü yönetebilir mi? (KR-063 basit kural).

        CENTRAL_ADMIN: tüm rolleri yönetir.
        COOP_ADMIN: kendi kooperatif rollerini yönetir.
        Diğerleri: rol yönetim yetkisi yok.
        """
        if self.code == self.CENTRAL_ADMIN:
            return True
        if self.code == self.COOP_ADMIN:
            return target.code in self._COOP_ROLES or target.is_farmer
        return False

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Serileştirme için dict dönüşümü."""
        return {
            "code": self.code,
            "display_name": self.display_name,
        }

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"Role(code='{self.code}')"
