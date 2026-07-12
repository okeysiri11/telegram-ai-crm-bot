# Telegram handlers — PostgreSQL Deal Workflow.

from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.pg_deal_workflow import DealWorkflowService, format_deal

deal_workflow_router = Router()


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value.strip())
    except ValueError:
        return None


async def _require_access(message: Message) -> int | None:
    user_id = message.from_user.id
    if not await DealWorkflowService.user_can_access(user_id):
        await message.answer("Access denied. Required roles: OWNER, ADMIN, or MANAGER.")
        return None
    return user_id


@deal_workflow_router.message(Command("new_deal"))
async def cmd_new_deal(message: Message) -> None:
    user_id = await _require_access(message)
    if user_id is None:
        return

    parts = (message.text or "").split()[1:]
    if len(parts) < 4:
        await message.answer(
            "Usage: /new_deal <asset_in> <amount_in> <asset_out> <amount_out>\n"
            "Example: /new_deal USDT 1000 RUB 95000"
        )
        return

    asset_in, amount_in, asset_out, amount_out = parts[0], parts[1], parts[2], parts[3]
    try:
        deal = await DealWorkflowService.create_deal(
            user_id,
            asset_in_type=asset_in.upper(),
            asset_in_amount=Decimal(amount_in),
            asset_out_type=asset_out.upper(),
            asset_out_amount=Decimal(amount_out),
        )
    except (InvalidOperation, ValueError) as exc:
        await message.answer(f"Invalid input: {exc}")
        return
    except PermissionError as exc:
        await message.answer(str(exc))
        return

    await message.answer(f"Deal created.\n\n{format_deal(deal)}")


@deal_workflow_router.message(Command("my_deals"))
async def cmd_my_deals(message: Message) -> None:
    user_id = await _require_access(message)
    if user_id is None:
        return

    try:
        deals = await DealWorkflowService.get_my_deals(user_id)
    except PermissionError as exc:
        await message.answer(str(exc))
        return

    if not deals:
        await message.answer("No deals assigned to you.")
        return

    lines = [f"My deals ({len(deals)}):"]
    for deal in deals[:20]:
        lines.append(
            f"• `{deal.id}` — {deal.status} — "
            f"{deal.asset_in_amount} {deal.asset_in_type} → "
            f"{deal.asset_out_amount} {deal.asset_out_type}"
        )
    await message.answer("\n".join(lines))


@deal_workflow_router.message(Command("active_deals"))
async def cmd_active_deals(message: Message) -> None:
    user_id = await _require_access(message)
    if user_id is None:
        return

    try:
        deals = await DealWorkflowService.get_active_deals(user_id)
    except PermissionError as exc:
        await message.answer(str(exc))
        return

    if not deals:
        await message.answer("No active deals.")
        return

    lines = [f"Active deals ({len(deals)}):"]
    for deal in deals[:20]:
        lines.append(
            f"• `{deal.id}` — {deal.status} — mgr {deal.manager_id or '—'}"
        )
    await message.answer("\n".join(lines))


@deal_workflow_router.message(Command("deal_info"))
async def cmd_deal_info(message: Message) -> None:
    user_id = await _require_access(message)
    if user_id is None:
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /deal_info <deal_uuid>")
        return

    deal_id = _parse_uuid(parts[1])
    if deal_id is None:
        await message.answer("Invalid deal UUID.")
        return

    try:
        deal = await DealWorkflowService.get_deal_info(user_id, deal_id)
    except PermissionError as exc:
        await message.answer(str(exc))
        return

    if deal is None:
        await message.answer("Deal not found.")
        return

    await message.answer(format_deal(deal))


@deal_workflow_router.message(Command("assign_deal"))
async def cmd_assign_deal(message: Message) -> None:
    user_id = await _require_access(message)
    if user_id is None:
        return

    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("Usage: /assign_deal <deal_uuid> <manager_telegram_id>")
        return

    deal_id = _parse_uuid(parts[1])
    if deal_id is None:
        await message.answer("Invalid deal UUID.")
        return

    try:
        manager_id = int(parts[2])
    except ValueError:
        await message.answer("Invalid manager Telegram ID.")
        return

    try:
        deal = await DealWorkflowService.assign_deal(user_id, deal_id, manager_id)
    except PermissionError as exc:
        await message.answer(str(exc))
        return

    if deal is None:
        await message.answer("Deal not found.")
        return

    await message.answer(f"Deal assigned.\n\n{format_deal(deal)}")


@deal_workflow_router.message(Command("update_status"))
async def cmd_update_status(message: Message) -> None:
    user_id = await _require_access(message)
    if user_id is None:
        return

    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(
            "Usage: /update_status <deal_uuid> <status>\n"
            "Statuses: NEW, ASSIGNED, FUNDS_RECEIVED, PROCESSING, COMPLETED, CANCELLED"
        )
        return

    deal_id = _parse_uuid(parts[1])
    if deal_id is None:
        await message.answer("Invalid deal UUID.")
        return

    new_status = parts[2].upper()
    try:
        deal = await DealWorkflowService.update_status(user_id, deal_id, new_status)
    except PermissionError as exc:
        await message.answer(str(exc))
        return
    except ValueError as exc:
        await message.answer(str(exc))
        return

    if deal is None:
        await message.answer("Deal not found.")
        return

    await message.answer(f"Status updated.\n\n{format_deal(deal)}")


@deal_workflow_router.message(Command("complete_deal"))
async def cmd_complete_deal(message: Message) -> None:
    user_id = await _require_access(message)
    if user_id is None:
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /complete_deal <deal_uuid>")
        return

    deal_id = _parse_uuid(parts[1])
    if deal_id is None:
        await message.answer("Invalid deal UUID.")
        return

    try:
        deal = await DealWorkflowService.complete_deal(user_id, deal_id)
    except PermissionError as exc:
        await message.answer(str(exc))
        return
    except ValueError as exc:
        await message.answer(str(exc))
        return

    if deal is None:
        await message.answer("Deal not found.")
        return

    await message.answer(f"Deal completed.\n\n{format_deal(deal)}")
