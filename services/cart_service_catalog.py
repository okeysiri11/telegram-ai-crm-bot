# Cart service catalog — AUTO and AGRO services.

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CartService:
    code: str
    title_ru: str
    title_uk: str
    price: Decimal
    currency: str = "USD"


AUTO_SERVICES: tuple[CartService, ...] = (
    CartService("auto_vin_check", "Проверка VIN", "Перевірка VIN", Decimal("25")),
    CartService("auto_insurance", "Консультация по страхованию", "Консультація зі страхування", Decimal("50")),
    CartService("auto_credit", "Подбор кредита", "Підбір кредиту", Decimal("75")),
    CartService("auto_delivery", "Организация доставки", "Організація доставки", Decimal("120")),
    CartService("auto_inspection", "Техосмотр авто", "Техогляд авто", Decimal("90")),
)

AGRO_SERVICES: tuple[CartService, ...] = (
    CartService("agro_consult", "Агро-консультация", "Агро-консультація", Decimal("40")),
    CartService("agro_logistics", "Логистика зерна", "Логістика зерна", Decimal("150")),
    CartService("agro_storage", "Хранение урожая", "Зберігання врожаю", Decimal("100")),
    CartService("agro_quality", "Лабораторный анализ", "Лабораторний аналіз", Decimal("60")),
    CartService("agro_contract", "Подготовка контракта", "Підготовка контракту", Decimal("80")),
)

VERTICAL_SERVICES: dict[str, tuple[CartService, ...]] = {
    "auto": AUTO_SERVICES,
    "agro": AGRO_SERVICES,
}


def services_for_vertical(vertical: str) -> tuple[CartService, ...]:
    return VERTICAL_SERVICES.get(vertical.lower(), AUTO_SERVICES)


def service_by_code(vertical: str, code: str) -> CartService | None:
    for svc in services_for_vertical(vertical):
        if svc.code == code:
            return svc
    return None


def service_title(svc: CartService, lang: str | None = None) -> str:
    if lang == "uk":
        return svc.title_uk
    return svc.title_ru
