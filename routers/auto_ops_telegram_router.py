"""AUTO 1.4 — Auto ops staff commands inside the shared ADOS Telegram bot.

Does not replace /start for unauthorized users. Does not create a second bot.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import BaseFilter, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.auto_ops import get_auto_ops_service
from services.auto_ops.telegram import note_telegram_update
from services.auto_ops.telegram_auth import looks_like_intercept

logger = logging.getLogger(__name__)

router = Router(name="auto_ops_telegram")


class AutoOpsBound(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        if user is None:
            return False
        return get_auto_ops_service().telegram_user_bound(user.id)


class AutoOpsSlash(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return bool(message.text) and looks_like_intercept(str(message.text))


def _keyboard(rows: list[list[dict[str, str]]] | None) -> InlineKeyboardMarkup | None:
    if not rows:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=b["text"], callback_data=b["callback_data"]) for b in row] for row in rows]
    )


async def _reply(message: Message, result: dict) -> None:
    text = str(result.get("message_ru") or "Готово.")
    await message.answer(text, reply_markup=_keyboard(result.get("keyboard")))


@router.message(CommandStart(), AutoOpsBound())
async def auto_ops_start(message: Message) -> None:
    if message.from_user is None:
        return
    svc = get_auto_ops_service()
    result = await svc.handle_telegram_inbound(telegram_id=message.from_user.id, text=message.text or "/start")
    await _reply(message, result)


@router.message(AutoOpsSlash())
async def auto_ops_commands(message: Message) -> None:
    if message.from_user is None:
        return
    svc = get_auto_ops_service()
    extra: dict = {}
    if message.photo:
        extra["filename"] = "telegram.jpg"
        extra["mime_type"] = "image/jpeg"
    result = await svc.handle_telegram_inbound(telegram_id=message.from_user.id, text=message.text or "", extra=extra)
    if result.get("intercepted") is False:
        return
    await _reply(message, result)


@router.message(AutoOpsBound(), F.photo)
async def auto_ops_photo(message: Message) -> None:
    if message.from_user is None:
        return
    svc = get_auto_ops_service()
    if not svc.telegram_user_bound(message.from_user.id):
        return
    caption = message.caption or "/photo"
    extra = {"filename": "telegram.jpg", "mime_type": "image/jpeg"}
    if message.bot and message.photo:
        try:
            file = await message.bot.get_file(message.photo[-1].file_id)
            buf = await message.bot.download_file(file.file_path)
            extra["content_bytes"] = buf.read() if hasattr(buf, "read") else buf
        except Exception as exc:  # noqa: BLE001
            note_telegram_update(error=type(exc).__name__)
            await message.answer("Не удалось скачать фото. Повторите.")
            return
    vin_guess = (caption or "").split()
    if vin_guess and not vin_guess[0].startswith("/"):
        extra["vin"] = vin_guess[0]
        caption = f"/photo {vin_guess[0]}"
    elif looks_like_intercept(caption):
        pass
    else:
        caption = f"/photo {caption}".strip()
    result = await svc.handle_telegram_inbound(telegram_id=message.from_user.id, text=caption, extra=extra)
    await _reply(message, result)


@router.message(AutoOpsBound(), F.document)
async def auto_ops_document(message: Message) -> None:
    if message.from_user is None:
        return
    svc = get_auto_ops_service()
    if not svc.telegram_user_bound(message.from_user.id):
        return
    doc = message.document
    extra: dict = {
        "filename": (doc.file_name if doc else None) or "telegram.bin",
        "mime_type": (doc.mime_type if doc else None) or "application/octet-stream",
    }
    if message.bot and doc:
        try:
            file = await message.bot.get_file(doc.file_id)
            buf = await message.bot.download_file(file.file_path)
            extra["content_bytes"] = buf.read() if hasattr(buf, "read") else buf
        except Exception as exc:  # noqa: BLE001
            note_telegram_update(error=type(exc).__name__)
            await message.answer("Не удалось скачать документ. Повторите.")
            return
    caption = message.caption or "/doc"
    parts = (caption or "").split()
    if parts and not parts[0].startswith("/"):
        extra["vin"] = parts[0]
        if len(parts) > 1:
            extra["document_type"] = parts[1]
        caption = f"/doc {caption}".strip()
    elif looks_like_intercept(caption):
        pass
    else:
        caption = f"/doc {caption}".strip()
    result = await svc.handle_telegram_inbound(telegram_id=message.from_user.id, text=caption, extra=extra)
    await _reply(message, result)


@router.message(AutoOpsBound(), F.text)
async def auto_ops_pending_doc(message: Message) -> None:
    if message.from_user is None or not message.text:
        return
    if looks_like_intercept(message.text):
        return
    svc = get_auto_ops_service()
    pending = getattr(svc, "_tg_upload_pending", {}).get(message.from_user.id)
    if not pending:
        return
    result = await svc.handle_telegram_inbound(telegram_id=message.from_user.id, text=message.text)
    await _reply(message, result)


@router.callback_query(F.data.startswith("ao:"))
async def auto_ops_callback(query: CallbackQuery) -> None:
    if query.from_user is None:
        return
    svc = get_auto_ops_service()
    result = await svc.handle_telegram_inbound(telegram_id=query.from_user.id, callback_data=query.data or "")
    await query.answer()
    if query.message:
        await query.message.answer(str(result.get("message_ru") or "Готово."), reply_markup=_keyboard(result.get("keyboard")))
