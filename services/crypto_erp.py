# Crypto OTC ERP Phase 1 — deal lifecycle orchestration.

class CryptoErpService:
    MODULE = "crypto_otc"
    LARGE_DEAL_THRESHOLD = 50000

    @staticmethod
    def on_deal_created(actor_id: int, deal_id: int, request_number: int = None) -> None:
        from database import get_crypto_deal, log_audit
        from services.crypto_erp_calendar import CryptoErpCalendar
        from services.crypto_erp_workflow import CryptoErpWorkflow

        deal = get_crypto_deal(deal_id)
        if not deal:
            return
        CryptoErpCalendar.on_deal_created(deal_id, actor_id)
        CryptoErpWorkflow.emit(
            "DEAL_CREATED",
            actor_id,
            entity_type="crypto_deal",
            entity_id=deal_id,
            payload={
                "title": f"Crypto сделка #{deal_id} создана",
                "message": f"Запрос #{request_number or deal[2]} · {deal[3]}",
                "priority": "HIGH",
            },
        )
        log_audit(actor_id, "crypto_deal_created", CryptoErpService.MODULE, str(deal_id))

    @staticmethod
    def on_payment_received(actor_id: int, deal_id: int, payment_id: int) -> None:
        from services.crypto_erp_workflow import CryptoErpWorkflow

        CryptoErpWorkflow.emit(
            "PAYMENT_RECEIVED",
            actor_id,
            entity_type="crypto_payment",
            entity_id=payment_id,
            payload={
                "title": f"Оплата по сделке #{deal_id}",
                "message": f"Payment #{payment_id}",
                "deal_id": deal_id,
            },
        )

    @staticmethod
    def on_delivery_completed(actor_id: int, deal_id: int) -> None:
        from services.crypto_erp_calendar import CryptoErpCalendar
        from services.crypto_erp_workflow import CryptoErpWorkflow

        deal = __import__("database").get_crypto_deal(deal_id)
        direction = deal[3] if deal else ""
        if "CASH" in (direction or ""):
            CryptoErpCalendar.create_deal_event(deal_id, "cash_delivery", actor_id)
        if "USDT" in (direction or ""):
            CryptoErpCalendar.create_deal_event(deal_id, "usdt_receipt", actor_id)
        CryptoErpWorkflow.emit(
            "DELIVERY_COMPLETED",
            actor_id,
            entity_type="crypto_deal",
            entity_id=deal_id,
            payload={"title": f"Выдача по сделке #{deal_id} завершена"},
        )

    @staticmethod
    def on_deal_closed(actor_id: int, deal_id: int) -> None:
        from services.crypto_erp_calendar import CryptoErpCalendar
        from services.crypto_erp_workflow import CryptoErpWorkflow

        CryptoErpCalendar.create_deal_event(
            deal_id, "client_meeting", actor_id,
            title=f"Закрытие сделки #{deal_id}",
        )
        CryptoErpWorkflow.emit(
            "DEAL_CLOSED",
            actor_id,
            entity_type="crypto_deal",
            entity_id=deal_id,
            payload={"title": f"Crypto сделка #{deal_id} закрыта"},
        )
