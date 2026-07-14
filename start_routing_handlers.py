# Start command routing — strict entry-point flows.

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from config import OWNER_ID
from services.entry_point_routing import EntryPoint
from services.pg_entry_point_engine import EntryPointEngineV1
from services.pg_vertical_onboarding_engine import VerticalOnboardingEngineV1
from services.tenant_routing import ENTRY_LINK_REGISTRY, is_owner
from vertical_onboarding_handlers import begin_vertical_onboarding

logger = logging.getLogger(__name__)

start_routing_router = Router()


@start_routing_router.message(Command("start_auto_client"))
async def cmd_start_auto_client(message: Message) -> None:
    await EntryPointEngineV1.begin_auto_client(message)


@start_routing_router.message(Command("start_auto_dealer"))
async def cmd_start_auto_dealer(message: Message) -> None:
    await EntryPointEngineV1.begin_auto_dealer(message)


@start_routing_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    user = message.from_user
    user_id = user.id

    entry_link = VerticalOnboardingEngineV1.parse_entry_link_code(command.args)
    if entry_link == "auto_client":
        await EntryPointEngineV1.begin_auto_client(message)
        return
    if entry_link == "auto_dealer":
        await EntryPointEngineV1.begin_auto_dealer(message)
        return

    if entry_link and entry_link in ENTRY_LINK_REGISTRY:
        handled = await EntryPointEngineV1.begin_from_source_link(message, entry_link)
        if handled:
            return

    deep_link_vertical = VerticalOnboardingEngineV1.parse_deep_link(command.args)
    if deep_link_vertical and entry_link not in ENTRY_LINK_REGISTRY:
        await begin_vertical_onboarding(message, deep_link_vertical, start_args=command.args)
        return

    if is_owner(user_id) or user_id == OWNER_ID:
        await message.answer(f"Ваш Telegram ID: {user_id}")
        await EntryPointEngineV1.begin_owner_start(message)
        return

    await message.answer(f"Ваш Telegram ID: {user_id}")
    await EntryPointEngineV1.begin_regular_start(message)
