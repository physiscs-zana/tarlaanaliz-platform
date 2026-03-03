# BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/services/mission_planner.py
# DESC: Mission planlama kuralları.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum


class MissionPlanningError(Exception):
    """Mission planlama domain invariant ihlali."""


class MissionPriority(Enum):
    """Mission öncelik seviyeleri."""

    CRITICAL = "critical"  # Gecikmeli / SLA riski
    HIGH = "high"  # Abonelik takviminde
    NORMAL = "normal"  # Standart talep
    LOW = "low"  # Esnek zamanlama


@dataclass(frozen=True)
class MissionRequest:
    """Mission planlama talebi."""

    field_id: uuid.UUID
    subscription_id: uuid.UUID | None  # Abonelik varsa
    crop_type: str
    province_code: str
    area_m2: float
    priority: MissionPriority = MissionPriority.NORMAL
    earliest_date: date | None = None  # En erken uçuş tarihi
    latest_date: date | None = None  # En geç uçuş tarihi
    requires_calibrated: bool = True  # KR-018


@dataclass(frozen=True)
class PlannedMission:
    """Planlanan mission detayları."""

    mission_request_id: uuid.UUID  # Talep referansı
    field_id: uuid.UUID
    planned_date: date
    pilot_id: uuid.UUID | None  # Atanmışsa
    priority: MissionPriority
    estimated_duration_minutes: int
    notes: str = ""


@dataclass(frozen=True)
class MissionPlanResult:
    """Mission planlama sonucu."""

    planned_missions: tuple[PlannedMission, ...]
    unplanned_requests: tuple[uuid.UUID, ...]  # Planlanamayan talep ID'leri
    warnings: tuple[str, ...]


class MissionPlanner:
    """Mission planlama kuralları servisi.

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.

    Domain invariants:
    - Mission tarihi belirtilen aralıkta olmalıdır.
    - Aynı tarla için aynı gün birden fazla mission planlanamaz.
    - Alan büyüklüğüne göre tahmini süre hesaplanır.
    - Öncelik sıralamasına göre planlama yapılır.
    """

    # Hektar başına tahmini uçuş süresi (dakika)
    MINUTES_PER_HECTARE: float = 15.0
    # Minimum uçuş süresi (dakika)
    MIN_FLIGHT_DURATION: int = 20
    # Maksimum uçuş süresi (dakika)
    MAX_FLIGHT_DURATION: int = 240

    def estimate_duration(self, area_m2: float) -> int:
        """Alan büyüklüğüne göre tahmini uçuş süresi hesaplar.

        Args:
            area_m2: Tarla alanı (m²).

        Returns:
            Tahmini süre (dakika).
        """
        if area_m2 <= 0:
            raise MissionPlanningError("area_m2 pozitif olmalıdır.")

        hectares = area_m2 / 10_000.0
        estimated = int(hectares * self.MINUTES_PER_HECTARE)

        return max(self.MIN_FLIGHT_DURATION, min(estimated, self.MAX_FLIGHT_DURATION))

    def validate_date_window(
        self,
        *,
        planned_date: date,
        earliest_date: date | None,
        latest_date: date | None,
    ) -> bool:
        """Planlanan tarihin geçerli pencere içinde olup olmadığını kontrol eder.

        Args:
            planned_date: Planlanan uçuş tarihi.
            earliest_date: En erken tarih.
            latest_date: En geç tarih.

        Returns:
            Tarih pencere içinde mi.
        """
        if earliest_date and planned_date < earliest_date:
            return False
        if latest_date and planned_date > latest_date:
            return False
        return True

    def plan_missions(
        self,
        requests: list[MissionRequest],
        available_dates: list[date],
        field_existing_dates: dict[uuid.UUID, set[date]] | None = None,
    ) -> MissionPlanResult:
        """Mission taleplerini planlar.

        Basit greedy yaklaşım: önceliğe göre sırala, uygun tarihe ata.

        Args:
            requests: Mission talepleri.
            available_dates: Müsait tarihler (sıralı).
            field_existing_dates: Tarla bazında mevcut mission tarihleri
                                  (çakışma kontrolü için).

        Returns:
            MissionPlanResult: Planlama sonucu.
        """
        if not requests:
            return MissionPlanResult(
                planned_missions=(),
                unplanned_requests=(),
                warnings=(),
            )

        existing_dates = field_existing_dates or {}
        warnings: list[str] = []

        # Önceliğe göre sırala (CRITICAL > HIGH > NORMAL > LOW)
        priority_order = {
            MissionPriority.CRITICAL: 0,
            MissionPriority.HIGH: 1,
            MissionPriority.NORMAL: 2,
            MissionPriority.LOW: 3,
        }
        sorted_requests = sorted(
            requests,
            key=lambda r: priority_order.get(r.priority, 99),
        )

        planned: list[PlannedMission] = []
        unplanned: list[uuid.UUID] = []
        # Her tarih için kullanım sayacı (tarla bazında)
        used_dates: dict[uuid.UUID, set[date]] = {
            fid: set(dates) for fid, dates in existing_dates.items()
        }

        sorted_available = sorted(available_dates)

        for request in sorted_requests:
            request_id = uuid.uuid4()  # Planlama referans ID'si
            assigned_date: date | None = None

            for candidate_date in sorted_available:
                # Tarih penceresi kontrolü
                if not self.validate_date_window(
                    planned_date=candidate_date,
                    earliest_date=request.earliest_date,
                    latest_date=request.latest_date,
                ):
                    continue

                # Aynı tarla aynı gün kontrolü
                field_used = used_dates.get(request.field_id, set())
                if candidate_date in field_used:
                    continue

                assigned_date = candidate_date
                break

            if assigned_date:
                duration = self.estimate_duration(request.area_m2)
                planned.append(
                    PlannedMission(
                        mission_request_id=request_id,
                        field_id=request.field_id,
                        planned_date=assigned_date,
                        pilot_id=None,  # Pilot ataması PlanningEngine'de yapılır
                        priority=request.priority,
                        estimated_duration_minutes=duration,
                    )
                )
                # Kullanılan tarihi işaretle
                if request.field_id not in used_dates:
                    used_dates[request.field_id] = set()
                used_dates[request.field_id].add(assigned_date)
            else:
                unplanned.append(request_id)
                warnings.append(
                    f"Tarla {request.field_id}: uygun tarih bulunamadı "
                    f"(öncelik: {request.priority.value})."
                )

        return MissionPlanResult(
            planned_missions=tuple(planned),
            unplanned_requests=tuple(unplanned),
            warnings=tuple(warnings),
        )

    def calculate_replan_window(
        self,
        *,
        original_date: date,
        replan_reason: str,
        max_delay_days: int = 7,
    ) -> tuple[date, date]:
        """Yeniden planlama penceresi hesaplar.

        Args:
            original_date: Orijinal planlı tarih.
            replan_reason: Yeniden planlama nedeni (WEATHER_BLOCK, PILOT_CANCEL, vb.).
            max_delay_days: Maksimum gecikme günü.

        Returns:
            (earliest_replan_date, latest_replan_date) tuple'ı.
        """
        if max_delay_days <= 0:
            raise MissionPlanningError("max_delay_days > 0 olmalıdır.")

        # Weather block için ertesi gün, diğerleri için 2 gün sonra
        if replan_reason == "WEATHER_BLOCK":
            earliest = original_date + timedelta(days=1)
        else:
            earliest = original_date + timedelta(days=2)

        latest = original_date + timedelta(days=max_delay_days)

        return earliest, latest
