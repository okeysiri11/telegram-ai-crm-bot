# Agro ERP Phase 2 — calendar events linked to deals (additive).

from datetime import datetime


class AgroErpCalendar:
    MODULE = "agro_trading"

    EVENT_LABELS = {
        "deal_created": "Создание сделки",
        "contract_signed": "Подписание контракта",
        "loading": "Погрузка",
        "vessel_arrival": "Прибытие судна",
        "payment": "Оплата",
        "deal_closed": "Закрытие сделки",
    }

    @staticmethod
    def create_deal_event(
        deal_id: int,
        event_type: str,
        user_id: int,
        title: str = None,
        start_time: str = None,
    ) -> int:
        from database import (
            get_agro_deal_by_id,
            link_agro_deal_calendar,
        )
        from services.calendar_service import CalendarService

        deal = get_agro_deal_by_id(deal_id)
        if not deal:
            return 0

        request_number = deal[1]
        label = AgroErpCalendar.EVENT_LABELS.get(event_type, event_type)
        event_title = title or f"{label} · сделка #{deal_id} · заявка #{request_number}"
        start_time = start_time or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        owner = deal[5] or user_id

        event_id = CalendarService.create_event(
            creator_id=user_id,
            title=f"[Agro ERP] {event_title}",
            start_time=start_time,
            description=f"agro_erp:{event_type}|deal:{deal_id}|request:{request_number}",
            module=AgroErpCalendar.MODULE,
            event_type=event_type,
            owner_id=owner,
        )
        if event_id:
            link_agro_deal_calendar(deal_id, event_id, event_type)
        return event_id
