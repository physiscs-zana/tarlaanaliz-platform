# SEC-FIX [H-07]: Merkezi PII log scrubbing altyapısı.
# KR-066: KVKK PII filtreleme — log'lara PII sızmasını önler.
# KR-083: İl operatörü PII göremez.
"""Centralized PII scrubbing for all log output (stdlib logging + structlog).

Bu modül iki katmanlı koruma sağlar:
  1. logging.Filter  — stdlib logging handler'larına eklenir
  2. structlog processor — structlog pipeline'ına eklenir

Her iki katman da aynı _scrub() fonksiyonunu kullanır.
"""

from __future__ import annotations

import logging
import re
from typing import Any


# ---------------------------------------------------------------------------
# PII tanımlama kuralları
# ---------------------------------------------------------------------------

# Alan adlarıyla eşleşen PII key'leri (case-insensitive kontrol edilir)
_PII_KEYS: frozenset[str] = frozenset(
    {
        "phone",
        "phone_number",
        "telefon",
        "tc_kimlik_no",
        "tckn",
        "national_id",
        "iban",
        "email",
        "e_posta",
        "full_name",
        "ad_soyad",
        "address",
        "adres",
        "gps_lat",
        "gps_lon",
        "gps_latitude",
        "gps_longitude",
        "latitude",
        "longitude",
        "pin",
        "pin_hash",
        "phone_tail",
        "field_id",
    }
)

# Türkiye telefon numarası pattern'i — log mesajı string'lerinde aranır
_PHONE_RE = re.compile(
    r"(?<!\d)"                     # rakamla başlamayan
    r"(?:\+90|0)?"                 # ülke kodu veya 0 prefix (opsiyonel)
    r"[5]\d{2}"                    # operatör kodu
    r"[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"  # numara
    r"(?!\d)"                      # rakamla bitmeyen
)

_REPLACEMENT = "***PII***"


# ---------------------------------------------------------------------------
# Scrub fonksiyonları
# ---------------------------------------------------------------------------

def _mask_phone_in_text(text: str) -> str:
    """Log mesajı string'i içindeki telefon numaralarını maskeler."""
    return _PHONE_RE.sub("05XX-XXX-XXXX", text)


def _scrub_value(key: str, value: Any) -> Any:
    """Tek bir key-value çiftini PII açısından temizler."""
    if key.lower() in _PII_KEYS:
        return _REPLACEMENT
    if isinstance(value, str):
        return _mask_phone_in_text(value)
    return value


def _scrub_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Dict içindeki tüm PII alanlarını recursive olarak temizler."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in _PII_KEYS:
            result[key] = _REPLACEMENT
        elif isinstance(value, dict):
            result[key] = _scrub_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _scrub_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, str):
            result[key] = _mask_phone_in_text(value)
        else:
            result[key] = value
    return result


def _scrub_message(msg: str) -> str:
    """Log mesajı string'indeki phone=..., pin=... gibi PII pattern'lerini temizler."""
    # phone=05325551234 veya phone=+905325551234 pattern'leri
    msg = re.sub(
        r"(phone|telefon|pin|tckn|iban|email)\s*=\s*\S+",
        r"\1=***PII***",
        msg,
        flags=re.IGNORECASE,
    )
    # Kalan telefon numaralarını maskele
    msg = _mask_phone_in_text(msg)
    return msg


# ---------------------------------------------------------------------------
# stdlib logging.Filter — tüm handler'lara eklenir
# ---------------------------------------------------------------------------

class PIILogFilter(logging.Filter):
    """stdlib logging Filter: log record'larından PII temizler.

    Kullanım:
        handler.addFilter(PIILogFilter())
    veya logging.yaml'da:
        filters:
          pii_scrub:
            (): src.infrastructure.security.pii_log_scrubber.PIILogFilter
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # 1. Ana mesajı temizle
        if isinstance(record.msg, str):
            record.msg = _scrub_message(record.msg)

        # 2. Args içindeki PII'yi temizle (format string %s parametreleri)
        if record.args:
            if isinstance(record.args, dict):
                record.args = _scrub_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    _mask_phone_in_text(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )

        # 3. Extra dict içindeki PII key'leri temizle
        for attr in list(vars(record)):
            if attr.lower() in _PII_KEYS:
                setattr(record, attr, _REPLACEMENT)

        # 4. exc_text içindeki PII'yi temizle (exception mesajları)
        if record.exc_text and isinstance(record.exc_text, str):
            record.exc_text = _scrub_message(record.exc_text)

        return True  # Her zaman log'a yaz, sadece PII'yi temizle


# ---------------------------------------------------------------------------
# structlog processor — structlog.configure() pipeline'ına eklenir
# ---------------------------------------------------------------------------

def structlog_pii_scrubber(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """structlog processor: event_dict'ten PII temizler.

    Kullanım:
        structlog.configure(
            processors=[
                ...,
                structlog_pii_scrubber,
                ...,
            ]
        )
    """
    # Event mesajını temizle
    if "event" in event_dict and isinstance(event_dict["event"], str):
        event_dict["event"] = _scrub_message(event_dict["event"])

    # Tüm key'leri kontrol et
    for key in list(event_dict.keys()):
        if key.lower() in _PII_KEYS:
            event_dict[key] = _REPLACEMENT
        elif isinstance(event_dict[key], str):
            event_dict[key] = _mask_phone_in_text(event_dict[key])
        elif isinstance(event_dict[key], dict):
            event_dict[key] = _scrub_dict(event_dict[key])

    # exc_info içindeki exception mesajını temizle
    if "exc_info" in event_dict and event_dict["exc_info"]:
        exc = event_dict["exc_info"]
        if isinstance(exc, BaseException):
            exc_msg = str(exc)
            scrubbed = _scrub_message(exc_msg)
            if scrubbed != exc_msg:
                event_dict["exc_info_scrubbed"] = scrubbed

    return event_dict


# ---------------------------------------------------------------------------
# Kurulum yardımcıları
# ---------------------------------------------------------------------------

def install_on_all_handlers() -> None:
    """Mevcut tüm logging handler'larına PIILogFilter ekler.

    Uygulama başlangıcında bir kez çağrılmalıdır.
    """
    pii_filter = PIILogFilter()
    root = logging.getLogger()

    # Root logger handler'ları
    for handler in root.handlers:
        handler.addFilter(pii_filter)

    # Bilinen logger'ların handler'ları
    for name in list(logging.Logger.manager.loggerDict):
        lgr = logging.getLogger(name)
        for handler in lgr.handlers:
            handler.addFilter(pii_filter)
