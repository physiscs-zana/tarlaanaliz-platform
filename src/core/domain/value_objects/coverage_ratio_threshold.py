# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/core/domain/value_objects/coverage_ratio_threshold.py
# DESC: CoverageRatioThreshold VO; KR-031 uçuş kapsama eşikleri.
# SSOT: TARLAANALIZ_SSOT_v1_2_0.txt — KR-031 (Pilot ödeme ve kapsama oranı)
"""
CoverageRatioThreshold value object.

KR-031: Pilot hakedişini belirleyen kapsama oranı eşikleri.

  ≥ 0.95  → FULL_PAY     (tam ödeme)
  0.80 – 0.95 → PARTIAL_REVIEW (kısmi ödeme + manuel inceleme)
  < 0.80  → REFLY        (tekrar uçuş zorunlu veya itiraz)

coverage_ratio: gerçek kapsanan alan / planlanan toplam alan (0.0 – 1.0)
"""

from __future__ import annotations

from enum import Enum


class CoverageOutcome(str, Enum):
    """Kapsama oranına göre hakediş kararı (KR-031)."""

    FULL_PAY = "FULL_PAY"  # coverage_ratio >= 0.95
    PARTIAL_REVIEW = "PARTIAL_REVIEW"  # 0.80 <= coverage_ratio < 0.95
    REFLY = "REFLY"  # coverage_ratio < 0.80


# Eşik sabitleri (KR-031)
COVERAGE_FULL_PAY_THRESHOLD: float = 0.95
COVERAGE_PARTIAL_THRESHOLD: float = 0.80


def evaluate_coverage(coverage_ratio: float) -> CoverageOutcome:
    """Kapsama oranından hakediş kararını belirle (KR-031).

    Args:
        coverage_ratio: 0.0 – 1.0 arası kapsama oranı.
                        (gerçek kapsanan alan / planlanan alan)

    Returns:
        CoverageOutcome: FULL_PAY | PARTIAL_REVIEW | REFLY

    Raises:
        ValueError: coverage_ratio 0.0 – 1.0 dışındaysa.
    """
    if not (0.0 <= coverage_ratio <= 1.0):
        raise ValueError(f"coverage_ratio 0.0 ile 1.0 arasında olmalıdır, alınan: {coverage_ratio}")

    if coverage_ratio >= COVERAGE_FULL_PAY_THRESHOLD:
        return CoverageOutcome.FULL_PAY
    if coverage_ratio >= COVERAGE_PARTIAL_THRESHOLD:
        return CoverageOutcome.PARTIAL_REVIEW
    return CoverageOutcome.REFLY


def is_payable(coverage_ratio: float) -> bool:
    """Bu kapsama oranı herhangi bir ödemeye hak kazandırıyor mu?

    REFLY durumunda hakediş oluşmaz.
    """
    return evaluate_coverage(coverage_ratio) != CoverageOutcome.REFLY


def requires_manual_review(coverage_ratio: float) -> bool:
    """Kısmi kapsama nedeniyle manuel inceleme gerekiyor mu?"""
    return evaluate_coverage(coverage_ratio) == CoverageOutcome.PARTIAL_REVIEW
