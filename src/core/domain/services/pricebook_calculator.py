# PATH: src/core/domain/services/pricebook_calculator.py
# DESC: Fiyat hesaplama ve snapshot oluşturma (KR-022).

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


class PricebookError(Exception):
    """Fiyat hesaplama domain invariant ihlali."""


@dataclass(frozen=True)
class PriceRule:
    """Fiyat kuralı (ürün/hizmet bazında).

    Tüm tutarlar kuruş cinsindendir (TRY).
    """

    rule_id: uuid.UUID
    crop_type: str  # Bitki türü (boş ise genel kural)
    base_price_per_hectare_kurus: int  # Hektar başına baz fiyat (kuruş)
    min_area_m2: float  # Minimum alan (m²)
    max_area_m2: float | None  # Maksimum alan (None = sınırsız)
    discount_percentage: float = 0.0  # %0 - %100 arası indirim
    currency: str = "TRY"

    def __post_init__(self) -> None:
        if self.base_price_per_hectare_kurus <= 0:
            raise PricebookError("base_price_per_hectare_kurus > 0 olmalıdır.")
        if self.min_area_m2 < 0:
            raise PricebookError("min_area_m2 negatif olamaz.")
        if self.max_area_m2 is not None and self.max_area_m2 <= self.min_area_m2:
            raise PricebookError("max_area_m2, min_area_m2'den büyük olmalıdır.")
        if not 0.0 <= self.discount_percentage <= 100.0:
            raise PricebookError("discount_percentage 0-100 arasında olmalıdır.")


@dataclass(frozen=True)
class PriceCalculation:
    """Fiyat hesaplama sonucu."""

    field_id: uuid.UUID
    crop_type: str
    area_m2: float
    area_hectares: float
    base_amount_kurus: int
    discount_amount_kurus: int
    total_amount_kurus: int
    currency: str
    rule_id: uuid.UUID
    calculated_at: datetime


@dataclass(frozen=True)
class PriceSnapshotData:
    """Fiyat snapshot verisi (immutable, KR-022).

    Sipariş anında alınan fiyat bilgisi; sonradan değişemez.
    """

    snapshot_id: uuid.UUID
    field_id: uuid.UUID
    subscription_id: uuid.UUID | None
    crop_type: str
    area_m2: float
    unit_price_kurus: int  # Hektar başına birim fiyat
    total_amount_kurus: int
    discount_percentage: float
    currency: str
    rule_id: uuid.UUID
    captured_at: datetime


class PricebookCalculator:
    """Fiyat hesaplama ve snapshot oluşturma servisi (KR-022).

    Tek entity'ye sığmayan saf iş mantığı; policy ve hesaplamalar.

    Domain invariants:
    - Fiyat her zaman pozitif olmalıdır.
    - Snapshot oluşturulduktan sonra değiştirilemez.
    - Crop type ve alan büyüklüğü eşleşen kural kullanılır.
    - Birden fazla kural eşleşirse en spesifik olan seçilir.
    - Tüm tutarlar kuruş cinsindendir.
    """

    def __init__(self, rules: list[PriceRule] | None = None) -> None:
        self._rules = list(rules) if rules else []

    @property
    def rules(self) -> list[PriceRule]:
        return list(self._rules)

    def add_rule(self, rule: PriceRule) -> None:
        """Yeni fiyat kuralı ekler."""
        self._rules.append(rule)

    def find_matching_rule(
        self,
        crop_type: str,
        area_m2: float,
    ) -> PriceRule | None:
        """Crop type ve alan büyüklüğüne uygun kuralı bulur.

        Öncelik: crop_type eşleşen > genel kural.
        Alan aralığı: min_area_m2 <= area <= max_area_m2.

        Args:
            crop_type: Bitki türü.
            area_m2: Tarla alanı (m²).

        Returns:
            Eşleşen fiyat kuralı veya None.
        """
        specific_matches: list[PriceRule] = []
        general_matches: list[PriceRule] = []

        for rule in self._rules:
            # Alan kontrolü
            if area_m2 < rule.min_area_m2:
                continue
            if rule.max_area_m2 is not None and area_m2 > rule.max_area_m2:
                continue

            if rule.crop_type and rule.crop_type == crop_type:
                specific_matches.append(rule)
            elif not rule.crop_type:
                general_matches.append(rule)

        # Spesifik eşleşme öncelikli
        if specific_matches:
            return specific_matches[0]
        if general_matches:
            return general_matches[0]

        return None

    def calculate_price(
        self,
        *,
        field_id: uuid.UUID,
        crop_type: str,
        area_m2: float,
    ) -> PriceCalculation:
        """Fiyat hesaplar.

        Args:
            field_id: Tarla ID.
            crop_type: Bitki türü.
            area_m2: Tarla alanı (m²).

        Returns:
            PriceCalculation: Hesaplama sonucu.

        Raises:
            PricebookError: Kural bulunamazsa veya alan geçersizse.
        """
        if area_m2 <= 0:
            raise PricebookError("area_m2 pozitif olmalıdır.")

        rule = self.find_matching_rule(crop_type, area_m2)
        if not rule:
            raise PricebookError(f"Fiyat kuralı bulunamadı: crop_type={crop_type}, area_m2={area_m2}")

        area_hectares = area_m2 / 10_000.0
        base_amount = int(area_hectares * rule.base_price_per_hectare_kurus)
        discount_amount = int(base_amount * rule.discount_percentage / 100.0)
        total_amount = base_amount - discount_amount

        if total_amount <= 0:
            raise PricebookError("Hesaplanan toplam tutar pozitif olmalıdır.")

        return PriceCalculation(
            field_id=field_id,
            crop_type=crop_type,
            area_m2=area_m2,
            area_hectares=area_hectares,
            base_amount_kurus=base_amount,
            discount_amount_kurus=discount_amount,
            total_amount_kurus=total_amount,
            currency=rule.currency,
            rule_id=rule.rule_id,
            calculated_at=datetime.now(timezone.utc),
        )

    def create_snapshot(
        self,
        *,
        calculation: PriceCalculation,
        subscription_id: uuid.UUID | None = None,
    ) -> PriceSnapshotData:
        """Fiyat hesaplamasından immutable snapshot oluşturur (KR-022).

        Snapshot sipariş anında alınır ve değiştirilemez.

        Args:
            calculation: Fiyat hesaplama sonucu.
            subscription_id: İlişkili abonelik ID'si.

        Returns:
            PriceSnapshotData: Fiyat snapshot'ı.
        """
        rule = self.find_matching_rule(calculation.crop_type, calculation.area_m2)
        unit_price = rule.base_price_per_hectare_kurus if rule else 0
        discount_pct = rule.discount_percentage if rule else 0.0

        return PriceSnapshotData(
            snapshot_id=uuid.uuid4(),
            field_id=calculation.field_id,
            subscription_id=subscription_id,
            crop_type=calculation.crop_type,
            area_m2=calculation.area_m2,
            unit_price_kurus=unit_price,
            total_amount_kurus=calculation.total_amount_kurus,
            discount_percentage=discount_pct,
            currency=calculation.currency,
            rule_id=calculation.rule_id,
            captured_at=datetime.now(timezone.utc),
        )

    def calculate_subscription_price(
        self,
        *,
        field_id: uuid.UUID,
        crop_type: str,
        area_m2: float,
        total_analyses: int,
    ) -> PriceCalculation:
        """Abonelik toplam fiyatını hesaplar.

        Args:
            field_id: Tarla ID.
            crop_type: Bitki türü.
            area_m2: Tarla alanı (m²).
            total_analyses: Toplam analiz sayısı.

        Returns:
            PriceCalculation: Toplam abonelik fiyatı.

        Raises:
            PricebookError: Geçersiz parametre.
        """
        if total_analyses <= 0:
            raise PricebookError("total_analyses > 0 olmalıdır.")

        single = self.calculate_price(
            field_id=field_id,
            crop_type=crop_type,
            area_m2=area_m2,
        )

        total_base = single.base_amount_kurus * total_analyses
        total_discount = single.discount_amount_kurus * total_analyses
        total_amount = single.total_amount_kurus * total_analyses

        return PriceCalculation(
            field_id=field_id,
            crop_type=crop_type,
            area_m2=area_m2,
            area_hectares=single.area_hectares,
            base_amount_kurus=total_base,
            discount_amount_kurus=total_discount,
            total_amount_kurus=total_amount,
            currency=single.currency,
            rule_id=single.rule_id,
            calculated_at=datetime.now(timezone.utc),
        )
