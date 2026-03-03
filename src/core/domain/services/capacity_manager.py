# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/services/capacity_manager.py
# DESC: Pilot kapasite hesaplama ve müsaitlik sorgusu (KR-015-1, KR-015-2).

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta


class CapacityError(Exception):
    """Kapasite hesaplama domain invariant ihlali."""


@dataclass(frozen=True)
class PilotCapacity:
    """Pilot kapasite bilgisi."""

    pilot_id: uuid.UUID
    work_days: frozenset[int]  # 0=Pazartesi .. 6=Pazar (ISO weekday - 1)
    daily_capacity: int  # Günlük maksimum görev sayısı
    province_code: str  # Yetki bölgesi


@dataclass(frozen=True)
class PilotAssignment:
    """Mevcut pilot görev ataması."""

    pilot_id: uuid.UUID
    mission_id: uuid.UUID
    scheduled_date: date


@dataclass(frozen=True)
class AvailabilitySlot:
    """Müsait zaman dilimi."""

    pilot_id: uuid.UUID
    date: date
    remaining_capacity: int


@dataclass(frozen=True)
class CapacityCheckResult:
    """Kapasite kontrol sonucu."""

    pilot_id: uuid.UUID
    requested_date: date
    is_available: bool
    current_load: int
    daily_capacity: int
    remaining: int
    reason: str = ""


class CapacityManager:
    """Pilot kapasite hesaplama ve müsaitlik sorgusu servisi (KR-015-1, KR-015-2).

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.

    Domain invariants:
    - Pilot günlük kapasitesini aşamaz.
    - Pilot sadece çalışma günlerinde görev alabilir.
    - Pilot sadece yetki bölgesindeki görevleri alabilir.
    - daily_capacity > 0 olmalıdır.
    """

    def check_availability(
        self,
        pilot: PilotCapacity,
        requested_date: date,
        existing_assignments: list[PilotAssignment],
    ) -> CapacityCheckResult:
        """Belirli bir tarihte pilotun müsaitliğini kontrol eder.

        Args:
            pilot: Pilot kapasite bilgisi.
            requested_date: Talep edilen tarih.
            existing_assignments: Mevcut görev atamaları.

        Returns:
            CapacityCheckResult: Müsaitlik sonucu.
        """
        if pilot.daily_capacity <= 0:
            raise CapacityError(
                f"Pilot {pilot.pilot_id}: daily_capacity > 0 olmalıdır."
            )

        # Çalışma günü kontrolü (weekday: 0=Monday..6=Sunday)
        weekday = requested_date.weekday()
        if weekday not in pilot.work_days:
            return CapacityCheckResult(
                pilot_id=pilot.pilot_id,
                requested_date=requested_date,
                is_available=False,
                current_load=0,
                daily_capacity=pilot.daily_capacity,
                remaining=0,
                reason="Pilotun çalışma günü değil.",
            )

        # O günkü mevcut yük hesabı
        current_load = sum(
            1
            for a in existing_assignments
            if a.pilot_id == pilot.pilot_id and a.scheduled_date == requested_date
        )

        remaining = pilot.daily_capacity - current_load
        is_available = remaining > 0

        reason = "" if is_available else "Günlük kapasite dolu."

        return CapacityCheckResult(
            pilot_id=pilot.pilot_id,
            requested_date=requested_date,
            is_available=is_available,
            current_load=current_load,
            daily_capacity=pilot.daily_capacity,
            remaining=max(0, remaining),
            reason=reason,
        )

    def find_available_slots(
        self,
        pilot: PilotCapacity,
        start_date: date,
        end_date: date,
        existing_assignments: list[PilotAssignment],
    ) -> list[AvailabilitySlot]:
        """Tarih aralığında pilotun müsait slotlarını bulur.

        Args:
            pilot: Pilot kapasite bilgisi.
            start_date: Başlangıç tarihi (dahil).
            end_date: Bitiş tarihi (dahil).
            existing_assignments: Mevcut görev atamaları.

        Returns:
            Müsait slotların listesi.

        Raises:
            CapacityError: start_date > end_date ise.
        """
        if start_date > end_date:
            raise CapacityError("start_date, end_date'den sonra olamaz.")

        slots: list[AvailabilitySlot] = []
        current = start_date

        while current <= end_date:
            result = self.check_availability(pilot, current, existing_assignments)
            if result.is_available:
                slots.append(
                    AvailabilitySlot(
                        pilot_id=pilot.pilot_id,
                        date=current,
                        remaining_capacity=result.remaining,
                    )
                )
            current += timedelta(days=1)

        return slots

    def calculate_utilization(
        self,
        pilot: PilotCapacity,
        start_date: date,
        end_date: date,
        existing_assignments: list[PilotAssignment],
    ) -> float:
        """Tarih aralığında pilotun kullanım oranını hesaplar (0.0 - 1.0).

        Args:
            pilot: Pilot kapasite bilgisi.
            start_date: Başlangıç tarihi (dahil).
            end_date: Bitiş tarihi (dahil).
            existing_assignments: Mevcut görev atamaları.

        Returns:
            Kullanım oranı (0.0 - 1.0).
        """
        if start_date > end_date:
            raise CapacityError("start_date, end_date'den sonra olamaz.")

        total_capacity = 0
        total_used = 0
        current = start_date

        while current <= end_date:
            weekday = current.weekday()
            if weekday in pilot.work_days:
                total_capacity += pilot.daily_capacity
                day_load = sum(
                    1
                    for a in existing_assignments
                    if a.pilot_id == pilot.pilot_id and a.scheduled_date == current
                )
                total_used += min(day_load, pilot.daily_capacity)
            current += timedelta(days=1)

        if total_capacity == 0:
            return 0.0

        return total_used / total_capacity

    def is_province_authorized(
        self,
        pilot: PilotCapacity,
        field_province_code: str,
    ) -> bool:
        """Pilotun belirtilen il için yetkilendirilmiş olup olmadığını kontrol eder.

        Args:
            pilot: Pilot kapasite bilgisi.
            field_province_code: Tarla il kodu.

        Returns:
            Pilot bu ildeki görevleri alabilir mi.
        """
        return pilot.province_code == field_province_code
