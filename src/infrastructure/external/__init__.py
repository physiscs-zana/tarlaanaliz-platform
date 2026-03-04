# PATH: src/infrastructure/external/__init__.py
"""Infrastructure external adapters package: dış servis implementasyonları.

Port interface'leri core'da tanımlıdır; burada yalnızca implementasyonlar bulunur.
"""

from src.infrastructure.external.av_scanner_client import AVScannerClient
from src.infrastructure.external.payment_gateway_adapter import PaymentGatewayAdapter
from src.infrastructure.external.sms_gateway_adapter import SMSGatewayAdapter
from src.infrastructure.external.storage_adapter import S3StorageAdapter
from src.infrastructure.external.tkgm_megsis_wfs_adapter import TKGMMegsisWFSAdapter
from src.infrastructure.external.weather_api_adapter import WeatherAPIAdapter, WeatherData

__all__: list[str] = [
    "AVScannerClient",
    "PaymentGatewayAdapter",
    "SMSGatewayAdapter",
    "S3StorageAdapter",
    "TKGMMegsisWFSAdapter",
    "WeatherAPIAdapter",
    "WeatherData",
]
