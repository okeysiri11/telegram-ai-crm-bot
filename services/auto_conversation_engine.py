"""Sprint 46.1 — Auto conversation engine (search immediately, refine without re-asking)."""

from __future__ import annotations

import re
from typing import Any

from services.auto_client_output import format_car_card_ru, is_staff_role, sanitize_ai_reply_for_client
from services.auto_conversation_quality_guard import apply_conversation_quality_guard
from services.auto_dealer_settings import auto_dealer_settings
from services.auto_dialog_state import LEASING, REFINING, SEARCHING, auto_dialog_state
from services.auto_human_conversation_policy import (
    is_short_contextual,
    leasing_ack_ru,
    leasing_closing_ru,
    leasing_results_intro_ru,
    resolve_ai_style,
)
from services.auto_request_memory import (
    AutoSearchSlots,
    auto_request_memory,
    conversation_summary_ru,
    parse_search_utterance,
)
from services.auto_saved_search import auto_saved_search


AI_MANAGER_WELCOME_RU = (
    "Напишите, что нужно.\n\n"
    "Например:\n"
    "• Найди BMW X5 в Одессе до $15 000\n"
    "• Продай мой Mercedes GLE\n"
    "• Сколько стоит мой автомобиль?\n"
    "• Найди автомобиль под перепродажу\n"
    "• Сравни эти две машины"
)


def looks_like_search(text: str) -> bool:
    low = (text or "").lower()
    if re.search(r"найд|поиск|покажи|ищи|x5|bmw|mercedes|audi|toyota|до\s*\$?\d|можно\s+до", low):
        return True
    if re.search(r"только\s+дизел|дешевле|сравни|сохрани|оставь\s+только", low):
        return True
    return False


def is_skip_clarify(text: str) -> bool:
    low = (text or "").strip().lower()
    return low in {"пропустить", "не знаю", "нет", "-", "skip", "1", "2", "да"} or "не задавай" in low


class AutoConversationEngine:
    """Conversation-first automotive AI manager."""

    def welcome(self) -> str:
        return AI_MANAGER_WELCOME_RU

    def _guard(
        self,
        body: str,
        *,
        slots: AutoSearchSlots,
        settings: dict[str, Any],
        role: str,
        debug: bool,
    ) -> str:
        known = slots.to_dict()
        return apply_conversation_quality_guard(
            body,
            known=known,
            settings=settings,
            role=role,
            debug=debug,
        )

    async def handle(
        self,
        user_id: int,
        text: str,
        *,
        role: str = "client",
        debug: bool = False,
    ) -> dict[str, Any]:
        raw = (text or "").strip()
        settings = resolve_ai_style(auto_dealer_settings.get(user_id))
        # merge dealer search settings
        dealer = auto_dealer_settings.get(user_id)
        settings = {**dealer, **settings}

        # 1) Deterministic dialog state first (VIN / short answers)
        transition = auto_dialog_state.resolve_short_answer(user_id, raw)
        if transition and transition.get("event") in {"VIN_SKIPPED", "WAITING_FOR_VIN", "VIN_PROVIDED"}:
            return {
                "reply_ru": self._guard(
                    transition.get("reply_ru") or "",
                    slots=auto_request_memory.get(user_id) or AutoSearchSlots(),
                    settings=settings,
                    role=role,
                    debug=debug,
                ),
                "slots": (auto_request_memory.get(user_id) or AutoSearchSlots()).to_dict(),
                "cars": [],
                "started_search": False,
                "dialog_event": transition.get("event"),
                "continue_workflow": transition.get("continue_workflow"),
            }

        # Short contextual replies with active search → refine/search, not new intent
        force_from_short = bool(transition and transition.get("force_search"))

        prev = auto_request_memory.get(user_id)
        if is_short_contextual(raw) and prev and (prev.brand or prev.model) and not transition:
            # Do not treat as standalone intent
            force_from_short = True

        slots = auto_request_memory.update(user_id, raw)

        # apply owner defaults if missing
        if not slots.city and settings.get("default_city"):
            slots.city = settings["default_city"]
            auto_request_memory._slots[user_id] = slots
        if slots.currency == "USD" and settings.get("default_currency"):
            slots.currency = settings["default_currency"]

        auto_dialog_state.update_known(
            user_id,
            brand=slots.brand,
            model=slots.model,
            city=slots.city,
            budget_max=slots.budget_max,
            fuel=slots.fuel,
            intent=slots.intent,
        )

        # Leasing entry: single word
        if re.fullmatch(r"лизинг|leasing", raw.lower()):
            auto_dialog_state.set_phase(user_id, LEASING, intent="LEASING", workflow="leasing")
            slots.intent = "LEASING"
            auto_request_memory._slots[user_id] = slots
            return {
                "reply_ru": self._guard(
                    "Конечно. Какой автомобиль рассматриваете?",
                    slots=slots,
                    settings=settings,
                    role=role,
                    debug=debug,
                ),
                "slots": slots.to_dict(),
                "cars": [],
                "started_search": False,
                "intent": "LEASING",
            }

        # Leasing details line (intent from взнос / prior phase)
        if slots.intent == "LEASING" or auto_dialog_state.get(user_id).phase == LEASING:
            slots.intent = "LEASING"
            auto_dialog_state.set_phase(user_id, LEASING, intent="LEASING", workflow="leasing")
            if slots.brand or slots.model:
                cars = await self._run_search(user_id, slots, settings)
                auto_request_memory.set_results(user_id, cars)
                self._persist_memory(user_id, slots)
                ack = leasing_ack_ru(name=slots.client_name, label=slots.label_ru())
                if cars:
                    body = (
                        f"{ack}\n\n{leasing_results_intro_ru()}\n\n"
                        + "\n\n".join(format_car_card_ru(c) for c in cars[: int(settings.get("max_results", 7))])
                        + f"\n\n{leasing_closing_ru()}"
                    )
                else:
                    body = f"{ack}\n\nПока подходящих вариантов нет. Могу расширить поиск."
                return {
                    "reply_ru": self._guard(body, slots=slots, settings=settings, role=role, debug=debug),
                    "slots": slots.to_dict(),
                    "cars": cars,
                    "started_search": True,
                    "intent": "LEASING",
                    "lead_id": auto_request_memory.ensure_lead(user_id),
                }
            return {
                "reply_ru": self._guard(
                    "Конечно. Какой автомобиль рассматриваете?",
                    slots=slots,
                    settings=settings,
                    role=role,
                    debug=debug,
                ),
                "slots": slots.to_dict(),
                "cars": [],
                "started_search": False,
                "intent": "LEASING",
            }

        # compare / save follow-ups
        if re.search(r"сравни\s+перв|перв(ые|ых)?\s+две\s+сравни|сравни.*перв|перв.*сравни", raw.lower()):
            return self._finalize_result(self._compare(user_id, n=2, role=role, debug=debug), slots, settings, role, debug)
        if re.search(r"(втор(ую|ая)|2[- ]?ю)\s+сохран", raw.lower()) or re.search(
            r"сохран.*(втор|2)", raw.lower()
        ):
            return self._finalize_result(self._save_nth(user_id, index=1, role=role), slots, settings, role, debug)

        if re.search(r"следить|монитор|новые", raw.lower()):
            auto_saved_search.save(user_id, slots)
            slots.mode = "monitor"
            return {
                "reply_ru": self._guard(
                    f"🔔 Слежу за новыми: {slots.label_ru()}. Сообщу в Telegram.",
                    slots=slots,
                    settings=settings,
                    role=role,
                    debug=debug,
                ),
                "slots": slots.to_dict(),
                "cars": [],
                "started_search": False,
            }

        intent_buy = bool(
            re.search(r"найд|куп|поиск|покажи|x5|bmw|дизел|бензин|дешевле|201\d|одесс|можно\s+до", raw.lower())
        ) or force_from_short
        lead_id = auto_request_memory.get_lead_id(user_id)
        if lead_id is None and (intent_buy or slots.brand or slots.model):
            lead_id = auto_request_memory.ensure_lead(user_id)

        max_q = int(settings.get("max_clarifying_questions", 1))
        if not settings.get("ask_optional_questions", False):
            max_q = min(max_q, 1)
        search_immediately = bool(settings.get("search_immediately", True))

        can_search = bool(slots.brand or slots.model or looks_like_search(raw) or force_from_short)
        # Sufficient context: brand+budget or brand+city → search now
        sufficient = bool(
            (slots.brand or slots.model)
            and (slots.budget_max or slots.city or force_from_short or search_immediately)
        )
        force_search = (
            search_immediately
            or is_skip_clarify(raw)
            or force_from_short
            or "не задавай" in raw.lower()
            or sufficient
        )

        if can_search and force_search:
            auto_dialog_state.set_phase(
                user_id,
                REFINING if prev and (prev.brand or prev.model) else SEARCHING,
                intent=slots.intent or "BUY_CAR",
            )
            cars = await self._run_search(user_id, slots, settings)
            auto_request_memory.set_results(user_id, cars)
            self._persist_memory(user_id, slots)
            ack = f"Ищу {slots.label_ru()}."
            if not cars:
                body = f"{ack}\n\nПока ничего не нашёл. Уточните фильтр или расширьте бюджет."
            else:
                body = f"{ack}\n\nНашёл {len(cars)} вариант(ов)."
                cards = "\n\n".join(
                    format_car_card_ru(c) for c in cars[: int(settings.get("max_results", 7))]
                )
                body = f"{body}\n\n{cards}"
            if is_staff_role(role) and debug and settings.get("show_technical_classification"):
                body += f"\n\n[debug] lead={lead_id} slots={slots.to_dict()}"
            return {
                "reply_ru": self._guard(body, slots=slots, settings=settings, role=role, debug=debug),
                "slots": slots.to_dict(),
                "cars": cars,
                "started_search": True,
                "lead_id": lead_id,
                "summary_ru": conversation_summary_ru(slots),
            }

        missing = []
        if not slots.brand and not slots.model:
            missing.append("марку/модель")
        if max_q > 0 and missing and not force_search:
            return {
                "reply_ru": self._guard(
                    f"Уточните {missing[0]} — или напишите «ищи».",
                    slots=slots,
                    settings=settings,
                    role=role,
                    debug=debug,
                ),
                "slots": slots.to_dict(),
                "cars": [],
                "started_search": False,
            }

        if re.search(r"прода|сколько\s+стоит|оцен", raw.lower()):
            return {
                "reply_ru": self._guard(
                    "Могу помочь с продажей или оценкой. Напишите марку, модель и город.",
                    slots=slots,
                    settings=settings,
                    role=role,
                    debug=debug,
                ),
                "slots": slots.to_dict(),
                "cars": [],
                "started_search": False,
            }

        return {
            "reply_ru": self._guard(AI_MANAGER_WELCOME_RU, slots=slots, settings=settings, role=role, debug=debug),
            "slots": slots.to_dict(),
            "cars": [],
            "started_search": False,
        }

    def _finalize_result(
        self,
        result: dict[str, Any],
        slots: AutoSearchSlots,
        settings: dict[str, Any],
        role: str,
        debug: bool,
    ) -> dict[str, Any]:
        result["reply_ru"] = self._guard(
            result.get("reply_ru") or "",
            slots=slots,
            settings=settings,
            role=role,
            debug=debug,
        )
        return result

    async def _run_search(
        self,
        user_id: int,
        slots: AutoSearchSlots,
        settings: dict[str, Any],
    ) -> list[dict[str, Any]]:
        from services.auto_search_orchestrator import auto_search_orchestrator

        try:
            result = await auto_search_orchestrator.search(
                slots,
                user_id=user_id,
                settings=settings,
                mode=slots.mode or "fast",
            )
            cars = list(result.get("listings") or [])
        except Exception:
            cars = []

        if not cars:
            cars = [c for c in self._demo_inventory(slots)]
            cars = [
                {**c, "make": c.get("brand"), "location": c.get("city"), "listing_url": c.get("url")}
                for c in cars
            ]

        cars = self._filter(cars, slots)
        limit = int(settings.get("max_results", 7))
        if slots.mode == "fast":
            limit = min(limit, 7)
        return cars[:limit]

    def _filter(self, cars: list[dict[str, Any]], slots: AutoSearchSlots) -> list[dict[str, Any]]:
        out = []
        for c in cars:
            blob = " ".join(str(c.get(k, "")) for k in ("brand", "model", "title", "fuel", "city", "name", "make")).lower()
            if slots.model and slots.model.lower() not in blob and slots.model.lower() not in str(c.get("model", "")).lower():
                if "x5" in (slots.model or "").lower() and "x5" not in blob:
                    continue
            if slots.fuel:
                fuel = str(c.get("fuel") or c.get("engine") or "").lower()
                want = slots.fuel
                if want == "diesel" and "диз" not in fuel and "diesel" not in fuel and "диз" not in blob:
                    continue
            if slots.budget_max is not None:
                price = c.get("price") or c.get("price_usd") or c.get("cost")
                try:
                    if price is not None and float(price) > float(slots.budget_max):
                        continue
                except (TypeError, ValueError):
                    pass
            if slots.year_min:
                try:
                    y = int(c.get("year") or 0)
                    if y and y < slots.year_min:
                        continue
                except (TypeError, ValueError):
                    pass
            out.append(c)
        return out or cars

    def _demo_inventory(self, slots: AutoSearchSlots) -> list[dict[str, Any]]:
        brand = slots.brand or "BMW"
        model = slots.model or "X5"
        city = slots.city or "Одесса"
        base_price = float(slots.budget_max or 14000)
        fuels = ["дизель", "дизель", "бензин", "дизель", "гибрид", "дизель", "бензин"]
        cars = []
        for i, fuel in enumerate(fuels, start=1):
            price = base_price - i * 300
            cars.append(
                {
                    "id": f"demo_{i}",
                    "brand": brand,
                    "model": model,
                    "title": f"{brand} {model}",
                    "year": 2015 + (i % 5),
                    "price": max(5000, price),
                    "fuel": fuel,
                    "city": city,
                    "mileage": 80000 + i * 7000,
                    "url": f"https://example.com/cars/{i}",
                    "photo": None,
                }
            )
        return cars

    def _compare(self, user_id: int, *, n: int, role: str, debug: bool) -> dict[str, Any]:
        cars = auto_request_memory.results(user_id)[:n]
        if len(cars) < 2:
            return {"reply_ru": "Нужно минимум два результата. Сначала выполните поиск.", "cars": cars}
        lines = ["Сравнение:"]
        for i, c in enumerate(cars, 1):
            lines.append(f"{i}) {format_car_card_ru(c)}")
        return {"reply_ru": "\n\n".join(lines), "cars": cars, "started_search": False}

    def _save_nth(self, user_id: int, *, index: int, role: str) -> dict[str, Any]:
        cars = auto_request_memory.results(user_id)
        if index >= len(cars):
            return {"reply_ru": "Не нашёл этот вариант в текущей подборке.", "cars": cars}
        car = cars[index]
        auto_request_memory.save_favorite(user_id, car)
        return {"reply_ru": f"Добавил в избранное: {car.get('title') or car.get('model')}.", "cars": cars}

    def _persist_memory(self, user_id: int, slots: AutoSearchSlots) -> None:
        try:
            from platform_memory.memory_manager import memory_manager

            memory_manager.save(
                f"tg:{user_id}",
                title="Автопоиск",
                content=conversation_summary_ru(slots),
                level="working",
                kind="auto_search",
                channel="telegram",
                tags=["auto", "search"],
                metadata=slots.to_dict(),
            )
        except Exception:
            pass


auto_conversation_engine = AutoConversationEngine()
