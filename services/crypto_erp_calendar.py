# Crypto OTC ERP — calendar events linked to deals.

from datetime import datetime


class CryptoErpCalendar:
    MODULE = "crypto_otc"

    EVENT_LABELS = {
        "client_meeting": "Встреча с клиентом",
        "cash_delivery": "Выдача наличных",
        "usdt_receipt": "Получение USDT",
        "large_deal": "Крупная сделка",
    }

    @staticmethod
    def create_deal_event(
        deal_id: int,
        event_type: str,
        user_id: int,
        title: str = None,
        start_time: str = None,
    ) -> int:
        from database import get_crypto_deal, link_crypto_deal_calendar
        from services.calendar_service import CalendarService

        deal = get_crypto_deal(deal_id)
        if not deal:
            return 0

        amount = deal[5] or 0
        label = CryptoErpCalendar.EVENT_LABELS.get(event_type, event_type)
        event_title = title or f"{label} · сделка #{deal_id}"
        start_time = start_time or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        owner = deal[9] or deal[1] or user_id

        event_id = CalendarService.create_event(
            creator_id=user_id,
            title=f"[Crypto OTC] {event_title}",
            start_time=start_time,
            description=f"crypto_erp:{event_type}|deal:{deal_id}|amount:{amount}",
            module=CryptoErpCalendar.MODULE,
            event_type=event_type,
            owner_id=owner,
        )
        if event_id:
            link_crypto_deal_calendar(deal_id, event_id, event_type)
        return event_id

    @staticmethod
    def on_deal_created(deal_id: int, user_id: int) -> None:
        from database import get_crypto_deal

        deal = get_crypto_deal(deal_id)
        if not deal:
            return
        direction = deal[3] or ""
        amount = deal[5] or 0
        CryptoErpCalendar.create_deal_event(deal_id, "client_meeting", user_id)
        if amount >= 50000:
            CryptoErpCalendar.create_deal_event(deal_id, "large_deal", user_id)
        if "CASH" in direction:
            CryptoErpCalendar.create_deal_event(deal_id, "cash_delivery", user_id)
        if "USDT" in direction:
            CryptoErpCalendar.create_deal_event(deal_id, "usdt_receipt", user_id)
