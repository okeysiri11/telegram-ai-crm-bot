# CRM Pipeline Boards v1 — Telegram board UI and stage moves.

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import OWNER_ID
from database import has_permission, log_audit
from services.pg_crm_pipeline_boards_engine import (
    CrmPipelineBoardsEngineV1,
    CrmPipelineBoardsError,
)

logger = logging.getLogger(__name__)

crm_pipeline_boards_router = Router()


def _can_access(user_id: int) -> bool:
    return has_permission(user_id, "users_access") or user_id == OWNER_ID


@crm_pipeline_boards_router.message(F.text == "📋 Pipeline Board")
async def open_pipeline_board(message: Message) -> None:
    user_id = message.from_user.id
    if not _can_access(user_id):
        await message.answer("Нет доступа.")
        return
    log_audit(user_id, "open", "crm_pipeline_board")
    await message.answer(
        "📋 Pipeline Board\n\nВыберите вертикаль:",
        reply_markup=CrmPipelineBoardsEngineV1.vertical_picker_keyboard(),
    )


@crm_pipeline_boards_router.callback_query(F.data == "pip:pick:vertical")
async def pipeline_pick_vertical(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    if not _can_access(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        "📋 Pipeline Board\n\nВыберите вертикаль:",
        reply_markup=CrmPipelineBoardsEngineV1.vertical_picker_keyboard(),
    )


@crm_pipeline_boards_router.callback_query(F.data.startswith("pip:v:"))
async def pipeline_pick_entity_type(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    if not _can_access(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    vertical = callback.data.rsplit(":", 1)[-1]
    await callback.answer()
    label = "🚗 AUTO" if vertical == "auto" else "🌾 AGRO"
    await callback.message.edit_text(
        f"📋 Pipeline Board — {label}\n\nВыберите тип:",
        reply_markup=CrmPipelineBoardsEngineV1.entity_type_keyboard(vertical),
    )


@crm_pipeline_boards_router.callback_query(F.data.startswith("pip:t:"))
async def pipeline_open_board_from_type(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    parts = (callback.data or "").split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    vertical, entity_type = parts[2], parts[3]
    await _render_board(callback, vertical=vertical, entity_type=entity_type)


@crm_pipeline_boards_router.callback_query(F.data.startswith("pip:board:"))
async def pipeline_refresh_board(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    parts = (callback.data or "").split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    vertical, entity_type = parts[2], parts[3]
    await _render_board(callback, vertical=vertical, entity_type=entity_type)


async def _render_board(
    callback: CallbackQuery,
    *,
    vertical: str,
    entity_type: str,
) -> None:
    try:
        board = await CrmPipelineBoardsEngineV1.get_board(vertical, entity_type)
        text = CrmPipelineBoardsEngineV1.format_board_text(board)
        keyboard = CrmPipelineBoardsEngineV1.board_keyboard(board)
    except Exception as exc:
        logger.exception("Pipeline board failed vertical=%s type=%s", vertical, entity_type)
        await callback.answer(f"Ошибка: {exc}", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=keyboard)


@crm_pipeline_boards_router.callback_query(F.data.startswith("pip:item:"))
async def pipeline_open_item(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    if not _can_access(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    parts = (callback.data or "").split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    entity_type, entity_id_str = parts[2], parts[3]
    try:
        entity_id = uuid.UUID(entity_id_str)
    except ValueError:
        await callback.answer("Некорректный ID", show_alert=True)
        return

    try:
        from database.session import get_session
        from repositories.crm_pipeline_boards_repository import CrmPipelineBoardsRepository

        async with get_session() as session:
            repo = CrmPipelineBoardsRepository(session)
            if entity_type == "lead":
                row = await repo.get_lead(entity_id)
            else:
                row = await repo.get_deal(entity_id)
            if row is None:
                await callback.answer("Не найдено", show_alert=True)
                return
            vertical = row.vertical
        card = await CrmPipelineBoardsEngineV1.get_entity_card(vertical, entity_type, entity_id)
        text = CrmPipelineBoardsEngineV1.format_entity_card(card)
        keyboard = CrmPipelineBoardsEngineV1.entity_card_keyboard(card)
    except Exception as exc:
        logger.exception("Pipeline item card failed id=%s", entity_id_str)
        await callback.answer(f"Ошибка: {exc}", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(text, reply_markup=keyboard)


@crm_pipeline_boards_router.callback_query(F.data.startswith("pip:move:"))
async def pipeline_move_item(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    user_id = callback.from_user.id
    if not _can_access(user_id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = (callback.data or "").split(":")
    if len(parts) < 5:
        await callback.answer()
        return
    entity_type, entity_id_str, new_stage = parts[2], parts[3], parts[4]
    try:
        entity_id = uuid.UUID(entity_id_str)
    except ValueError:
        await callback.answer("Некорректный ID", show_alert=True)
        return

    try:
        from database.session import get_session
        from repositories.crm_pipeline_boards_repository import CrmPipelineBoardsRepository

        async with get_session() as session:
            repo = CrmPipelineBoardsRepository(session)
            if entity_type == "lead":
                row = await repo.get_lead(entity_id)
            else:
                row = await repo.get_deal(entity_id)
            if row is None:
                await callback.answer("Не найдено", show_alert=True)
                return
            vertical = row.vertical

        result = await CrmPipelineBoardsEngineV1.move_entity(
            vertical=vertical,
            entity_type=entity_type,
            entity_id=entity_id,
            new_stage=new_stage,
            moved_by=user_id,
        )
        card = await CrmPipelineBoardsEngineV1.get_entity_card(
            vertical, entity_type, entity_id
        )
        text = CrmPipelineBoardsEngineV1.format_entity_card(card)
        keyboard = CrmPipelineBoardsEngineV1.entity_card_keyboard(card)
    except CrmPipelineBoardsError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    except Exception as exc:
        logger.exception("Pipeline move failed id=%s stage=%s", entity_id_str, new_stage)
        await callback.answer(f"Ошибка: {exc}", show_alert=True)
        return

    await callback.answer(f"→ {result['new_stage']}")
    await callback.message.edit_text(text, reply_markup=keyboard)
    log_audit(user_id, "move", "crm_pipeline", f"{entity_type}:{entity_id}:{new_stage}")
