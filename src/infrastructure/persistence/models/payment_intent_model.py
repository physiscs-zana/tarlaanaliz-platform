# PATH: src/infrastructure/persistence/models/payment_intent_model.py
# DESC: PaymentIntent DB modeli re-export (KR-033).
# Kanonik implementasyon: src/infrastructure/persistence/sqlalchemy/models/payment_intent_model.py
"""PaymentIntent model re-export — kanonik modul sqlalchemy/models altindadir."""

from src.infrastructure.persistence.sqlalchemy.models.payment_intent_model import PaymentIntentModel

__all__ = ["PaymentIntentModel"]
