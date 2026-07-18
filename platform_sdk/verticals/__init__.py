# Built-in platform verticals.

from platform_sdk.verticals.agro_vertical import AgroVertical
from platform_sdk.verticals.auto_vertical import AutoVertical
from platform_sdk.verticals.crm_vertical import CrmVertical
from platform_sdk.verticals.legal_vertical import LegalVertical
from platform_sdk.verticals.logistics_vertical import LogisticsVertical
from platform_sdk.verticals.realty_vertical import RealtyVertical

BUILTIN_VERTICALS = (
    AutoVertical,
    AgroVertical,
    RealtyVertical,
    LegalVertical,
    LogisticsVertical,
    CrmVertical,
)

__all__ = [
    "AgroVertical",
    "AutoVertical",
    "BUILTIN_VERTICALS",
    "CrmVertical",
    "LegalVertical",
    "LogisticsVertical",
    "RealtyVertical",
]
