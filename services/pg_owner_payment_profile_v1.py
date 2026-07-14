# Owner Payment Profile v1 — settings, client instructions, method toggles.

from __future__ import annotations

import re
import uuid
from decimal import Decimal
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models.owner_payment_profile_v1 import (
    METHOD_ENABLE_FIELDS,
    OwnerPaymentProfileV1,
)
from database.models.payment_engine_v1 import PaymentEngineMethod
from database.session import get_session
from repositories.owner_payment_profile_v1_repository import OwnerPaymentProfileV1Repository

_PAYMENT_METHOD_LABELS: dict[str, dict[str, str]] = {
    "CARD": {"ru": "💳 Карта", "uk": "💳 Картка"},
    "IBAN": {"ru": "🏦 IBAN", "uk": "🏦 IBAN"},
    "USDT_TRC20": {"ru": "💎 USDT TRC20", "uk": "💎 USDT TRC20"},
    "USDT_ERC20": {"ru": "💎 USDT ERC20", "uk": "💎 USDT ERC20"},
    "CASH": {"ru": "💵 Наличные", "uk": "💵 Готівка"},
}

_EDITABLE_FIELDS = frozenset({
    "card_holder_name",
    "card_mask",
    "iban",
    "usdt_trc20_wallet",
    "usdt_erc20_wallet",
    "cash_instructions",
})


class OwnerPaymentProfileV1Error(Exception):
    pass


class OwnerPaymentProfileEngineV1:
    @staticmethod
    async def get_profile() -> dict[str, Any]:
        async with get_session() as session:
            row = await OwnerPaymentProfileV1Repository(session).get_or_create_singleton()
        return OwnerPaymentProfileEngineV1._snapshot(row)

    @staticmethod
    async def update_field(field: str, value: str) -> dict[str, Any]:
        if field not in _EDITABLE_FIELDS:
            raise OwnerPaymentProfileV1Error(f"Unsupported field: {field}")
        cleaned = value.strip()
        if not cleaned:
            raise OwnerPaymentProfileV1Error("Значение не может быть пустым")
        if field == "card_mask":
            cleaned = OwnerPaymentProfileEngineV1._validate_card_mask(cleaned)

        async with get_session() as session:
            repo = OwnerPaymentProfileV1Repository(session)
            row = await repo.get_or_create_singleton()
            updated = await repo.update(row.id, **{field: cleaned})
        return OwnerPaymentProfileEngineV1._snapshot(updated)

    @staticmethod
    async def toggle_method(method: str) -> dict[str, Any]:
        method = method.upper()
        field = METHOD_ENABLE_FIELDS.get(method)
        if field is None:
            raise OwnerPaymentProfileV1Error(f"Unsupported method: {method}")

        async with get_session() as session:
            repo = OwnerPaymentProfileV1Repository(session)
            row = await repo.get_or_create_singleton()
            current = bool(getattr(row, field))
            if current:
                other_enabled = any(
                    getattr(row, other_field)
                    for other_method, other_field in METHOD_ENABLE_FIELDS.items()
                    if other_method != method
                )
                if not other_enabled:
                    raise OwnerPaymentProfileV1Error("Нельзя отключить все способы оплаты")
            updated = await repo.update(row.id, **{field: not current})
            if (
                updated
                and updated.default_payment_method == method
                and not getattr(updated, field)
            ):
                fallback = OwnerPaymentProfileEngineV1._first_enabled_method(updated)
                updated = await repo.update(updated.id, default_payment_method=fallback)
        return OwnerPaymentProfileEngineV1._snapshot(updated)

    @staticmethod
    async def set_default_method(method: str) -> dict[str, Any]:
        method = method.upper()
        field = METHOD_ENABLE_FIELDS.get(method)
        if field is None:
            raise OwnerPaymentProfileV1Error(f"Unsupported method: {method}")

        async with get_session() as session:
            repo = OwnerPaymentProfileV1Repository(session)
            row = await repo.get_or_create_singleton()
            if not getattr(row, field):
                raise OwnerPaymentProfileV1Error(f"Метод {method} отключён")
            updated = await repo.update(row.id, default_payment_method=method)
        return OwnerPaymentProfileEngineV1._snapshot(updated)

    @staticmethod
    async def get_enabled_methods() -> list[str]:
        profile = await OwnerPaymentProfileEngineV1.get_profile()
        return profile.get("enabled_methods") or []

    @staticmethod
    async def is_method_enabled(method: str) -> bool:
        return method.upper() in await OwnerPaymentProfileEngineV1.get_enabled_methods()

    @staticmethod
    async def payment_methods_keyboard(*, lang: str | None = None) -> InlineKeyboardMarkup:
        from services.automotive_localization import normalize_language

        language = normalize_language(lang)
        profile = await OwnerPaymentProfileEngineV1.get_profile()
        enabled = profile.get("enabled_methods") or []
        default_method = profile.get("default_payment_method")

        ordered: list[str] = []
        if default_method and default_method in enabled:
            ordered.append(default_method)
        for method in PaymentEngineMethod:
            code = method.value
            if code in enabled and code not in ordered:
                ordered.append(code)

        rows = []
        for code in ordered:
            label = _PAYMENT_METHOD_LABELS[code].get(language, code)
            if code == default_method:
                label = f"⭐ {label}"
            rows.append([
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"cart:pay:{code}",
                )
            ])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    async def build_payment_instructions(
        method: str,
        *,
        amount: Decimal,
        currency: str,
    ) -> str:
        method = method.upper()
        if not await OwnerPaymentProfileEngineV1.is_method_enabled(method):
            raise OwnerPaymentProfileV1Error(f"Payment method disabled: {method}")

        profile = await OwnerPaymentProfileEngineV1.get_profile()
        suffix = "После оплаты отправьте скриншот перевода в этот чат."

        if method == PaymentEngineMethod.CARD.value:
            holder = profile.get("card_holder_name") or "—"
            mask = profile.get("card_mask") or "—"
            return (
                f"💳 Оплата картой\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Карта: {mask}\n"
                f"Получатель: {holder}\n"
                f"Назначение: Order payment\n\n"
                f"{suffix}"
            )
        if method == PaymentEngineMethod.IBAN.value:
            iban = profile.get("iban") or "—"
            holder = profile.get("card_holder_name") or "—"
            return (
                f"🏦 Банковский перевод (IBAN)\n\n"
                f"Сумма: {amount} {currency}\n"
                f"IBAN: {iban}\n"
                f"Получатель: {holder}\n"
                f"Назначение: Order payment\n\n"
                f"{suffix}"
            )
        if method == PaymentEngineMethod.USDT_TRC20.value:
            wallet = profile.get("usdt_trc20_wallet") or "—"
            return (
                f"💎 USDT (TRC20)\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Адрес: {wallet}\n"
                f"Сеть: TRON (TRC20)\n\n"
                f"{suffix}"
            )
        if method == PaymentEngineMethod.USDT_ERC20.value:
            wallet = profile.get("usdt_erc20_wallet") or "—"
            return (
                f"💎 USDT (ERC20)\n\n"
                f"Сумма: {amount} {currency}\n"
                f"Адрес: {wallet}\n"
                f"Сеть: Ethereum (ERC20)\n\n"
                f"{suffix}"
            )
        if method == PaymentEngineMethod.CASH.value:
            cash_info = profile.get("cash_instructions") or "Свяжитесь с менеджером для уточнения адреса."
            return (
                f"💵 Наличные\n\n"
                f"Сумма: {amount} {currency}\n"
                f"{cash_info}\n\n"
                f"После оплаты отправьте фото чека или квитанции в этот чат."
            )
        return f"Сумма: {amount} {currency}"

    @staticmethod
    def format_owner_profile(profile: dict[str, Any]) -> str:
        lines = [
            "💳 Owner Payment Profile",
            "",
            f"Получатель: {profile.get('card_holder_name') or '—'}",
            f"Карта (mask): {profile.get('card_mask') or '—'}",
            f"IBAN: {profile.get('iban') or '—'}",
            f"USDT TRC20: {profile.get('usdt_trc20_wallet') or '—'}",
            f"USDT ERC20: {profile.get('usdt_erc20_wallet') or '—'}",
            f"Наличные: {profile.get('cash_instructions') or '—'}",
            "",
            f"По умолчанию: {profile.get('default_payment_method') or '—'}",
            "",
            "Методы:",
        ]
        for method in PaymentEngineMethod:
            code = method.value
            enabled = code in (profile.get("enabled_methods") or [])
            mark = "✅" if enabled else "❌"
            default = " ⭐" if code == profile.get("default_payment_method") else ""
            label = _PAYMENT_METHOD_LABELS[code]["ru"]
            lines.append(f"  {mark} {label}{default}")
        return "\n".join(lines)

    @staticmethod
    def owner_settings_keyboard(profile: dict[str, Any]) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(
                    text="✏️ Получатель",
                    callback_data="owner:pay:edit:card_holder_name",
                ),
                InlineKeyboardButton(
                    text="✏️ Маска карты",
                    callback_data="owner:pay:edit:card_mask",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ IBAN",
                    callback_data="owner:pay:edit:iban",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ USDT TRC20",
                    callback_data="owner:pay:edit:usdt_trc20_wallet",
                ),
                InlineKeyboardButton(
                    text="✏️ USDT ERC20",
                    callback_data="owner:pay:edit:usdt_erc20_wallet",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Наличные",
                    callback_data="owner:pay:edit:cash_instructions",
                ),
            ],
        ]
        toggle_row = []
        for method in PaymentEngineMethod:
            code = method.value
            enabled = code in (profile.get("enabled_methods") or [])
            mark = "✅" if enabled else "❌"
            toggle_row.append(
                InlineKeyboardButton(
                    text=f"{mark} {code}",
                    callback_data=f"owner:pay:toggle:{code}",
                )
            )
            if len(toggle_row) == 2:
                rows.append(toggle_row)
                toggle_row = []
        if toggle_row:
            rows.append(toggle_row)

        default_row = []
        for method in PaymentEngineMethod:
            code = method.value
            if code not in (profile.get("enabled_methods") or []):
                continue
            star = "⭐ " if code == profile.get("default_payment_method") else ""
            default_row.append(
                InlineKeyboardButton(
                    text=f"{star}{code}",
                    callback_data=f"owner:pay:default:{code}",
                )
            )
            if len(default_row) == 2:
                rows.append(default_row)
                default_row = []
        if default_row:
            rows.append(default_row)

        rows.append([
            InlineKeyboardButton(text="⬅ Назад", callback_data="owner:pay:back"),
        ])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def edit_field_prompt(field: str) -> str:
        prompts = {
            "card_holder_name": "Введите имя получателя (для карты и IBAN):",
            "card_mask": (
                "Введите маску карты (только masked формат, например **** **** **** 1234).\n"
                "Полный номер карты сохранять нельзя."
            ),
            "iban": "Введите IBAN:",
            "usdt_trc20_wallet": "Введите USDT TRC20 кошелёк:",
            "usdt_erc20_wallet": "Введите USDT ERC20 кошелёк:",
            "cash_instructions": "Введите инструкции для оплаты наличными (адрес, часы):",
        }
        return prompts.get(field, "Введите новое значение:")

    @staticmethod
    def _validate_card_mask(value: str) -> str:
        if OwnerPaymentProfileEngineV1._looks_like_full_card(value):
            raise OwnerPaymentProfileV1Error(
                "Нельзя сохранять полный номер карты. Используйте маску, например **** **** **** 1234."
            )
        digits = re.sub(r"\D", "", value)
        if len(digits) > 4:
            raise OwnerPaymentProfileV1Error(
                "В маске карты допускаются только последние 4 цифры."
            )
        normalized = value.strip()
        if "*" not in normalized and "•" not in normalized and "X" not in normalized.upper():
            if len(digits) == 4:
                normalized = f"**** **** **** {digits}"
            else:
                raise OwnerPaymentProfileV1Error(
                    "Используйте masked формат, например **** **** **** 1234."
                )
        return normalized

    @staticmethod
    def _looks_like_full_card(value: str) -> bool:
        digits = re.sub(r"\D", "", value)
        has_mask_char = any(ch in value for ch in "*•Xx")
        return len(digits) >= 13 and not has_mask_char

    @staticmethod
    def _any_enabled(row: OwnerPaymentProfileV1) -> bool:
        return any(getattr(row, field) for field in METHOD_ENABLE_FIELDS.values())

    @staticmethod
    def _first_enabled_method(row: OwnerPaymentProfileV1) -> str | None:
        for method, field in METHOD_ENABLE_FIELDS.items():
            if getattr(row, field):
                return method
        return None

    @staticmethod
    def _snapshot(row: OwnerPaymentProfileV1 | None) -> dict[str, Any]:
        if row is None:
            return {}
        enabled = [
            method
            for method, field in METHOD_ENABLE_FIELDS.items()
            if getattr(row, field)
        ]
        return {
            "id": str(row.id),
            "card_holder_name": row.card_holder_name,
            "card_mask": row.card_mask,
            "iban": row.iban,
            "usdt_trc20_wallet": row.usdt_trc20_wallet,
            "usdt_erc20_wallet": row.usdt_erc20_wallet,
            "cash_instructions": row.cash_instructions,
            "card_enabled": row.card_enabled,
            "iban_enabled": row.iban_enabled,
            "usdt_trc20_enabled": row.usdt_trc20_enabled,
            "usdt_erc20_enabled": row.usdt_erc20_enabled,
            "cash_enabled": row.cash_enabled,
            "default_payment_method": row.default_payment_method,
            "enabled_methods": enabled,
        }
