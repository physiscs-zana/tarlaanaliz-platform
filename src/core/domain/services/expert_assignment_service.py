# PATH: src/core/domain/services/expert_assignment_service.py
# DESC: Analiz sonucu → expert review matching (KR-019).

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


class ExpertAssignmentError(Exception):
    """Expert atama domain invariant ihlali."""


@dataclass(frozen=True)
class ExpertProfile:
    """Expert profil bilgisi (atama kararı için gerekli alanlar).

    PII içermez; sadece yetkinlik ve kapasite bilgileri.
    """

    expert_id: uuid.UUID
    specializations: frozenset[str]  # Uzmanlık alanları (crop type vb.)
    province_code: str  # Yetki bölgesi
    is_active: bool
    current_review_count: int  # Aktif review sayısı
    max_review_capacity: int  # Maksimum eşzamanlı review kapasitesi
    total_completed_reviews: int  # Toplam tamamlanmış review sayısı


@dataclass(frozen=True)
class AssignmentCandidate:
    """Atama adayı (skorlanmış)."""

    expert_id: uuid.UUID
    matching_score: float  # 0.0 - 1.0
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class AssignmentResult:
    """Expert atama sonucu."""

    analysis_job_id: uuid.UUID
    field_id: uuid.UUID
    assigned_expert_id: uuid.UUID | None
    candidates: tuple[AssignmentCandidate, ...]
    success: bool
    reason: str


class ExpertAssignmentService:
    """Analiz sonucu → expert review matching servisi (KR-019).

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.

    Domain invariants:
    - Expert aktif olmalıdır.
    - Expert'in kapasitesi müsait olmalıdır.
    - Expert'in uzmanlık alanı analiz ile eşleşmelidir.
    - Expert bölge yetkisi tarla ile eşleşmelidir.
    - Birden fazla expert gerektiğinde farklı expert'ler atanmalıdır.
    """

    # Skor ağırlıkları
    WEIGHT_SPECIALIZATION: float = 0.40
    WEIGHT_PROVINCE: float = 0.25
    WEIGHT_CAPACITY: float = 0.20
    WEIGHT_EXPERIENCE: float = 0.15

    def assign(
        self,
        *,
        analysis_job_id: uuid.UUID,
        field_id: uuid.UUID,
        crop_type: str,
        field_province_code: str,
        available_experts: list[ExpertProfile],
        required_expert_count: int = 1,
        excluded_expert_ids: frozenset[uuid.UUID] | None = None,
    ) -> AssignmentResult:
        """Analiz sonucu için en uygun expert'i atar.

        Args:
            analysis_job_id: Analiz iş ID'si.
            field_id: Tarla ID'si.
            crop_type: Bitki türü.
            field_province_code: Tarla il kodu.
            available_experts: Müsait expert listesi.
            required_expert_count: Gerekli expert sayısı.
            excluded_expert_ids: Hariç tutulacak expert ID'leri.

        Returns:
            AssignmentResult: Atama sonucu.
        """
        if required_expert_count <= 0:
            raise ExpertAssignmentError("required_expert_count > 0 olmalıdır.")

        excluded = excluded_expert_ids or frozenset()

        # Uygun adayları filtrele ve skorla
        candidates: list[AssignmentCandidate] = []

        for expert in available_experts:
            # Temel filtreler
            if expert.expert_id in excluded:
                continue
            if not expert.is_active:
                continue
            if expert.current_review_count >= expert.max_review_capacity:
                continue

            # Skorlama
            score, reasons = self._calculate_matching_score(
                expert=expert,
                crop_type=crop_type,
                field_province_code=field_province_code,
            )

            candidates.append(
                AssignmentCandidate(
                    expert_id=expert.expert_id,
                    matching_score=score,
                    reasons=tuple(reasons),
                )
            )

        # Skora göre sırala (yüksekten düşüğe)
        candidates.sort(key=lambda c: c.matching_score, reverse=True)

        if not candidates:
            return AssignmentResult(
                analysis_job_id=analysis_job_id,
                field_id=field_id,
                assigned_expert_id=None,
                candidates=(),
                success=False,
                reason="Uygun expert bulunamadı.",
            )

        # En yüksek skorlu expert'i ata
        best = candidates[0]

        return AssignmentResult(
            analysis_job_id=analysis_job_id,
            field_id=field_id,
            assigned_expert_id=best.expert_id,
            candidates=tuple(candidates),
            success=True,
            reason=f"Expert atandı (skor: {best.matching_score:.2f}).",
        )

    def assign_multiple(
        self,
        *,
        analysis_job_id: uuid.UUID,
        field_id: uuid.UUID,
        crop_type: str,
        field_province_code: str,
        available_experts: list[ExpertProfile],
        required_count: int,
    ) -> list[AssignmentResult]:
        """Birden fazla expert ataması yapar (kritik escalation için).

        Her atamada önceki atanan expert'ler hariç tutulur.

        Args:
            analysis_job_id: Analiz iş ID'si.
            field_id: Tarla ID'si.
            crop_type: Bitki türü.
            field_province_code: Tarla il kodu.
            available_experts: Müsait expert listesi.
            required_count: Gerekli expert sayısı.

        Returns:
            Her expert için AssignmentResult listesi.
        """
        results: list[AssignmentResult] = []
        excluded: set[uuid.UUID] = set()

        for _ in range(required_count):
            result = self.assign(
                analysis_job_id=analysis_job_id,
                field_id=field_id,
                crop_type=crop_type,
                field_province_code=field_province_code,
                available_experts=available_experts,
                required_expert_count=1,
                excluded_expert_ids=frozenset(excluded),
            )
            results.append(result)
            if result.assigned_expert_id:
                excluded.add(result.assigned_expert_id)

        return results

    def _calculate_matching_score(
        self,
        expert: ExpertProfile,
        crop_type: str,
        field_province_code: str,
    ) -> tuple[float, list[str]]:
        """Expert-analiz eşleşme skoru hesaplar.

        Returns:
            (score, reasons) tuple'ı.
        """
        score = 0.0
        reasons: list[str] = []

        # Uzmanlık alanı eşleşmesi
        if crop_type and crop_type in expert.specializations:
            score += self.WEIGHT_SPECIALIZATION
            reasons.append(f"Uzmanlık eşleşmesi: {crop_type}")
        elif not crop_type:
            score += self.WEIGHT_SPECIALIZATION * 0.5
            reasons.append("Crop type belirtilmemiş; kısmi skor.")

        # Bölge eşleşmesi
        if expert.province_code == field_province_code:
            score += self.WEIGHT_PROVINCE
            reasons.append(f"Bölge eşleşmesi: {field_province_code}")

        # Kapasite durumu (ne kadar boşsa o kadar yüksek skor)
        if expert.max_review_capacity > 0:
            capacity_ratio = 1.0 - (expert.current_review_count / expert.max_review_capacity)
            score += self.WEIGHT_CAPACITY * max(0.0, capacity_ratio)
            reasons.append(f"Kapasite oranı: {capacity_ratio:.2f}")

        # Deneyim (tamamlanmış review sayısına göre normalize)
        experience_score = min(1.0, expert.total_completed_reviews / 100.0)
        score += self.WEIGHT_EXPERIENCE * experience_score
        reasons.append(f"Deneyim skoru: {experience_score:.2f}")

        return score, reasons
