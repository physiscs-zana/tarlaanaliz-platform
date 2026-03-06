# PATH: src/core/domain/value_objects/weather_block_status.py
# DESC: WeatherBlockStatus VO; rapor durumu enum.
# SSOT: KR-015-3A (pilot tek yetkili, admin doğrulama kaldırıldı), KR-015-5 (reschedule/force majeure), KR-028 (mission lifecycle)
"""
WeatherBlockStatus value object.

Hava durumu engeli raporunun durumunu temsil eder.
KR-015-3A: Pilot sahada tek yetkili; admin doğrulama akışı kaldırılmıştır.
KR-015-5: Weather block force majeure olarak değerlendirilir;
reschedule token tüketmez.
"""

from __future__ import annotations

from enum import Enum


class WeatherBlockStatus(str, Enum):
    """Hava durumu engeli rapor durumları.

    KR-015-3A: Pilot sahada tek yetkili; admin doğrulama kaldırıldı.

    * REPORTED   -- Pilot tarafından bildirildi (force majeure, token tüketmez).
    * EXPIRED    -- Rapor süresi doldu (zamanında işlenmedi).
    * RESOLVED   -- Hava engeli kalktı; görev yeniden planlanabilir.
    """

    REPORTED = "REPORTED"
    EXPIRED = "EXPIRED"
    RESOLVED = "RESOLVED"


# Geçerli durum geçişleri
VALID_WEATHER_BLOCK_TRANSITIONS: dict[WeatherBlockStatus, frozenset[WeatherBlockStatus]] = {
    WeatherBlockStatus.REPORTED: frozenset(
        {
            WeatherBlockStatus.EXPIRED,
            WeatherBlockStatus.RESOLVED,
        }
    ),
    WeatherBlockStatus.EXPIRED: frozenset(),
    WeatherBlockStatus.RESOLVED: frozenset(),
}

# Terminal durumlar: bu durumlardan çıkış yoktur
TERMINAL_WEATHER_BLOCK_STATUSES: frozenset[WeatherBlockStatus] = frozenset(
    {
        WeatherBlockStatus.EXPIRED,
        WeatherBlockStatus.RESOLVED,
    }
)


def is_valid_weather_block_transition(
    current: WeatherBlockStatus,
    target: WeatherBlockStatus,
) -> bool:
    """Verilen geçiş kurallara uygun mu?"""
    allowed = VALID_WEATHER_BLOCK_TRANSITIONS.get(current, frozenset())
    return target in allowed


def is_force_majeure(status: WeatherBlockStatus) -> bool:
    """Bu durum force majeure (token tüketmeyen reschedule) tetikler mi?

    KR-015-3A: Pilot bildirimi doğrudan force majeure kabul edilir.
    KR-015-5: REPORTED weather block, reschedule token tüketmez.
    """
    return status == WeatherBlockStatus.REPORTED


def is_blocking_mission(status: WeatherBlockStatus) -> bool:
    """Bu durum görevi engelliyor mu?

    REPORTED durumda görev uçurulamaz.
    """
    return status == WeatherBlockStatus.REPORTED
