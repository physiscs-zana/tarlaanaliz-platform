# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-022: Fiyat hesaplama – config bridge between admin pricing config and domain PricebookCalculator.
"""Pricing service helper: bridges admin pricing config with domain PricebookCalculator."""

from __future__ import annotations

import logging
import uuid
from uuid import UUID

from src.core.domain.services.pricebook_calculator import (
    PricebookCalculator,
    PricebookError,
    PriceRule,
)
from src.presentation.api.v1.endpoints.admin_pricing import _read_config

logger = logging.getLogger(__name__)


def _build_single_rules(config: dict[str, object]) -> list[PriceRule]:
    """Convert pricing config crops into PriceRule objects for single analysis."""
    rules: list[PriceRule] = []
    crops = config.get("crops", [])
    if not isinstance(crops, list):
        logger.warning("PRICING_CONFIG_INVALID: 'crops' is not a list, returning empty rules")
        return rules

    for crop in crops:
        if not isinstance(crop, dict):
            continue
        code = crop.get("code", "")
        single_price = crop.get("single_price", 0)
        if not code or not isinstance(single_price, (int, float)) or single_price <= 0:
            logger.warning("PRICING_RULE_SKIP: invalid crop entry code=%s", code)
            continue
        rules.append(
            PriceRule(
                rule_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"single.{code}"),
                crop_type=str(code),
                base_price_per_hectare_kurus=int(single_price * 100),
                min_area_m2=0.0,
                max_area_m2=None,
            ),
        )
    return rules


def _build_seasonal_rules(config: dict[str, object]) -> list[PriceRule]:
    """Convert pricing config crops into PriceRule objects for seasonal subscription."""
    rules: list[PriceRule] = []
    crops = config.get("crops", [])
    if not isinstance(crops, list):
        logger.warning("PRICING_CONFIG_INVALID: 'crops' is not a list, returning empty rules")
        return rules

    for crop in crops:
        if not isinstance(crop, dict):
            continue
        code = crop.get("code", "")
        seasonal_price = crop.get("seasonal_price", 0)
        if not code or not isinstance(seasonal_price, (int, float)) or seasonal_price <= 0:
            logger.warning("PRICING_RULE_SKIP: invalid seasonal crop entry code=%s", code)
            continue
        rules.append(
            PriceRule(
                rule_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"seasonal.{code}"),
                crop_type=str(code),
                base_price_per_hectare_kurus=int(seasonal_price * 100),
                min_area_m2=0.0,
                max_area_m2=None,
            ),
        )
    return rules


def calculate_single_price(field_id: UUID, crop_type: str, area_m2: float) -> int:
    """Calculate amount_kurus for a single analysis.

    Reads the pricing config, builds single-price rules, and delegates to
    PricebookCalculator.calculate_price.

    Returns:
        Total amount in kurus (int). Returns 0 if pricing fails.
    """
    try:
        config = _read_config()
        rules = _build_single_rules(config)
        if not rules:
            logger.warning("PRICING_NO_RULES: no single-price rules found in config")
            return 0

        calculator = PricebookCalculator(rules=rules)
        result = calculator.calculate_price(
            field_id=field_id,
            crop_type=crop_type,
            area_m2=area_m2,
        )
        return result.total_amount_kurus
    except PricebookError as exc:
        logger.warning("PRICING_CALC_FAILED: field_id=%s crop=%s area=%s err=%s", field_id, crop_type, area_m2, exc)
        return 0
    except Exception:
        logger.warning("PRICING_UNEXPECTED: field_id=%s crop=%s area=%s", field_id, crop_type, area_m2, exc_info=True)
        return 0


def calculate_subscription_price(
    field_id: UUID,
    crop_type: str,
    area_m2: float,
    total_analyses: int,
) -> int:
    """Calculate amount_kurus for a seasonal subscription.

    Reads the pricing config, builds seasonal-price rules, and delegates to
    PricebookCalculator.calculate_subscription_price.

    Returns:
        Total amount in kurus (int). Returns 0 if pricing fails.
    """
    try:
        config = _read_config()
        rules = _build_seasonal_rules(config)
        if not rules:
            logger.warning("PRICING_NO_RULES: no seasonal-price rules found in config")
            return 0

        calculator = PricebookCalculator(rules=rules)
        result = calculator.calculate_subscription_price(
            field_id=field_id,
            crop_type=crop_type,
            area_m2=area_m2,
            total_analyses=total_analyses,
        )
        return result.total_amount_kurus
    except PricebookError as exc:
        logger.warning(
            "PRICING_SUB_CALC_FAILED: field_id=%s crop=%s area=%s analyses=%d err=%s",
            field_id,
            crop_type,
            area_m2,
            total_analyses,
            exc,
        )
        return 0
    except Exception:
        logger.warning(
            "PRICING_SUB_UNEXPECTED: field_id=%s crop=%s area=%s analyses=%d",
            field_id,
            crop_type,
            area_m2,
            total_analyses,
            exc_info=True,
        )
        return 0
