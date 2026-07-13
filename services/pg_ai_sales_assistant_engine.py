# AI Sales Assistant v1 — customer Q&A, vehicles, financing, contacts, meetings, handoffs.

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from aiogram import Bot

from config import BOT_TOKEN, MANAGER_ID, MANAGERS, OWNER_ID
from database.models.ai_sales_assistant import SalesSessionStatus
from database.session import get_session
from openrouter import ask_openrouter
from repositories.ai_sales_assistant_repository import SalesAssistantRepository
from repositories.car_repository import CarRepository
from repositories.user_role_repository import UserRoleRepository
from services.calendar_service import CalendarService
from services.pg_car_engine import CarEngineV1
from services.pg_lead_automation_engine import LeadAutomationEngineV1

logger = logging.getLogger(__name__)

SALES_ASSISTANT_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})

SALES_SYSTEM_PROMPT = """
Ты AI Sales Assistant автосалона. Помогаешь клиентам:
- отвечать на вопросы об автомобилях;
- рассказывать о доступных авто из инвентаря;
- объяснять условия покупки и финансирования;
- мягко собирать контактные данные;
- предлагать записаться на встречу или тест-драйв.

Правила:
- отвечай кратко и дружелюбно на русском языке;
- не выдумывай авто — используй только переданный инвентарь;
- если клиент просит менеджера — согласись и сообщи, что передашь заявку;
- для точного расчёта финансирования попроси сумму, взнос, срок и ставку;
- не запрашивай лишние персональные данные без необходимости.
"""

INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "vehicle": (
        "авто", "машин", "vin", "марка", "модель", "каталог", "инвентар",
        "camry", "toyota", "honda", "bmw", "mercedes", "есть ли",
    ),
    "financing": (
        "кредит", "финанс", "рассроч", "платеж", "взнос", "ставк", "loan", "finance",
        "ежемесяч", "процент",
    ),
    "contact": (
        "контакт", "телефон", "email", "почта", "имя", "связ", "перезвон",
        "оставить номер",
    ),
    "schedule": (
        "встреч", "запис", "тест-драйв", "test drive", "приехать", "визит",
        "когда можно", "расписан",
    ),
    "manager": (
        "менеджер", "человек", "оператор", "живой", "переключ", "manager",
        "позови", "соедини",
    ),
}

DEFAULT_ANNUAL_RATE = Decimal("12")
DEFAULT_TERM_MONTHS = 36


class AiSalesAssistantError(Exception):
    pass


class AiSalesAssistantEngineV1:
    @staticmethod
    async def is_staff(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in SALES_ASSISTANT_ROLES for role in roles)

    @staticmethod
    def detect_intent(text: str) -> str:
        lowered = text.lower()
        scores: dict[str, int] = {intent: 0 for intent in INTENT_KEYWORDS}
        for intent, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in lowered:
                    scores[intent] += 1
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
        return "general"

    @staticmethod
    def calculate_financing(
        *,
        vehicle_price: Decimal | float | int,
        down_payment: Decimal | float | int = 0,
        annual_rate_percent: Decimal | float | int = DEFAULT_ANNUAL_RATE,
        term_months: int = DEFAULT_TERM_MONTHS,
    ) -> dict[str, Any]:
        price = Decimal(str(vehicle_price))
        down = Decimal(str(down_payment))
        rate = Decimal(str(annual_rate_percent))
        months = int(term_months)

        if price <= 0:
            raise AiSalesAssistantError("Vehicle price must be positive")
        if down < 0 or down >= price:
            raise AiSalesAssistantError("Down payment must be between 0 and vehicle price")
        if months <= 0:
            raise AiSalesAssistantError("Term must be positive")

        loan_amount = price - down
        monthly_rate = rate / Decimal("100") / Decimal("12")

        if monthly_rate == 0:
            monthly_payment = loan_amount / Decimal(months)
        else:
            factor = (1 + monthly_rate) ** months
            monthly_payment = loan_amount * monthly_rate * factor / (factor - 1)

        total_paid = monthly_payment * Decimal(months) + down
        total_interest = total_paid - price

        return {
            "vehicle_price": str(price.quantize(Decimal("0.01"))),
            "down_payment": str(down.quantize(Decimal("0.01"))),
            "loan_amount": str(loan_amount.quantize(Decimal("0.01"))),
            "annual_rate_percent": str(rate),
            "term_months": months,
            "monthly_payment": str(monthly_payment.quantize(Decimal("0.01"))),
            "total_paid": str(total_paid.quantize(Decimal("0.01"))),
            "total_interest": str(total_interest.quantize(Decimal("0.01"))),
        }

    @staticmethod
    def format_financing(financing: dict[str, Any]) -> str:
        return (
            "🧮 Расчёт финансирования\n\n"
            f"Цена авто: {financing['vehicle_price']}\n"
            f"Первый взнос: {financing['down_payment']}\n"
            f"Сумма кредита: {financing['loan_amount']}\n"
            f"Ставка: {financing['annual_rate_percent']}% годовых\n"
            f"Срок: {financing['term_months']} мес.\n"
            f"Ежемесячный платёж: {financing['monthly_payment']}\n"
            f"Общая сумма выплат: {financing['total_paid']}\n"
            f"Переплата: {financing['total_interest']}"
        )

    @staticmethod
    async def _inventory_context(limit: int = 8) -> str:
        cars = await CarEngineV1.list_cars(OWNER_ID, limit=limit)
        if not cars:
            return "Инвентарь пуст."
        lines = ["Доступные автомобили:"]
        for car in cars:
            lines.append(
                f"- {car.get('year')} {car.get('make')} {car.get('model')} | "
                f"VIN: {car.get('vin')} | цена: {car.get('sale_price', '—')} | "
                f"статус: {car.get('status')}"
            )
        return "\n".join(lines)

    @staticmethod
    async def _vehicle_lookup(text: str) -> dict[str, Any] | None:
        vin_match = re.search(r"\b([A-HJ-NPR-Z0-9]{17})\b", text.upper())
        if vin_match:
            try:
                return await CarEngineV1.get_car_by_vin(OWNER_ID, vin_match.group(1))
            except Exception:
                return None

        cars = await CarEngineV1.list_cars(OWNER_ID, limit=50)
        lowered = text.lower()
        for car in cars:
            haystack = f"{car.get('make', '')} {car.get('model', '')} {car.get('year', '')}".lower()
            if any(token in haystack for token in lowered.split() if len(token) > 2):
                return car
        return None

    @staticmethod
    def format_vehicle(car: dict[str, Any]) -> str:
        return (
            f"🚗 {car.get('year')} {car.get('make')} {car.get('model')}\n"
            f"VIN: {car.get('vin')}\n"
            f"Цвет: {car.get('color') or '—'}\n"
            f"Пробег: {car.get('mileage') or '—'}\n"
            f"Цена: {car.get('sale_price') or '—'}\n"
            f"Статус: {car.get('status')}"
        )

    @staticmethod
    async def _answer_with_ai(
        session,
        messages: list,
        inventory: str,
        car_context: str = "",
    ) -> str:
        history = [
            {"role": m.role if m.role != "assistant" else "assistant", "content": m.content}
            for m in messages[-10:]
            if m.role in {"user", "assistant"}
        ]
        system = (
            f"{SALES_SYSTEM_PROMPT.strip()}\n\n"
            f"Инвентарь:\n{inventory}\n"
        )
        if car_context:
            system += f"\nАвто клиента:\n{car_context}\n"

        return await ask_openrouter(
            history,
            user_memory=system,
            ai_settings={"language": "ru", "tone": "friendly"},
        )

    @staticmethod
    def _parse_financing_numbers(text: str) -> dict[str, Decimal | int] | None:
        numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
        if len(numbers) < 2:
            return None
        try:
            values = [Decimal(n.replace(",", ".")) for n in numbers[:4]]
        except InvalidOperation:
            return None
        result: dict[str, Decimal | int] = {
            "vehicle_price": values[0],
            "down_payment": values[1] if len(values) > 1 else Decimal("0"),
        }
        if len(values) > 2:
            result["annual_rate_percent"] = values[2]
        if len(values) > 3:
            result["term_months"] = int(values[3])
        else:
            result["term_months"] = DEFAULT_TERM_MONTHS
        return result

    @staticmethod
    async def start_session(
        *,
        telegram_user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict[str, Any]:
        lead_result = await LeadAutomationEngineV1.ingest_from_telegram(
            user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        lead_id = uuid.UUID(lead_result["id"]) if lead_result.get("id") else None

        async with get_session() as session:
            repo = SalesAssistantRepository(session)
            sales_session = await repo.get_or_create_session(
                telegram_user_id=telegram_user_id,
                lead_id=lead_id,
            )
            if sales_session.message_count == 0:
                await repo.add_message(
                    session_id=sales_session.id,
                    role="assistant",
                    content=(
                        "Здравствуйте! Я AI Sales Assistant. "
                        "Помогу подобрать авто, рассчитать финансирование, "
                        "записать на встречу или соединить с менеджером."
                    ),
                    intent="greeting",
                )
                await repo.update_session(sales_session, message_count=1)
            await session.refresh(sales_session)
            snapshot = SalesAssistantRepository.session_snapshot(sales_session)
            return snapshot

    @staticmethod
    async def handle_message(
        *,
        telegram_user_id: int,
        text: str,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> str:
        if await AiSalesAssistantEngineV1.is_staff(telegram_user_id):
            raise AiSalesAssistantError("Staff users should not use sales assistant")

        await AiSalesAssistantEngineV1.start_session(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        intent = AiSalesAssistantEngineV1.detect_intent(text)

        async with get_session() as session:
            repo = SalesAssistantRepository(session)
            sales_session = await repo.get_or_create_session(
                telegram_user_id=telegram_user_id,
            )

            if sales_session.status == SalesSessionStatus.TRANSFERRED.value:
                return (
                    "Ваш запрос уже передан менеджеру. "
                    "Ожидайте связи или напишите «менеджер» для повторного запроса."
                )

            await repo.add_message(
                session_id=sales_session.id,
                role="user",
                content=text,
                intent=intent,
            )
            await repo.update_session(
                sales_session,
                message_count=sales_session.message_count + 1,
                last_intent=intent,
            )

            if sales_session.status == SalesSessionStatus.COLLECTING_CONTACT.value:
                reply = await AiSalesAssistantEngineV1._handle_contact_step(
                    repo, sales_session, text,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
            elif sales_session.status == SalesSessionStatus.SCHEDULING_MEETING.value:
                reply = await AiSalesAssistantEngineV1._handle_schedule_step(
                    repo, sales_session, text,
                )
            elif intent == "manager":
                reply = await AiSalesAssistantEngineV1._transfer_to_manager(
                    repo, sales_session, text,
                )
            elif intent == "financing":
                reply = await AiSalesAssistantEngineV1._handle_financing(
                    repo, sales_session, text,
                )
            elif intent == "vehicle":
                reply = await AiSalesAssistantEngineV1._handle_vehicle(
                    repo, sales_session, text,
                )
            elif intent == "contact":
                reply = await AiSalesAssistantEngineV1._start_contact_collection(
                    repo, sales_session,
                )
            elif intent == "schedule":
                reply = await AiSalesAssistantEngineV1._start_scheduling(
                    repo, sales_session,
                )
            else:
                inventory = await AiSalesAssistantEngineV1._inventory_context()
                car = None
                if sales_session.car_id:
                    car_obj = await CarRepository(session).get_car(sales_session.car_id)
                    if car_obj is not None:
                        car = CarEngineV1._car_snapshot(car_obj)
                if car is None:
                    car = await AiSalesAssistantEngineV1._vehicle_lookup(text)
                    if car and car.get("id"):
                        await repo.update_session(
                            sales_session,
                            car_id=uuid.UUID(car["id"]),
                        )
                car_context = AiSalesAssistantEngineV1.format_vehicle(car) if car else ""
                messages = await repo.list_messages(sales_session.id)
                reply = await AiSalesAssistantEngineV1._answer_with_ai(
                    sales_session,
                    messages,
                    inventory,
                    car_context,
                )

            await repo.add_message(
                session_id=sales_session.id,
                role="assistant",
                content=reply,
                intent=intent,
            )
            await repo.update_session(
                sales_session,
                message_count=sales_session.message_count + 1,
            )
            return reply

    @staticmethod
    async def _handle_vehicle(repo, sales_session, text: str) -> str:
        car = await AiSalesAssistantEngineV1._vehicle_lookup(text)
        if car is None:
            inventory = await AiSalesAssistantEngineV1._inventory_context()
            return (
                "Не нашёл конкретное авто по запросу. Вот что сейчас доступно:\n\n"
                f"{inventory}\n\n"
                "Уточните VIN, марку или модель."
            )
        if car.get("id"):
            await repo.update_session(sales_session, car_id=uuid.UUID(car["id"]))
        return AiSalesAssistantEngineV1.format_vehicle(car)

    @staticmethod
    async def _handle_financing(repo, sales_session, text: str) -> str:
        params = AiSalesAssistantEngineV1._parse_financing_numbers(text)
        car_price = None
        if sales_session.car_id:
            async with get_session() as session:
                car = await CarRepository(session).get_car(sales_session.car_id)
                if car and car.sale_price:
                    car_price = car.sale_price

        if params is None:
            await repo.update_session(
                sales_session,
                status=SalesSessionStatus.ACTIVE.value,
                financing_data={"awaiting_input": True},
            )
            hint = ""
            if car_price:
                hint = f"\n\nЦена выбранного авто: {car_price}"
            return (
                "Для расчёта финансирования отправьте через пробел:\n"
                "цена взнос [ставка%] [срок мес.]\n"
                "Пример: 15000 3000 12 36" + hint
            )

        if car_price and params.get("vehicle_price", 0) <= 0:
            params["vehicle_price"] = Decimal(str(car_price))

        financing = AiSalesAssistantEngineV1.calculate_financing(
            vehicle_price=params["vehicle_price"],
            down_payment=params.get("down_payment", 0),
            annual_rate_percent=params.get("annual_rate_percent", DEFAULT_ANNUAL_RATE),
            term_months=int(params.get("term_months", DEFAULT_TERM_MONTHS)),
        )
        await repo.update_session(
            sales_session,
            financing_data=financing,
        )
        return AiSalesAssistantEngineV1.format_financing(financing)

    @staticmethod
    async def _start_contact_collection(repo, sales_session) -> str:
        contact = dict(sales_session.contact_data or {})
        contact["step"] = "name"
        await repo.update_session(
            sales_session,
            status=SalesSessionStatus.COLLECTING_CONTACT.value,
            contact_data=contact,
        )
        return "Отлично! Как к вам обращаться? Напишите имя."

    @staticmethod
    async def _handle_contact_step(
        repo,
        sales_session,
        text: str,
        *,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> str:
        contact = dict(sales_session.contact_data or {})
        step = contact.get("step", "name")

        if step == "name":
            contact["name"] = text.strip()
            contact["step"] = "phone"
            await repo.update_session(sales_session, contact_data=contact)
            return "Спасибо! Укажите номер телефона."

        if step == "phone":
            contact["phone"] = text.strip()
            contact["step"] = "email"
            await repo.update_session(sales_session, contact_data=contact)
            return "Почта (email) или «-» чтобы пропустить."

        if step == "email":
            email = None if text.strip() == "-" else text.strip()
            contact["email"] = email
            contact["step"] = "done"
            await repo.update_session(
                sales_session,
                status=SalesSessionStatus.ACTIVE.value,
                contact_data=contact,
            )

            lead = await LeadAutomationEngineV1.ingest_lead(
                source="telegram",
                customer_name=contact.get("name") or first_name or f"User {sales_session.telegram_user_id}",
                phone=contact.get("phone"),
                email=email,
                telegram_user_id=sales_session.telegram_user_id,
                car_id=sales_session.car_id,
                source_metadata={"username": username, "via": "ai_sales_assistant"},
            )
            if lead.get("id"):
                await repo.update_session(
                    sales_session,
                    lead_id=uuid.UUID(lead["id"]),
                )
            return (
                "✅ Контактные данные сохранены. "
                "Менеджер свяжется с вами. "
                "Могу также записать на встречу — напишите «записаться»."
            )

        return "Продолжим сбор контактов. Напишите имя."

    @staticmethod
    async def _start_scheduling(repo, sales_session) -> str:
        scheduling = {"step": "datetime"}
        await repo.update_session(
            sales_session,
            status=SalesSessionStatus.SCHEDULING_MEETING.value,
            scheduling_data=scheduling,
        )
        return (
            "Запишу вас на встречу. "
            "Укажите дату и время в формате:\n"
            "ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Пример: 25.07.2026 14:30"
        )

    @staticmethod
    async def _handle_schedule_step(repo, sales_session, text: str) -> str:
        scheduling = dict(sales_session.scheduling_data or {})
        step = scheduling.get("step", "datetime")

        if step == "datetime":
            try:
                scheduled_at = datetime.strptime(text.strip(), "%d.%m.%Y %H:%M")
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            except ValueError:
                return "Не удалось разобрать дату. Формат: ДД.ММ.ГГГГ ЧЧ:ММ"

            scheduling["scheduled_at"] = scheduled_at.isoformat()
            scheduling["step"] = "notes"
            await repo.update_session(sales_session, scheduling_data=scheduling)
            return "Комментарий к встрече или «-» чтобы пропустить."

        if step == "notes":
            notes = None if text.strip() == "-" else text.strip()
            scheduled_at = datetime.fromisoformat(scheduling["scheduled_at"])
            contact = sales_session.contact_data or {}
            title = f"Встреча с клиентом {contact.get('name', sales_session.telegram_user_id)}"

            event_id = CalendarService.create_event(
                creator_id=sales_session.telegram_user_id,
                title=title,
                start_time=scheduled_at.strftime("%Y-%m-%d %H:%M:%S"),
                description=notes or "AI Sales Assistant meeting",
                module="ai_sales_assistant",
                event_type="sales_meeting",
                owner_id=MANAGER_ID,
                assigned_user_id=MANAGER_ID,
            )

            meeting = await repo.create_meeting(
                session_id=sales_session.id,
                scheduled_at=scheduled_at,
                title=title,
                notes=notes,
                calendar_event_id=event_id,
            )

            await repo.update_session(
                sales_session,
                status=SalesSessionStatus.ACTIVE.value,
                scheduling_data={"meeting_id": str(meeting.id), "step": "done"},
            )
            return (
                f"✅ Встреча запланирована на {scheduled_at.strftime('%d.%m.%Y %H:%M')}.\n"
                "Менеджер получит уведомление."
            )

        return "Укажите дату и время встречи."

    @staticmethod
    async def _transfer_to_manager(repo, sales_session, reason: str) -> str:
        manager_id = sales_session.assigned_manager_id or MANAGER_ID
        await repo.create_handoff(
            session_id=sales_session.id,
            manager_id=manager_id,
            reason=reason,
        )
        await repo.update_session(
            sales_session,
            status=SalesSessionStatus.TRANSFERRED.value,
            assigned_manager_id=manager_id,
        )

        if sales_session.lead_id is None:
            await LeadAutomationEngineV1.ingest_from_telegram(
                user_id=sales_session.telegram_user_id,
                username=None,
                first_name=None,
                last_name=None,
                metadata={"handoff_reason": reason},
            )

        await AiSalesAssistantEngineV1._notify_manager(
            manager_id=manager_id,
            telegram_user_id=sales_session.telegram_user_id,
            reason=reason,
            session_id=sales_session.id,
        )
        manager_name = MANAGERS.get(manager_id, str(manager_id))
        return (
            f"Передал ваш запрос менеджеру ({manager_name}). "
            "Ожидайте связи в ближайшее время."
        )

    @staticmethod
    async def _notify_manager(
        *,
        manager_id: int,
        telegram_user_id: int,
        reason: str,
        session_id: uuid.UUID,
    ) -> None:
        if not BOT_TOKEN:
            return
        bot = Bot(token=BOT_TOKEN)
        try:
            await bot.send_message(
                chat_id=manager_id,
                text=(
                    "🔔 AI Sales Assistant — передача клиента\n\n"
                    f"Клиент: {telegram_user_id}\n"
                    f"Сессия: {session_id}\n"
                    f"Причина: {reason[:500]}"
                ),
            )
        except Exception:
            logger.exception("Failed to notify manager %s", manager_id)
        finally:
            await bot.session.close()

    @staticmethod
    async def get_session(actor_id: int, session_id: uuid.UUID) -> dict[str, Any]:
        if not await AiSalesAssistantEngineV1.is_staff(actor_id):
            raise AiSalesAssistantError("Access denied")

        async with get_session() as session:
            sales_session = await SalesAssistantRepository(session).get_session(session_id)
            if sales_session is None:
                raise AiSalesAssistantError(f"Session not found: {session_id}")
            await session.refresh(sales_session)
            return SalesAssistantRepository.session_snapshot(sales_session)
