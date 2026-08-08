"""Telegram AI Super App service — Sprint 43.3 product UX over Unified Pipeline."""

from __future__ import annotations

from typing import Any

from platform_ai.pipeline import UnifiedAiPipeline, unified_ai_pipeline
from platform_ai.pipeline_models import AiChannel, AiTaskRecord, AiTaskRequest
from services.telegram_ai_super_app.catalog import AI_STUDIO_OPTIONS, BTN
from services.telegram_ai_super_app.concierge import format_plan_card, plan_from_text
from services.telegram_ai_super_app.conversation import conversation_memory
from services.telegram_ai_super_app.conversation_flow import (
    ConversationDraft,
    build_prompt_from_draft,
    detect_studio_from_text,
    is_short_idea,
    preview_brief,
    steps_for,
)
from services.telegram_ai_super_app.product_ux import (
    format_history_line,
    format_result_for_user,
    sanitize_user_text,
)
from services.telegram_ai_super_app.studios import BEAUTY_SCENARIOS, compose_generation_prompt, studio_steps


class TelegramAiSuperApp:
    """Channel façade — all generation goes through UnifiedAiPipeline."""

    VERSION = "43.4"

    def __init__(self, pipeline: UnifiedAiPipeline | None = None) -> None:
        self.pipeline = pipeline or unified_ai_pipeline
        self.memory = conversation_memory

    def user_key(self, telegram_id: int, tenant_id: str | None = None) -> str:
        return self.memory.key(telegram_id, tenant_id)

    def welcome_concierge(self) -> str:
        return (
            "Здравствуйте.\n\n"
            "Что хотите сделать?\n\n"
            "Например:\n"
            "• Создай рекламу\n"
            "• Создай видео\n"
            "• Создай картинку\n"
            "• Озвучь текст\n"
            "• Открыть студию AI\n"
            "• Проанализируй продажи\n"
            "• Подготовь КП\n"
            "• Создай договор\n"
            "• Покажи прибыль\n"
            "• Создай презентацию\n\n"
            "Пишите обычным языком — я уточню детали и подготовлю результат."
        )

    def welcome_studio(self) -> str:
        return (
            "🎨 Студия AI\n\n"
            "Выберите задачу — или напишите идею своими словами.\n"
            "Длинные промпты не нужны: я задам 2–3 вопроса и предложу сгенерировать."
        )

    def welcome_beauty(self) -> str:
        try:
            from platform_vertical_ai.framework import vertical_ai_framework

            return vertical_ai_framework.welcome("beauty")
        except Exception:
            from services.telegram_ai_super_app.studios import BEAUTY_SCENARIOS

            items = "\n".join(f"• {x}" for x in BEAUTY_SCENARIOS)
            return f"💅 Beauty AI\n\nГотовые сценарии:\n\n{items}"

    def welcome_settings(self) -> str:
        return (
            "⚙ Настройки студии\n\n"
            "Язык: Русский\n"
            "Режим: для владельца\n"
            "Уведомления о готовности: включены\n\n"
            "Технические детали скрыты — вы работаете только с задачами."
        )

    def welcome_ask_ai(self) -> str:
        return (
            "💬 Спросить AI\n\n"
            "Напишите, что нужно — рекламу, видео, анализ, документ или идею.\n"
            "Если мало деталей, я уточню."
        )

    def resolve_studio_label(self, label: str) -> str | None:
        if label == BTN.BEAUTY:
            return "beauty"
        for opt in AI_STUDIO_OPTIONS:
            if opt.label == label:
                return opt.id
        return None

    def handle_concierge_message(self, user_key: str, text: str) -> dict[str, Any]:
        ctx = self.memory.get_context(user_key)
        last_mod = ctx.get("last_modality")
        plan = plan_from_text(text, last_modality=last_mod)
        self.memory.add(user_key, "user", text)
        card = sanitize_user_text(format_plan_card(plan))
        self.memory.add(user_key, "ai", card, intent=plan.intent)
        studio_id = plan.studio_id or detect_studio_from_text(text)
        self.memory.set_context(
            user_key,
            last_modality=plan.modality,
            last_vertical=plan.vertical,
            last_agent=plan.agent,
            last_studio=studio_id,
        )
        needs_clarify = is_short_idea(text) or studio_id in (
            "ads",
            "image",
            "video",
            "reels",
            "voice",
            "beauty",
            "text",
            "prompt",
            "document",
            "presentation",
        )
        return {
            "plan": plan,
            "text": card,
            "studio_id": studio_id if needs_clarify else plan.studio_id,
            "needs_clarify": needs_clarify and bool(studio_id),
            "idea": text,
        }

    def start_clarify_draft(self, studio_id: str, idea: str = "") -> ConversationDraft:
        draft = ConversationDraft(intent=studio_id, studio_id=studio_id)
        if idea.strip():
            draft.answers["idea"] = idea.strip()
        return draft

    def clarify_preview(self, draft: ConversationDraft) -> str:
        return sanitize_user_text(preview_brief(draft))

    def draft_to_answers(self, draft: ConversationDraft) -> dict[str, str]:
        answers = dict(draft.answers)
        if "what" not in answers and answers.get("idea"):
            answers["what"] = answers["idea"]
        if "goal" not in answers and answers.get("idea"):
            answers["goal"] = answers["idea"]
        answers["_composed"] = build_prompt_from_draft(draft)
        return answers

    def _modality_for(self, studio_id: str, modality: str | None) -> str:
        opt = next((o for o in AI_STUDIO_OPTIONS if o.id == studio_id), None)
        mod = modality or (opt.modality if opt and opt.modality not in (None, "prompt", "workflow") else "text")
        if studio_id == "prompt":
            return "prompt"
        if studio_id in ("document", "documents"):
            return "document"
        if studio_id in ("presentation", "presentations"):
            return "presentation"
        if studio_id == "text":
            return "text"
        if studio_id == "voice_clone":
            return "voice"
        if studio_id in ("ads", "social", "beauty", "auto", "crypto", "agro", "legal", "post", "script", "design", "reels"):
            if studio_id == "reels":
                return "video"
            if studio_id == "design":
                return "image"
            if studio_id == "ads":
                return "ads"
            return "text"
        return mod or "text"

    async def run_generation(
        self,
        user_key: str,
        *,
        studio_id: str,
        answers: dict[str, str],
        modality: str | None = None,
    ) -> AiTaskRecord:
        mod = self._modality_for(studio_id, modality)
        meta = dict(answers)
        composed = meta.pop("_composed", None)
        prompt = composed or compose_generation_prompt(studio_id, meta)
        req = AiTaskRequest(
            owner_id=user_key,
            modality=mod,
            prompt=prompt,
            channel=AiChannel.TELEGRAM.value,
            meta=meta,
            studio_id=studio_id,
            vertical=studio_id if studio_id in ("beauty", "auto", "crypto", "agro", "legal") else None,
            optimize_prompt=True,
        )
        task = await self.pipeline.run(req)
        preview = format_result_for_user(task)
        self.memory.add(user_key, "ai", preview[:500], job_id=task.id)
        self.memory.set_context(
            user_key,
            last_modality=mod,
            last_job_id=task.id,
            last_prompt=prompt,
        )
        return task

    def history_text(self, user_key: str, *, query: str | None = None) -> str:
        tasks = self.pipeline.search(user_key, query or "") if query else self.pipeline.list_for_owner(user_key, limit=12)
        if not tasks:
            return "📚 История пуста.\n\nСоздайте первую генерацию в Студии AI."
        lines = ["📚 История генераций", "", "Последние:", ""]
        for t in tasks:
            lines.append(format_history_line(t))
            lines.append(f"  Повторить · Избранное · Экспорт — кнопки после открытия результата")
            lines.append("")
        return "\n".join(lines)

    def queue_text(self, user_key: str) -> str:
        tasks = self.pipeline.list_for_owner(user_key, limit=15)
        if not tasks:
            return "Сейчас нет активных задач."
        lines = ["⏳ Ваши задачи:", ""]
        for t in tasks:
            lines.append(format_history_line(t))
            if t.error:
                lines.append(f"  Ошибка: {sanitize_user_text(str(t.error))}")
        return "\n".join(lines)

    def favorites_text(self, user_key: str) -> str:
        favs = self.pipeline.favorites(user_key)
        if not favs:
            return "⭐ Избранное пусто.\n\nСохраняйте промпты, картинки, видео и шаблоны кнопкой «В избранное»."
        lines = ["⭐ Избранное:", ""]
        for t in favs:
            lines.append(format_history_line(t))
        return "\n".join(lines)

    def owner_dashboard_text(self, user_key: str) -> str:
        dash = self.pipeline.owner_dashboard(user_key)
        usage = dash["ai_usage"]
        return (
            "📊 Дашборд\n\n"
            f"Активные задачи: {dash['queue_depth']}\n"
            f"Генераций: {usage.get('generations', 0)}\n"
            f"Стоимость: {dash['cost_total']} у.е.\n"
            f"Ошибки: {usage.get('errors', 0)}\n"
            f"Среднее время: {usage.get('avg_duration_sec', 0)}с\n\n"
            "Подробности по моделям скрыты — смотрите историю генераций."
        )

    def owner_ai_reply(self, text: str) -> str | None:
        q = (text or "").lower()
        owner_hints = {
            "продаж": "Могу разобрать продажи: период, вертикаль и топ-сделки. Уточните период?",
            "кп": "Подготовлю коммерческое предложение. Для кого и по какому продукту?",
            "презентац": "Соберу презентацию. Тема и число слайдов?",
            "прибыл": "Покажу сводку прибыли по доступным данным. За какой период?",
            "реклам": "Создам рекламу. Какой бизнес и цель?",
            "договор": "Подготовлю черновик договора. Стороны и предмет?",
            "коммерческ": "Готовлю коммерческое предложение. Кому адресовано?",
        }
        for key, reply in owner_hints.items():
            if key in q:
                return reply
        return None

    def studio_steps(self, studio_id: str) -> list[dict[str, Any]]:
        # Prefer short clarify steps (≤3) for product UX
        if studio_id == "beauty":
            try:
                from platform_vertical_ai.framework import vertical_ai_framework

                return vertical_ai_framework.wizard_steps("beauty")
            except Exception:
                return [
                    {
                        "id": "what",
                        "prompt": "💅 Что создать для салона?",
                        "choices": list(BEAUTY_SCENARIOS),
                    }
                ]
        clarify = steps_for(studio_id)
        if studio_id == "voice_clone":
            return [{"id": "text", "prompt": "Текст для озвучки вашим голосом?", "choices": None}]
        if clarify and studio_id not in ("settings", "templates", "history", "favorites"):
            return [{"id": s.id, "prompt": s.question, "choices": s.choices} for s in clarify]
        return studio_steps(studio_id)

    def is_main_button(self, text: str) -> bool:
        return text in {
            BTN.CONCIERGE,
            BTN.DASHBOARD,
            BTN.TASKS,
            BTN.NOTIFICATIONS,
            BTN.BUSINESS,
            BTN.AI_STUDIO,
            BTN.SETTINGS,
            BTN.ALL_SECTIONS,
            BTN.DEVELOPER,
            BTN.BACK_MAIN,
            BTN.HISTORY,
            BTN.QUEUE,
            BTN.FAVORITES,
            BTN.ASK_AI,
            BTN.TEMPLATES,
            BTN.BEAUTY,
        }


telegram_ai_super_app = TelegramAiSuperApp()
