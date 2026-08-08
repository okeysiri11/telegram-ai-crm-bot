"""Telegram AI Super App router — Sprint 43.3 Production UX.

Registered before legacy handlers so Super App menu wins first match.
User-facing copy: Russian tasks only — no Provider / Pipeline / Runtime jargon.
"""

from __future__ import annotations

import logging
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.telegram_ai_super_app.catalog import (
    AI_STUDIO_OPTIONS,
    BTN,
    DEVELOPER_MENU_BUTTONS,
)
from services.telegram_ai_super_app.conversation_flow import ConversationDraft
from services.telegram_ai_super_app.keyboards import (
    ai_studio_keyboard,
    all_sections_keyboard,
    business_menu_keyboard,
    choices_inline,
    concierge_examples_inline,
    confirm_generate_inline,
    developer_menu_keyboard,
    hercules_menu_keyboard,
    ai_command_menu_keyboard,
    work_mode_keyboard,
    memory_menu_keyboard,
    automation_menu_keyboard,
    main_menu_keyboard,
    post_generation_inline,
    publish_channels_inline,
    template_categories_inline,
    templates_inline,
)
from services.telegram_ai_super_app.product_ux import (
    format_result_for_user,
    progress_message,
    sanitize_user_text,
)
from services.telegram_ai_super_app.service import telegram_ai_super_app
from services.telegram_ai_super_app.states import SuperAppFlow
from services.telegram_ai_super_app.templates import TEMPLATE_CATEGORIES, templates_by_category
from services.telegram_ai_super_app.vertical_ux import (
    calendar_periods_inline,
    is_vertical_menu_label,
    publish_after_vertical_inline,
    vertical_menu_keyboard,
)
from platform_vertical_ai.framework import vertical_ai_framework

logger = logging.getLogger(__name__)

router = Router(name="telegram_super_app")
app = telegram_ai_super_app
vfw = vertical_ai_framework


async def _is_developer(telegram_id: int | None) -> bool:
    if telegram_id is None:
        return False
    try:
        from services.pg_platform_permissions_engine import PlatformPermissionsEngineV1

        if await PlatformPermissionsEngineV1.user_has_permission(telegram_id, "platform.config.read"):
            return True
        if await PlatformPermissionsEngineV1.user_has_permission(telegram_id, "admin.manage"):
            return True
    except Exception:
        pass
    try:
        from config import DEFAULT_AUTO_MANAGER_ID, SUPER_ADMIN_IDS

        if telegram_id == DEFAULT_AUTO_MANAGER_ID:
            return True
        if SUPER_ADMIN_IDS and telegram_id in SUPER_ADMIN_IDS:
            return True
    except Exception:
        pass
    try:
        from services.pg_entry_point_engine import EntryPointEngineV1

        role = await EntryPointEngineV1.resolve_role(telegram_id)  # type: ignore[attr-defined]
        if role in ("owner", "platform_owner", "developer", "administrator"):
            return True
    except Exception:
        pass
    return False


def _ukey(message: Message) -> str:
    uid = message.from_user.id if message.from_user else 0
    return app.user_key(uid)


@router.message(Command("menu", "superapp", "ados"))
async def cmd_super_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    dev = await _is_developer(message.from_user.id if message.from_user else None)
    await message.answer(
        "ADOS Enterprise — главное меню",
        reply_markup=main_menu_keyboard(include_developer=dev),
    )


@router.message(F.text == BTN.BACK_MAIN)
async def back_main(message: Message, state: FSMContext) -> None:
    await state.clear()
    dev = await _is_developer(message.from_user.id if message.from_user else None)
    await message.answer("Главное меню", reply_markup=main_menu_keyboard(include_developer=dev))


@router.message(F.text == BTN.BACK_STUDIO)
async def back_studio(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(app.welcome_studio(), reply_markup=ai_studio_keyboard())


@router.message(F.text == BTN.WORK_MODE)
async def open_work_mode(message: Message, state: FSMContext) -> None:
    from platform_modes.manager import mode_manager

    menu = mode_manager.telegram_menu(_ukey(message))
    await message.answer(
        f"{menu['title']}\n\nТекущий режим:\n{menu['current']}",
        reply_markup=work_mode_keyboard(),
    )


WORK_MODE_BTNS = {
    "⚪ Human Mode",
    "🟢 AI Mode",
    "🎙 Voice Mode",
    "📌 Сделать режимом по умолчанию",
    "📌 Запомнить режим",
}


@router.message(F.text.in_(WORK_MODE_BTNS))
async def work_mode_buttons(message: Message, state: FSMContext) -> None:
    from platform_modes.manager import mode_manager
    from platform_modes.mode_state import WorkMode

    text = message.text or ""
    owner = _ukey(message)
    if text.startswith("📌"):
        st = mode_manager.remember_default(owner)
        await message.answer(
            f"Режим по умолчанию сохранён.\n{st['indicator']}",
            reply_markup=work_mode_keyboard(),
        )
        return
    mapping = {
        "⚪ Human Mode": WorkMode.HUMAN_MODE,
        "🟢 AI Mode": WorkMode.AI_MODE,
        "🎙 Voice Mode": WorkMode.VOICE_MODE,
    }
    mode = mapping.get(text)
    if mode:
        st = mode_manager.change(owner, mode, channel="telegram")
        await message.answer(
            f"Режим переключён.\n{st['indicator']}",
            reply_markup=work_mode_keyboard(),
        )
        return
    await open_work_mode(message, state)


MODE_NL_COMMANDS = {
    "AI ON",
    "AI OFF",
    "VOICE ON",
    "VOICE OFF",
    "HUMAN MODE",
    "Работаем вручную",
    "Включи AI",
    "Выключи AI",
    "Включи голос",
    "Остановись",
    "Стоп",
    "Отключись",
    "Выключить AI",
}


@router.message(F.text.in_(MODE_NL_COMMANDS))
async def mode_nl_commands(message: Message, state: FSMContext) -> None:
    from platform_modes.manager import mode_manager

    st = mode_manager.handle_text_command(_ukey(message), message.text or "", channel="telegram")
    if st:
        await message.answer(f"Режим: {st['indicator']}", reply_markup=work_mode_keyboard())
        return
    await open_work_mode(message, state)


@router.message(F.text == BTN.MEMORY)
async def open_memory(message: Message, state: FSMContext) -> None:
    from platform_memory.memory_manager import memory_manager

    menu = memory_manager.telegram_menu(_ukey(message))
    resume_txt = memory_manager.resume(_ukey(message), channel="telegram")
    lines = [
        menu["title"],
        "",
        resume_txt.get("welcome_ru") or "Добро пожаловать.",
    ]
    for s in (resume_txt.get("suggestions_ru") or [])[:3]:
        lines.append(f"• {s}")
    await message.answer("\n".join(lines), reply_markup=memory_menu_keyboard())


MEMORY_BTNS = {
    "Последние разговоры",
    "Продолжить работу",
    "Проекты",
    "Избранное",
    "Недавние документы",
    "Последние генерации",
    "AI Summary",
    "Поиск",
}

MEMORY_VOICE_RECALL = {
    "Что мы делали?",
    "Продолжим.",
    "Продолжим",
    "Напомни.",
    "Напомни",
    "Что осталось?",
    "Продолжить проект.",
    "Продолжить проект",
    "Покажи историю.",
    "Покажи историю",
}


@router.message(F.text.in_(MEMORY_BTNS))
async def memory_menu_buttons(message: Message, state: FSMContext) -> None:
    from platform_memory.conversation_memory import conversation_memory
    from platform_memory.memory_manager import memory_manager
    from platform_memory.memory_permissions import MemoryPrincipal

    owner = _ukey(message)
    p = MemoryPrincipal(owner_id=owner)
    text = message.text or ""
    if text == "Продолжить работу":
        recall = memory_manager.recall(owner, "Продолжим", channel="telegram")
        await message.answer(
            recall["reply_ru"] + "\n" + "\n".join(f"• {s}" for s in recall.get("suggestions", [])[:5]),
            reply_markup=memory_menu_keyboard(),
        )
        return
    if text == "Последние разговоры":
        hist = conversation_memory.history(p, limit=8)
        body = "\n".join(f"• {h.get('title')}: {h.get('content', '')[:80]}" for h in hist) or "Пока пусто."
        await message.answer(f"Последние разговоры\n{body}", reply_markup=memory_menu_keyboard())
        return
    if text == "Проекты":
        ws = memory_manager.workspace(owner)
        body = "\n".join(f"• {item.get('title')}" for item in ws.get("projects", [])) or "Нет проектов."
        await message.answer(f"Проекты\n{body}", reply_markup=memory_menu_keyboard())
        return
    if text == "Избранное":
        ws = memory_manager.workspace(owner)
        body = "\n".join(f"• {x.get('title')}" for x in ws.get("favorites", [])) or "Пусто."
        await message.answer(f"Избранное\n{body}", reply_markup=memory_menu_keyboard())
        return
    if text == "Недавние документы":
        ws = memory_manager.workspace(owner)
        body = "\n".join(f"• {x.get('title')}" for x in ws.get("documents", [])) or "Пусто."
        await message.answer(f"Документы\n{body}", reply_markup=memory_menu_keyboard())
        return
    if text == "Последние генерации":
        ws = memory_manager.workspace(owner)
        body = "\n".join(f"• {x.get('title')}" for x in ws.get("generations", [])) or "Пусто."
        await message.answer(f"Генерации\n{body}", reply_markup=memory_menu_keyboard())
        return
    if text == "AI Summary":
        s = memory_manager.summary(owner, channel="telegram")
        await message.answer(s.get("summary_ru") or "Нет резюме.", reply_markup=memory_menu_keyboard())
        return
    if text == "Поиск":
        await state.update_data(memory_search=True)
        await message.answer("Введите запрос для поиска по памяти:", reply_markup=memory_menu_keyboard())
        return
    await open_memory(message, state)


@router.message(F.text.in_(MEMORY_VOICE_RECALL))
async def memory_voice_recall(message: Message, state: FSMContext) -> None:
    from platform_memory.memory_manager import memory_manager

    recall = memory_manager.recall(_ukey(message), message.text or "", channel="telegram")
    await message.answer(
        recall["reply_ru"] + "\n" + "\n".join(f"• {s}" for s in recall.get("suggestions", [])[:5]),
        reply_markup=memory_menu_keyboard(),
    )


@router.message(F.text == BTN.AUTOMATION)
async def open_automation(message: Message, state: FSMContext) -> None:
    from platform_workflows.workflow_manager import workflow_manager

    menu = workflow_manager.telegram_menu(_ukey(message))
    st = menu["status"]
    await message.answer(
        f"{menu['title']}\n\nАктивных: {st.get('active_runs', 0)}\nWorkflow: {st.get('workflows', 0)}",
        reply_markup=automation_menu_keyboard(),
    )


AUTOMATION_BTNS = {
    "Создать Workflow",
    "Мои Workflow",
    "Библиотека",
    "Активные процессы",
    "Запланированные",
    "История",
    "Фоновые задачи",
    "Монитор",
    "Настройки",
}

AUTOMATION_VOICE = {
    "Создай Workflow.",
    "Создай Workflow",
    "Сделай рекламу.",
    "Сделай рекламу",
    "Подготовь презентацию.",
    "Подготовь презентацию",
    "Создай договор.",
    "Создай договор",
    "Запусти анализ.",
    "Запусти анализ",
    "Создай видео.",
    "Создай видео",
    "Сделай публикацию.",
    "Сделай публикацию",
    "Продолжи Workflow.",
    "Продолжи Workflow",
    "Останови Workflow.",
    "Останови Workflow",
}


@router.message(F.text.in_(AUTOMATION_BTNS))
async def automation_menu_buttons(message: Message, state: FSMContext) -> None:
    from platform_modes.manager import mode_manager
    from platform_modes.mode_state import WorkMode
    from platform_workflows.workflow_manager import workflow_manager

    owner = _ukey(message)
    text = message.text or ""
    # Prefer AI Mode for demo runs unless user stays Human (then approval path)
    if text == "Создать Workflow":
        mode_manager.change(owner, WorkMode.AI_MODE, channel="telegram")
        result = workflow_manager.run_goal(owner, "Создай рекламу салона красоты", channel="telegram", vertical="beauty")
        run = result["run"]
        await message.answer(
            f"Workflow создан и запущен.\nСтатус: {run.get('status')}\n{run.get('step_label')}\nчерез Hercules",
            reply_markup=automation_menu_keyboard(),
        )
        return
    if text == "Мои Workflow":
        items = workflow_manager.list_workflows(owner)
        body = "\n".join(f"• {w.get('title')}" for w in items[:15]) or "Пока нет Workflow."
        await message.answer(f"Мои Workflow\n{body}", reply_markup=automation_menu_keyboard())
        return
    if text == "Библиотека":
        lib = workflow_manager.templates()
        body = "\n".join(f"• {t.get('title_ru')}" for t in lib.get("templates", [])[:12])
        await message.answer(f"Библиотека\n{body}", reply_markup=automation_menu_keyboard())
        return
    if text == "Активные процессы":
        st = workflow_manager.status(owner)
        body = "\n".join(f"• {r.get('id')}: {r.get('status')}" for r in st.get("active", [])) or "Нет активных."
        await message.answer(f"Активные\n{body}", reply_markup=automation_menu_keyboard())
        return
    if text == "Запланированные":
        jobs = workflow_manager.jobs(owner)
        body = "\n".join(f"• {j.get('schedule')} · {j.get('workflow_id')}" for j in jobs) or "Пусто."
        await message.answer(f"Запланированные\n{body}", reply_markup=automation_menu_keyboard())
        return
    if text == "История":
        hist = workflow_manager.history(owner)
        body = "\n".join(f"• {h.get('status')} · {h.get('run_id')}" for h in hist[:12]) or "Пусто."
        await message.answer(f"История\n{body}", reply_markup=automation_menu_keyboard())
        return
    if text == "Фоновые задачи":
        dash = workflow_manager.dashboard(owner)
        await message.answer(
            f"Фоновые: {len(dash.get('background_jobs') or [])}\nОчередь Hercules: {len(dash.get('hercules_queue') or [])}",
            reply_markup=automation_menu_keyboard(),
        )
        return
    if text == "Монитор":
        st = workflow_manager.status(owner)
        active = st.get("active") or []
        if not active:
            await message.answer("Нет активного процесса.", reply_markup=automation_menu_keyboard())
            return
        mon = workflow_manager.monitor(active[-1]["id"])
        m = (mon or {}).get("monitor") or {}
        await message.answer(
            f"Монитор\n{m.get('step_label')}\n{m.get('current_action')}\nAI: {m.get('active_ai')}\nСтоимость: {m.get('cost')}",
            reply_markup=automation_menu_keyboard(),
        )
        return
    if text == "Настройки":
        await message.answer(
            "Настройки автоматизации: Human Mode требует подтверждение, AI Mode — автозапуск через Hercules.",
            reply_markup=automation_menu_keyboard(),
        )
        return
    await open_automation(message, state)


@router.message(F.text.in_(AUTOMATION_VOICE))
async def automation_voice_commands(message: Message, state: FSMContext) -> None:
    from platform_modes.manager import mode_manager
    from platform_modes.mode_state import WorkMode
    from platform_workflows.workflow_manager import workflow_manager

    owner = _ukey(message)
    mode_manager.change(owner, WorkMode.AI_MODE, channel="telegram")
    result = await workflow_manager.run_from_command(owner, message.text or "", channel="telegram")
    await message.answer(result.get("reply_ru") or "Готово.", reply_markup=automation_menu_keyboard())


@router.message(F.text == BTN.AI_COMMAND)
@router.message(Command("command", "aicommand"))
async def open_ai_command(message: Message, state: FSMContext) -> None:
    await state.set_state(SuperAppFlow.ask_ai)
    await state.update_data(ai_command=True)
    from platform_ai_command.core.command_center import ai_command_center

    home = ai_command_center.home(_ukey(message))
    await message.answer(
        "🧠 AI Command Center\n\n"
        "Единый чат платформы. Пишите или говорите — маршрутизация через Hercules.\n\n"
        f"Быстрые команды: {', '.join(home['quick_commands'][:5])}…",
        reply_markup=ai_command_menu_keyboard(),
    )


from platform_ai_command.telegram.menu import (
    BUTTON_TO_PROMPT,
    TG_CMD_NEW_CHAT,
    TG_CMD_SETTINGS,
    TG_CMD_VOICE,
    menu_labels as ai_command_menu_labels,
)

AI_COMMAND_BTNS = set(ai_command_menu_labels()) | {BTN.AI_COMMAND}


@router.message(F.text.in_(AI_COMMAND_BTNS))
async def ai_command_buttons(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    if text == BTN.AI_COMMAND:
        await open_ai_command(message, state)
        return
    if text == TG_CMD_NEW_CHAT:
        from platform_ai_command.core.command_center import ai_command_center

        ai_command_center.new_dialog(_ukey(message))
        await message.answer("Новый диалог. Напишите задачу.", reply_markup=ai_command_menu_keyboard())
        return
    if text == TG_CMD_VOICE:
        await state.update_data(voice_mode=True)
        await message.answer(
            "🎙 Голосовой режим включён.\n"
            "Скажите или напишите: «Создай рекламу», «Покажи прибыль», «Опубликуй».",
            reply_markup=ai_command_menu_keyboard(),
        )
        return
    if text == TG_CMD_SETTINGS:
        await open_settings(message)
        return
    prompt = BUTTON_TO_PROMPT.get(text)
    if prompt:
        await state.set_state(SuperAppFlow.ask_ai)
        await state.update_data(ai_command=True)
        from platform_ai_command.core.command_center import ai_command_center
        from services.vertical_role_registry import vertical_role_registry

        data = await state.get_data()
        sess = vertical_role_registry.get(message.from_user.id if message.from_user else 0)
        result = await ai_command_center.handle(
            prompt,
            owner_id=_ukey(message),
            channel="telegram",
            voice=bool(data.get("voice_mode")),
            max_steps=2,
            active_vertical=sess.active_vertical,
            active_persona=sess.active_persona,
            authenticated_role=sess.authenticated_role,
        )
        await message.answer(result.get("reply_ru") or "Готово.", reply_markup=ai_command_menu_keyboard())
        return
    await message.answer("AI Command Center", reply_markup=ai_command_menu_keyboard())


@router.message(F.text == BTN.CONCIERGE)
async def open_concierge(message: Message, state: FSMContext) -> None:
    await state.set_state(SuperAppFlow.concierge_chat)
    await message.answer(app.welcome_concierge(), reply_markup=concierge_examples_inline())
    await message.answer(
        "Или напишите свой запрос…",
        reply_markup=main_menu_keyboard(
            include_developer=await _is_developer(message.from_user.id if message.from_user else None)
        ),
    )


@router.message(F.text == BTN.ASK_AI)
async def open_ask_ai(message: Message, state: FSMContext) -> None:
    await state.set_state(SuperAppFlow.ask_ai)
    await message.answer(app.welcome_ask_ai(), reply_markup=ai_studio_keyboard())


@router.message(F.text == BTN.AI_STUDIO)
async def open_ai_studio(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(app.welcome_studio(), reply_markup=ai_studio_keyboard())


@router.message(F.text == BTN.DASHBOARD)
async def open_dashboard(message: Message) -> None:
    await message.answer(
        app.owner_dashboard_text(_ukey(message)),
        reply_markup=main_menu_keyboard(
            include_developer=await _is_developer(message.from_user.id if message.from_user else None)
        ),
    )


@router.message(F.text == BTN.TASKS)
async def open_tasks(message: Message) -> None:
    await message.answer(
        "📋 Задачи\n\nВаши активные задачи появятся здесь.\n"
        "Создайте задачу через AI Консьержа или «💬 Спросить AI».",
        reply_markup=main_menu_keyboard(
            include_developer=await _is_developer(message.from_user.id if message.from_user else None)
        ),
    )


@router.message(F.text == BTN.NOTIFICATIONS)
async def open_notifications(message: Message) -> None:
    await message.answer(
        "🔔 Уведомления\n\nНовых уведомлений нет.\n"
        "AI сообщит, когда генерация будет готова.",
        reply_markup=main_menu_keyboard(
            include_developer=await _is_developer(message.from_user.id if message.from_user else None)
        ),
    )


@router.message(F.text == BTN.BUSINESS)
async def open_business(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🏢 Бизнес — выберите раздел", reply_markup=business_menu_keyboard())


@router.message(
    F.text.in_(
        {
            "📇 CRM",
            "🚗 Авто",
            "💰 Crypto OTC",
            "🚁 Дроны",
            "🌾 Агро",
            "💄 Красота",
            "⚖ Юриспруденция",
            "✈ Travel",
        }
    )
)
async def business_section(message: Message, state: FSMContext) -> None:
    """Sprint 46.5 — Business labels open real verticals (role selector), not Hercules hints."""
    await state.clear()
    label = message.text or ""
    from services.vertical_role_registry import vertical_role_registry
    from services.vertical_nav_service import open_vertical_entry

    vertical_id = vertical_role_registry.resolve_entry_label(label)
    if vertical_id:
        await open_vertical_entry(message, vertical_id, state=state)
        return
    if label == "📇 CRM":
        await message.answer(
            "CRM: клиенты, сделки, задачи.\n"
            "Напишите: «найди клиента» или «покажи сделки».",
            reply_markup=business_menu_keyboard(),
        )
        return
    await message.answer(label, reply_markup=business_menu_keyboard())


@router.message(F.text.in_({b.label for b in DEVELOPER_MENU_BUTTONS}))
async def developer_section(message: Message, state: FSMContext) -> None:
    if not await _is_developer(message.from_user.id if message.from_user else None):
        await message.answer("Раздел доступен только владельцу.")
        return
    label = message.text or ""
    if label == BTN.HERCULES or label == "🟢 Hercules":
        await open_hercules(message, state)
        return
    await message.answer(
        f"⚙ {label}\n\n"
        "Инженерный модуль. Полный интерфейс — в веб-консоли.\n"
        "В Telegram используйте Консьержа для бизнес-задач.",
        reply_markup=developer_menu_keyboard(),
    )


@router.message(Command("hercules"))
@router.message(F.text == BTN.HERCULES)
async def open_hercules(message: Message, state: FSMContext) -> None:
    if not await _is_developer(message.from_user.id if message.from_user else None):
        await message.answer("Hercules доступен владельцу (Owner).")
        return
    await state.clear()
    from platform_hercules.runtime.hercules_runtime import hercules_runtime

    await message.answer(
        hercules_runtime.telegram_overview_ru(),
        reply_markup=hercules_menu_keyboard(),
    )


HERCULES_BTN = {
    "🟢 Hercules",
    "📊 Загрузка",
    "🖥 GPU",
    "⚙ CPU",
    "📦 Очереди",
    "🤖 Workers",
    "📈 Метрики",
    "📜 История",
}


@router.message(F.text.in_(HERCULES_BTN))
async def hercules_panel(message: Message, state: FSMContext) -> None:
    if not await _is_developer(message.from_user.id if message.from_user else None):
        await message.answer("Раздел Hercules — только для владельца.")
        return
    from platform_hercules.runtime.hercules_runtime import hercules_runtime

    text = message.text or ""
    dash = hercules_runtime.dashboard()
    if text in ("🟢 Hercules", "📊 Загрузка"):
        body = hercules_runtime.telegram_overview_ru()
    elif text == "🖥 GPU":
        g = dash["gpu"]
        body = (
            f"🖥 GPU\n\nБэкенд: {g['backend']}\n"
            f"Слоты: {g['used']}/{g['slots']}\n"
            f"VRAM ≈ {g['vram_mb_est']} МБ\n"
            f"Доступен: {'да' if g['available'] else 'нет (CPU fallback)'}"
        )
    elif text == "⚙ CPU":
        c = dash["cpu"]
        body = (
            f"⚙ CPU\n\nЯдра: {c['cores']}\nВоркеры: {c['workers']}\n"
            f"Активные: {c['active']}\nНагрузка ≈ {c['load_est']}%\n"
            f"RAM ≈ {c['ram_mb_est']} МБ"
        )
    elif text == "📦 Очереди":
        q = dash["queues"].get("hercules_lanes", {})
        lines = [f"• {k}: {v}" for k, v in list(q.items())[:12]]
        body = "📦 Очереди Hercules\n\n" + ("\n".join(lines) or "пусто")
    elif text == "🤖 Workers":
        lines = [f"• {w['id']} ({w['kind']}) load={w['load']}" for w in dash["workers"][:10]]
        body = "🤖 Workers\n\n" + "\n".join(lines)
    elif text == "📈 Метрики":
        m = dash["metrics"]
        body = (
            f"📈 Метрики\n\nRunning: {m['running']}\nFinished: {m['finished']}\n"
            f"Failed: {m['failed']}\nRetry: {m['retry']}\n"
            f"Jobs/sec: {m['jobs_per_sec']}\nLatency: {m['latency_avg_sec']}с\n"
            f"Cost: {m['cost_total']}"
        )
    else:
        jobs = dash["jobs"]
        lines = [j.get("line") or j.get("id") for j in jobs[:10]]
        body = "📜 История Hercules\n\n" + ("\n".join(lines) if lines else "Пока пусто")
    await message.answer(body, reply_markup=hercules_menu_keyboard())


@router.message(F.text == BTN.SETTINGS)
async def open_settings(message: Message) -> None:
    await message.answer(
        "⚙ Настройки\n\nЯзык: Русский\nРежим: для владельца\n"
        "Уведомления о готовности: включены.",
        reply_markup=main_menu_keyboard(
            include_developer=await _is_developer(message.from_user.id if message.from_user else None)
        ),
    )


@router.message(F.text == BTN.ALL_SECTIONS)
async def open_all_sections(message: Message) -> None:
    dev = await _is_developer(message.from_user.id if message.from_user else None)
    await message.answer("📂 Все разделы", reply_markup=all_sections_keyboard(include_developer=dev))


@router.message(F.text == BTN.DEVELOPER)
async def open_developer(message: Message) -> None:
    if not await _is_developer(message.from_user.id if message.from_user else None):
        await message.answer("Раздел для разработчика доступен только владельцу.")
        return
    await message.answer(
        "⚙ Для разработчика\n\nТехнические модули скрыты из ежедневной работы.",
        reply_markup=developer_menu_keyboard(),
    )


@router.message(F.text == BTN.HISTORY)
async def show_history(message: Message) -> None:
    await message.answer(app.history_text(_ukey(message)), reply_markup=ai_studio_keyboard())


@router.message(F.text == BTN.QUEUE)
async def show_queue(message: Message) -> None:
    await message.answer(app.queue_text(_ukey(message)))


@router.message(F.text == BTN.FAVORITES)
async def show_favorites(message: Message) -> None:
    await message.answer(app.favorites_text(_ukey(message)), reply_markup=ai_studio_keyboard())


@router.message(F.text == BTN.TEMPLATES)
async def open_templates(message: Message) -> None:
    await message.answer(
        "📦 Шаблоны\n\nВыберите отрасль:",
        reply_markup=template_categories_inline(),
    )


@router.message(F.text.in_({o.label for o in AI_STUDIO_OPTIONS}))
async def open_studio_option(message: Message, state: FSMContext) -> None:
    label = message.text or ""
    studio_id = app.resolve_studio_label(label)
    if not studio_id:
        return
    if studio_id == "history":
        await message.answer(app.history_text(_ukey(message)))
        return
    if studio_id == "favorites":
        await message.answer(app.favorites_text(_ukey(message)))
        return
    if studio_id == "beauty":
        await _open_beauty_vertical(message, state)
        return
    if studio_id == "settings":
        await message.answer(app.welcome_settings(), reply_markup=ai_studio_keyboard())
        return
    if studio_id == "templates":
        await open_templates(message)
        return
    steps = app.studio_steps(studio_id)
    await state.set_state(SuperAppFlow.studio_step)
    await state.update_data(studio_id=studio_id, step_index=0, answers={}, steps=steps)
    step = steps[0]
    text = f"{label}\n\n{step['prompt']}"
    if step.get("choices"):
        await message.answer(text, reply_markup=choices_inline("tsa:ch", step["choices"]))
    else:
        await state.set_state(SuperAppFlow.awaiting_free_text)
        await message.answer(text + "\n\nНапишите ответ сообщением.")


async def _open_beauty_vertical(message: Message, state: FSMContext) -> None:
    await state.set_state(SuperAppFlow.vertical_menu)
    await state.update_data(vertical_id="beauty")
    await message.answer(vfw.welcome("beauty"), reply_markup=vertical_menu_keyboard("beauty"))


@router.message(F.text == BTN.BEAUTY)
async def open_beauty_btn(message: Message, state: FSMContext) -> None:
    await _open_beauty_vertical(message, state)


@router.message(SuperAppFlow.vertical_menu)
async def vertical_menu_handler(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    data = await state.get_data()
    vertical_id = data.get("vertical_id") or "beauty"
    if text in (BTN.BACK_MAIN, BTN.BACK_STUDIO, BTN.AI_STUDIO):
        await state.clear()
        if text == BTN.BACK_MAIN:
            await back_main(message, state)
        else:
            await open_ai_studio(message, state)
        return
    if text == BTN.ASK_AI:
        await state.set_state(SuperAppFlow.ask_ai)
        await message.answer(app.welcome_ask_ai())
        return
    item = is_vertical_menu_label(vertical_id, text)
    if not item:
        # Natural language → wizard
        await _start_vertical_wizard(
            message, state, vertical_id=vertical_id, menu_id="post", seed={"idea": text}
        )
        return
    if item.action == "history":
        await message.answer(vfw.history_text(_ukey(message), vertical_id))
        return
    if item.action == "favorites":
        await message.answer(vfw.favorites_text(_ukey(message), vertical_id))
        return
    if item.action == "settings":
        await message.answer(vfw.settings_text(vertical_id))
        return
    if item.action == "calendar":
        await message.answer(
            "📅 На сколько дней построить контент-план?",
            reply_markup=calendar_periods_inline(vertical_id),
        )
        return
    if item.action == "marketing":
        await message.answer(vfw.marketing_text(vertical_id))
        return
    if item.action in ("studio", "wizard"):
        await _start_vertical_wizard(message, state, vertical_id=vertical_id, menu_id=item.id)
        return
    await message.answer(vfw.welcome(vertical_id), reply_markup=vertical_menu_keyboard(vertical_id))


async def _start_vertical_wizard(
    message: Message,
    state: FSMContext,
    *,
    vertical_id: str,
    menu_id: str,
    seed: dict[str, str] | None = None,
) -> None:
    steps = vfw.wizard_steps(vertical_id)
    await state.set_state(SuperAppFlow.vertical_wizard)
    await state.update_data(
        vertical_id=vertical_id,
        menu_id=menu_id,
        step_index=0,
        answers=dict(seed or {}),
        steps=steps,
    )
    step = steps[0]
    if step.get("choices"):
        await message.answer(step["prompt"], reply_markup=choices_inline("tsv:ch", step["choices"]))
    else:
        await message.answer(step["prompt"] + "\n\nНапишите ответ сообщением.")


@router.message(SuperAppFlow.vertical_wizard)
async def vertical_wizard_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text in MAIN_BTN_SET or text in (BTN.BACK_STUDIO, BTN.BEAUTY):
        await state.clear()
        if text == BTN.BEAUTY:
            await _open_beauty_vertical(message, state)
        return
    data = await state.get_data()
    steps: list[dict[str, Any]] = data.get("steps") or []
    idx = int(data.get("step_index") or 0)
    answers: dict[str, str] = dict(data.get("answers") or {})
    if idx >= len(steps):
        await state.clear()
        return
    step = steps[idx]
    # If choices exist, allow free-text override
    answers[step["id"]] = text
    await _advance_vertical_wizard(message, state, answers=answers, steps=steps, idx=idx + 1)


@router.callback_query(F.data.startswith("tsv:ch:"))
async def vertical_choice_cb(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    steps: list[dict[str, Any]] = data.get("steps") or []
    idx = int(data.get("step_index") or 0)
    answers: dict[str, str] = dict(data.get("answers") or {})
    if idx >= len(steps) or not callback.message:
        await callback.answer("Шаг устарел")
        return
    step = steps[idx]
    try:
        choice_i = int((callback.data or "").rsplit(":", 1)[-1])
        choice = (step.get("choices") or [])[choice_i]
    except Exception:
        await callback.answer("Неверный выбор")
        return
    answers[step["id"]] = choice
    await callback.answer(choice)
    await _advance_vertical_wizard(
        callback.message, state, answers=answers, steps=steps, idx=idx + 1
    )


async def _advance_vertical_wizard(
    message: Message,
    state: FSMContext,
    *,
    answers: dict[str, str],
    steps: list[dict[str, Any]],
    idx: int,
) -> None:
    data = await state.get_data()
    vertical_id = data.get("vertical_id") or "beauty"
    menu_id = data.get("menu_id") or "post"
    if idx < len(steps):
        await state.update_data(answers=answers, step_index=idx)
        step = steps[idx]
        if step.get("choices"):
            await message.answer(step["prompt"], reply_markup=choices_inline("tsv:ch", step["choices"]))
        else:
            await message.answer(step["prompt"] + "\n\nНапишите ответ сообщением.")
        return
    preview = vfw.preview_chain(vertical_id, answers)
    await state.set_state(SuperAppFlow.vertical_confirm)
    await state.update_data(answers=answers, vertical_id=vertical_id, menu_id=menu_id)
    await message.answer(
        preview,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=BTN.GENERATE_NOW, callback_data="tsv:gen:now")],
                [InlineKeyboardButton(text=BTN.RUN_CHAIN, callback_data="tsv:gen:chain")],
                [InlineKeyboardButton(text="Отмена", callback_data="tsa:cancel")],
            ]
        ),
    )


@router.callback_query(F.data == "tsv:gen:now")
async def vertical_gen_now(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    vertical_id = data.get("vertical_id") or "beauty"
    menu_id = data.get("menu_id") or "post"
    answers = dict(data.get("answers") or {})
    await state.clear()
    if not callback.message:
        await callback.answer()
        return
    await callback.message.answer(progress_message("prepare", eta_sec=3))
    await callback.message.answer(progress_message("generate", eta_sec=12))
    job = await vfw.run_menu_generation(
        app.user_key(callback.from_user.id if callback.from_user else 0),
        vertical_id,
        menu_id=menu_id,
        answers=answers,
    )
    await callback.message.answer(
        format_result_for_user(job) + "\n\nЧто дальше?",
        reply_markup=publish_after_vertical_inline(job.id),
    )
    await state.set_state(SuperAppFlow.vertical_menu)
    await state.update_data(vertical_id=vertical_id)
    await callback.message.answer("Меню Beauty AI", reply_markup=vertical_menu_keyboard(vertical_id))
    await callback.answer("Готово")


@router.callback_query(F.data == "tsv:gen:chain")
async def vertical_gen_chain(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    vertical_id = data.get("vertical_id") or "beauty"
    answers = dict(data.get("answers") or {})
    await state.clear()
    if not callback.message:
        await callback.answer()
        return
    uid = callback.from_user.id if callback.from_user else 0
    await callback.message.answer("Запускаю цепочку: промпт → изображение → описание → хэштеги…")
    result = await vfw.run_chain(app.user_key(uid), vertical_id, answers)
    lines = ["✅ Цепочка подготовлена", ""]
    for step_id, info in (result.get("steps") or {}).items():
        st = info.get("status", "")
        lines.append(f"• {step_id}: {st}")
    last_id = None
    for info in (result.get("steps") or {}).values():
        if info.get("task_id"):
            last_id = info["task_id"]
    await callback.message.answer(
        "\n".join(lines),
        reply_markup=publish_after_vertical_inline(last_id or "chain"),
    )
    await state.set_state(SuperAppFlow.vertical_menu)
    await state.update_data(vertical_id=vertical_id)
    await callback.message.answer("Меню Beauty AI", reply_markup=vertical_menu_keyboard(vertical_id))
    await callback.answer("Цепочка")


@router.callback_query(F.data.startswith("tsv:cal:"))
async def vertical_calendar_cb(callback: CallbackQuery) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 4 or not callback.message:
        await callback.answer()
        return
    vertical_id, days_s = parts[2], parts[3]
    try:
        days = int(days_s)
    except Exception:
        days = 30
    await callback.message.answer(vfw.calendar_text(vertical_id, days))
    await callback.answer(f"{days} дней")


@router.callback_query(F.data.startswith("tsv:act:"))
async def vertical_publish_act(callback: CallbackQuery) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 4 or not callback.message:
        await callback.answer()
        return
    action = parts[2]
    messages = {
        "publish": "Публикация подготовлена. Выберите канал через «Опубликовать» в Студии AI или укажите площадку.",
        "schedule": "Напишите: «опубликуй завтра в 10:00» — запланирую.",
        "download": "Файл доступен в истории генераций.",
        "staff": "Напишите имя сотрудника — отправлю результат.",
        "client": "Напишите клиента — подготовлю сообщение.",
        "chain": "Цепочка уже построена. Можно повторить через мастер Beauty AI.",
    }
    await callback.message.answer(messages.get(action, "Готово."))
    await callback.answer()


@router.message(SuperAppFlow.awaiting_free_text)
async def studio_free_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    steps: list[dict[str, Any]] = data.get("steps") or []
    idx = int(data.get("step_index") or 0)
    answers: dict[str, str] = dict(data.get("answers") or {})
    if idx >= len(steps):
        await state.clear()
        return
    step = steps[idx]
    answers[step["id"]] = (message.text or "").strip()
    await _advance_studio(
        message, state, answers=answers, steps=steps, idx=idx + 1, studio_id=data["studio_id"]
    )


MAIN_BTN_SET = {
    BTN.CONCIERGE,
    BTN.DASHBOARD,
    BTN.TASKS,
    BTN.NOTIFICATIONS,
    BTN.BUSINESS,
    BTN.AI_STUDIO,
    BTN.AI_COMMAND,
    BTN.WORK_MODE,
    BTN.MEMORY,
    BTN.AUTOMATION,
    BTN.SETTINGS,
    BTN.ALL_SECTIONS,
    BTN.DEVELOPER,
    BTN.BACK_MAIN,
    BTN.BACK_STUDIO,
    BTN.HISTORY,
    BTN.QUEUE,
    BTN.FAVORITES,
    BTN.ASK_AI,
    BTN.TEMPLATES,
    BTN.BEAUTY,
    BTN.GENERATE_NOW,
    BTN.HERCULES,
}


@router.message(SuperAppFlow.ask_ai, ~F.text.in_(MAIN_BTN_SET))
@router.message(SuperAppFlow.concierge_chat, ~F.text.in_(MAIN_BTN_SET))
async def concierge_chat(message: Message, state: FSMContext) -> None:
    # HOTFIX 46.2.2 — hard guard: active Add-car FSM must never hit AI Concierge
    try:
        from services.auto_add_vehicle_flow import ActiveFlowRoutingRequired, assert_no_active_add_vehicle

        await assert_no_active_add_vehicle(
            state,
            user_id=message.from_user.id if message.from_user else None,
        )
    except ActiveFlowRoutingRequired:
        logger.error(
            "TELEGRAM_UPDATE handler_selected=concierge_chat_BLOCKED reason=ACTIVE_FLOW_ROUTING_REQUIRED"
        )
        return

    text = (message.text or "").strip()
    data = await state.get_data()
    if data.get("ai_command") or data.get("voice_mode"):
        from platform_memory.memory_manager import memory_manager

        result = await memory_manager.run_with_memory(
            _ukey(message),
            text,
            channel="telegram",
            max_steps=3,
        )
        if result.get("type") == "smart_recall":
            await message.answer(
                result.get("reply_ru") or "Продолжаем.",
                reply_markup=memory_menu_keyboard(),
            )
            return
        if result.get("type") == "mode_switch":
            await message.answer(
                f"Режим: {result.get('indicator')}",
                reply_markup=work_mode_keyboard(),
            )
            return
        await message.answer(
            result.get("reply_ru") or "Готово.",
            reply_markup=ai_command_menu_keyboard(),
        )
        return
    # memory search follow-up
    if data.get("memory_search"):
        from platform_memory.memory_manager import memory_manager

        await state.update_data(memory_search=False)
        found = memory_manager.search(_ukey(message), text)
        lines = [f"Найдено: {found['count']}"]
        for r in found.get("results", [])[:8]:
            lines.append(f"• {r.get('title')} ({r.get('kind')})")
        await message.answer("\n".join(lines), reply_markup=memory_menu_keyboard())
        return
    owner = app.owner_ai_reply(text)
    if owner and not any(x in text.lower() for x in ("реклам", "видео", "картин", "изображ")):
        await message.answer(owner)
    result = app.handle_concierge_message(_ukey(message), text)
    await message.answer(result["text"])
    studio_id = result.get("studio_id")
    if studio_id and result.get("needs_clarify"):
        steps = app.studio_steps(studio_id)
        await state.set_state(SuperAppFlow.studio_step)
        await state.update_data(
            studio_id=studio_id,
            step_index=0,
            answers={"idea": text} if text else {},
            steps=steps,
        )
        step = steps[0]
        if step.get("choices"):
            await message.answer(step["prompt"], reply_markup=choices_inline("tsa:ch", step["choices"]))
        else:
            await state.set_state(SuperAppFlow.awaiting_free_text)
            await message.answer(step["prompt"] + "\n\nНапишите ответ сообщением.")


@router.message(SuperAppFlow.ask_ai)
@router.message(SuperAppFlow.concierge_chat)
async def concierge_menu_passthrough(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = message.text or ""
    if text == BTN.CONCIERGE:
        await open_concierge(message, state)
    elif text == BTN.AI_COMMAND:
        await open_ai_command(message, state)
    elif text == BTN.WORK_MODE:
        await open_work_mode(message, state)
    elif text == BTN.MEMORY:
        await open_memory(message, state)
    elif text == BTN.AUTOMATION:
        await open_automation(message, state)
    elif text == BTN.ASK_AI:
        await open_ask_ai(message, state)
    elif text == BTN.AI_STUDIO:
        await open_ai_studio(message, state)
    elif text == BTN.DASHBOARD:
        await open_dashboard(message)
    elif text == BTN.TASKS:
        await open_tasks(message)
    elif text == BTN.NOTIFICATIONS:
        await open_notifications(message)
    elif text == BTN.BUSINESS:
        await open_business(message, state)
    elif text == BTN.SETTINGS:
        await open_settings(message)
    elif text == BTN.ALL_SECTIONS:
        await open_all_sections(message)
    elif text == BTN.DEVELOPER:
        await open_developer(message)
    elif text == BTN.BACK_MAIN:
        await back_main(message, state)
    elif text == BTN.TEMPLATES:
        await open_templates(message)
    else:
        dev = await _is_developer(message.from_user.id if message.from_user else None)
        await message.answer("Главное меню", reply_markup=main_menu_keyboard(include_developer=dev))


@router.callback_query(F.data.startswith("tsa:ex:"))
async def concierge_example_cb(callback: CallbackQuery, state: FSMContext) -> None:
    ex = (callback.data or "").split("tsa:ex:", 1)[-1]
    await state.set_state(SuperAppFlow.concierge_chat)
    if callback.message:
        uid = callback.from_user.id if callback.from_user else 0
        result = app.handle_concierge_message(app.user_key(uid), ex)
        await callback.message.answer(result["text"])
        studio_id = result.get("studio_id")
        if studio_id and result.get("needs_clarify"):
            steps = app.studio_steps(studio_id)
            await state.set_state(SuperAppFlow.studio_step)
            await state.update_data(studio_id=studio_id, step_index=0, answers={"idea": ex}, steps=steps)
            step = steps[0]
            if step.get("choices"):
                await callback.message.answer(
                    step["prompt"], reply_markup=choices_inline("tsa:ch", step["choices"])
                )
            else:
                await state.set_state(SuperAppFlow.awaiting_free_text)
                await callback.message.answer(step["prompt"] + "\n\nНапишите ответ сообщением.")
    await callback.answer()


@router.callback_query(F.data.startswith("tsa:ch:"))
async def studio_choice_cb(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    steps: list[dict[str, Any]] = data.get("steps") or []
    idx = int(data.get("step_index") or 0)
    answers: dict[str, str] = dict(data.get("answers") or {})
    if idx >= len(steps) or not callback.message:
        await callback.answer("Шаг устарел")
        return
    step = steps[idx]
    try:
        choice_i = int((callback.data or "").rsplit(":", 1)[-1])
        choice = (step.get("choices") or [])[choice_i]
    except Exception:
        await callback.answer("Неверный выбор")
        return
    answers[step["id"]] = choice
    await callback.answer(choice)
    await _advance_studio(
        callback.message,
        state,
        answers=answers,
        steps=steps,
        idx=idx + 1,
        studio_id=data["studio_id"],
    )


@router.callback_query(F.data == "tsa:cancel")
async def cancel_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
        await callback.message.answer("Отменено.", reply_markup=ai_studio_keyboard())
    await callback.answer()


@router.callback_query(F.data == "tsa:gen:now")
async def confirm_gen_cb(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    studio_id = data.get("studio_id") or "ads"
    answers = dict(data.get("answers") or {})
    await state.clear()
    if callback.message:
        await _run_and_reply(callback.message, studio_id=studio_id, answers=answers)
    await callback.answer("Генерация")


@router.callback_query(F.data == "tsa:gen:edit")
async def edit_gen_cb(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    studio_id = data.get("studio_id") or "ads"
    steps = app.studio_steps(studio_id)
    await state.set_state(SuperAppFlow.studio_step)
    await state.update_data(studio_id=studio_id, step_index=0, answers={}, steps=steps)
    if callback.message and steps:
        step = steps[0]
        if step.get("choices"):
            await callback.message.answer(step["prompt"], reply_markup=choices_inline("tsa:ch", step["choices"]))
        else:
            await state.set_state(SuperAppFlow.awaiting_free_text)
            await callback.message.answer(step["prompt"] + "\n\nНапишите ответ сообщением.")
    await callback.answer()


@router.callback_query(F.data.startswith("tsa:tplcat:"))
async def template_cat_cb(callback: CallbackQuery) -> None:
    raw = (callback.data or "").split("tsa:tplcat:", 1)[-1]
    if not callback.message:
        await callback.answer()
        return
    if raw == "back":
        await callback.message.answer(
            "📦 Шаблоны — выберите отрасль:", reply_markup=template_categories_inline()
        )
        await callback.answer()
        return
    try:
        idx = int(raw)
        cat = TEMPLATE_CATEGORIES[idx]
    except Exception:
        await callback.answer("Нет категории")
        return
    items = templates_by_category(cat)
    titles = [t.title for t in items]
    await callback.message.answer(f"📦 {cat}", reply_markup=templates_inline(idx, titles))
    await callback.answer()


@router.callback_query(F.data.startswith("tsa:tpl:"))
async def template_pick_cb(callback: CallbackQuery, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 4 or not callback.message:
        await callback.answer()
        return
    try:
        cat_i, tpl_i = int(parts[2]), int(parts[3])
        cat = TEMPLATE_CATEGORIES[cat_i]
        item = templates_by_category(cat)[tpl_i]
    except Exception:
        await callback.answer("Шаблон не найден")
        return
    steps = app.studio_steps(item.studio_id)
    await state.set_state(SuperAppFlow.studio_step)
    await state.update_data(
        studio_id=item.studio_id,
        step_index=0,
        answers={"what": item.seed_prompt, "idea": item.seed_prompt},
        steps=steps,
    )
    await callback.message.answer(f"Шаблон: {item.title}\n\n{item.seed_prompt}\n\nУточним детали:")
    step = steps[0]
    if step.get("choices"):
        await callback.message.answer(step["prompt"], reply_markup=choices_inline("tsa:ch", step["choices"]))
    else:
        await state.set_state(SuperAppFlow.awaiting_free_text)
        await callback.message.answer(step["prompt"] + "\n\nНапишите ответ сообщением.")
    await callback.answer(item.title)


@router.callback_query(F.data.startswith("tsa:wf:"))
async def workflow_cb(callback: CallbackQuery, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 4 or not callback.message:
        await callback.answer()
        return
    action, job_id = parts[2], parts[3]
    messages = {
        "download": "Файл готов. Откройте результат или сохраните из истории.",
        "edit": "Напишите, что изменить — без повторного брифа.",
        "send": "Укажите получателя: «отправь клиенту …».",
        "video": "Продолжаем цепочку: создаём видео из результата…",
        "voice": "Продолжаем цепочку: добавляем озвучку…",
        "reels": "Готовим Reels на основе генерации…",
        "ads": "Готовим рекламный вариант…",
        "chain": "Продолжаем: изображение → видео → озвучка → публикация.",
    }
    chain_studio = {"video": "video", "voice": "voice", "reels": "reels", "ads": "ads", "chain": "video"}
    if action in chain_studio:
        job = app.pipeline.get(job_id)
        seed = (job.prompt if job else "")[:300]
        studio_id = chain_studio[action]
        steps = app.studio_steps(studio_id)
        await state.set_state(SuperAppFlow.studio_step)
        await state.update_data(
            studio_id=studio_id,
            step_index=0,
            answers={"what": seed, "idea": seed},
            steps=steps,
        )
        await callback.message.answer(messages.get(action) or "Продолжаем…")
        step = steps[0]
        if step.get("choices"):
            await callback.message.answer(step["prompt"], reply_markup=choices_inline("tsa:ch", step["choices"]))
        else:
            await state.set_state(SuperAppFlow.awaiting_free_text)
            await callback.message.answer(step["prompt"] + "\n\nНапишите ответ сообщением.")
    elif action == "publish":
        await callback.message.answer("Куда опубликовать?", reply_markup=publish_channels_inline(job_id))
    elif action == "back":
        await callback.message.answer("Что дальше?", reply_markup=post_generation_inline(job_id))
    elif action in messages:
        await callback.message.answer(messages[action])
    await callback.answer()


@router.callback_query(F.data.startswith("tsa:pub:"))
async def publish_cb(callback: CallbackQuery) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 4 or not callback.message:
        await callback.answer()
        return
    channel, job_id = parts[2], parts[3]
    job = app.pipeline.get(job_id)
    asset = (job.result.get("media_url") if job and job.result else None) or job_id
    caption = (job.prompt if job else "")[:200]
    try:
        from services.telegram_ai_super_app.providers import super_app_providers

        prep = super_app_providers.prepare_publish(
            channel=channel, asset_ref=str(asset), caption=caption
        )
        await callback.message.answer(
            sanitize_user_text(f"✅ Публикация подготовлена.\nКанал: {prep['channel']}")
        )
    except Exception as exc:  # noqa: BLE001
        await callback.message.answer(
            f"Не удалось подготовить публикацию: {sanitize_user_text(str(exc))}"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("tsa:fav:"))
async def fav_cb(callback: CallbackQuery) -> None:
    job_id = (callback.data or "").split(":")[-1]
    job = app.pipeline.toggle_favorite(job_id)
    await callback.answer("В избранном" if job and job.favorite else "Убрано из избранного")


@router.callback_query(F.data.startswith("tsa:retry:"))
async def retry_cb(callback: CallbackQuery, state: FSMContext) -> None:
    job_id = (callback.data or "").split(":")[-1]
    try:
        if callback.message:
            await callback.message.answer(progress_message("prepare", eta_sec=5))
            await callback.message.answer(progress_message("generate", eta_sec=12))
        new_job = await app.pipeline.retry(job_id)
    except Exception as exc:  # noqa: BLE001
        await callback.answer(sanitize_user_text(str(exc))[:50])
        return
    if callback.message:
        await callback.message.answer(
            format_result_for_user(new_job),
            reply_markup=post_generation_inline(new_job.id),
        )
    await callback.answer("Повтор запущён")


@router.callback_query(F.data.startswith("tsa:dup:"))
async def dup_cb(callback: CallbackQuery) -> None:
    job_id = (callback.data or "").split(":")[-1]
    try:
        app.pipeline.duplicate(job_id)
    except Exception as exc:  # noqa: BLE001
        await callback.answer(sanitize_user_text(str(exc))[:50])
        return
    await callback.answer("Дубликат создан")
    if callback.message:
        await callback.message.answer("Создан дубликат задачи. Можно повторить генерацию.")


@router.callback_query(F.data.startswith("tsa:export:"))
async def export_cb(callback: CallbackQuery) -> None:
    job_id = (callback.data or "").split(":")[-1]
    job = app.pipeline.get(job_id)
    if not job or not callback.message:
        await callback.answer("Не найдено")
        return
    await callback.message.answer(
        "📄 Экспорт\n\n"
        f"Тип: {job.modality}\n"
        f"Статус: {job.status}\n"
        f"Промпт: {sanitize_user_text(job.prompt)[:300]}\n"
        f"Стоимость: ≈ {job.cost_estimate:.3f} у.е."
    )
    await callback.answer("Экспорт")


async def _run_and_reply(message: Message, *, studio_id: str, answers: dict[str, str]) -> None:
    await message.answer(progress_message("prepare", eta_sec=3))
    await message.answer(progress_message("queue", eta_sec=5))
    await message.answer(progress_message("generate", eta_sec=15))
    job = await app.run_generation(_ukey(message), studio_id=studio_id, answers=answers)
    await message.answer(progress_message("process", eta_sec=2))
    await message.answer(
        format_result_for_user(job) + "\n\nЧто дальше?",
        reply_markup=post_generation_inline(job.id),
    )


async def _advance_studio(
    message: Message,
    state: FSMContext,
    *,
    answers: dict[str, str],
    steps: list[dict[str, Any]],
    idx: int,
    studio_id: str,
) -> None:
    if idx < len(steps):
        await state.update_data(answers=answers, step_index=idx)
        step = steps[idx]
        if step.get("choices"):
            await state.set_state(SuperAppFlow.studio_step)
            await message.answer(step["prompt"], reply_markup=choices_inline("tsa:ch", step["choices"]))
        else:
            await state.set_state(SuperAppFlow.awaiting_free_text)
            await message.answer(step["prompt"] + "\n\nНапишите ответ сообщением.")
        return

    draft = ConversationDraft(intent=studio_id, studio_id=studio_id, answers=dict(answers))
    preview = app.clarify_preview(draft)
    composed = app.draft_to_answers(draft)
    await state.set_state(SuperAppFlow.await_generate_confirm)
    await state.update_data(studio_id=studio_id, answers=composed)
    await message.answer(
        preview + "\n\nПромпт готов. Сгенерировать?",
        reply_markup=confirm_generate_inline(),
    )
