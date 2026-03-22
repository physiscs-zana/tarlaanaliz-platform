# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-015-5: WeatherBlockReport re-export — deprecated scaffold, gerçek model sqlalchemy/models/ altında.
# Gerçek ORM modeli: src/infrastructure/persistence/sqlalchemy/models/weather_block_model.py
# Eski import'lar için re-export:
from src.infrastructure.persistence.sqlalchemy.models.weather_block_model import (
    WeatherBlockReportModel,
)

__all__ = ["WeatherBlockReportModel"]
