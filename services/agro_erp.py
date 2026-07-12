# Agro ERP — deal entity, auto-activation, Phase 2 calendar/workflow/finance.

from datetime import datetime


class AgroErpService:
    MODULE = "agro_trading"
    ERP_STATUS_NEGOTIATION = "NEGOTIATION"

    @staticmethod
    def on_request_taken(
        actor_id: int,
        request_number: int,
        manager_id: int,
    ) -> int:
        """
        REQUEST_CREATED → REQUEST_TAKEN → auto ERP deal (status NEGOTIATION).
        Does not replace AgroDealLifecycle — runs additively after manager assign.
        """
        from database import (
            get_request_by_number,
            get_agro_deal_by_request,
            activate_agro_erp_deal,
            link_request_to_deal,
            get_agro_finance_by_deal,
            create_agro_finance,
            log_audit,
        )
        from services.agro_erp_calendar import AgroErpCalendar
        from services.agro_erp_workflow import AgroErpWorkflow

        request = get_request_by_number(request_number)
        if not request:
            return 0

        client_id = request[2]
        product = request[4]
        deal_id = activate_agro_erp_deal(
            request_number=request_number,
            buyer_id=client_id,
            manager_id=manager_id,
            product=product,
            erp_status=AgroErpService.ERP_STATUS_NEGOTIATION,
        )
        if deal_id:
            link_request_to_deal(request_number, deal_id)
            AgroErpCalendar.create_deal_event(deal_id, "deal_created", manager_id)
            if not get_agro_finance_by_deal(deal_id):
                price = None
                deal = get_agro_deal_by_request(request_number)
                if deal and deal[21]:
                    price = deal[21]
                create_agro_finance(
                    created_by=manager_id,
                    request_number=request_number,
                    deal_id=deal_id,
                    amount=price,
                    currency=deal[22] if deal else "USD",
                )

        AgroErpWorkflow.emit(
            "REQUEST_TAKEN",
            manager_id,
            entity_type="request",
            entity_id=request_number,
            payload={
                "title": f"Заявка #{request_number} взята",
                "message": f"Менеджер {manager_id}",
                "priority": "HIGH",
            },
        )
        if deal_id:
            AgroErpWorkflow.emit(
                "DEAL_CREATED",
                manager_id,
                entity_type="deal",
                entity_id=deal_id,
                payload={
                    "title": f"ERP сделка #{deal_id} создана",
                    "message": f"Статус NEGOTIATION · заявка #{request_number}",
                    "deal_id": deal_id,
                    "priority": "HIGH",
                },
            )

        log_audit(
            actor_id,
            "agro_erp_deal_activated",
            AgroErpService.MODULE,
            f"request:{request_number}:deal:{deal_id}:NEGOTIATION",
        )
        return deal_id

    @staticmethod
    def on_request_status_changed(
        actor_id: int,
        request_number: int,
        new_status: str,
    ) -> None:
        """Map terminal CRM statuses to ERP deal statuses when applicable."""
        from database import (
            get_agro_deal_by_request,
            update_agro_deal_erp,
            _agro_erp_post_deal_completed,
            log_audit,
        )
        from services.statuses import normalize_status

        deal = get_agro_deal_by_request(request_number)
        if not deal:
            return

        status = normalize_status(new_status)
        erp_map = {
            "DONE": "COMPLETED",
            "CANCELLED": "CANCELLED",
        }
        erp_status = erp_map.get(status)
        if not erp_status:
            return

        update_agro_deal_erp(
            request_number,
            erp_status=erp_status,
            closed_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") if erp_status == "COMPLETED" else None,
        )
        if erp_status == "COMPLETED":
            _agro_erp_post_deal_completed(deal[0], actor_id, request_number)
        log_audit(
            actor_id,
            "agro_erp_status",
            AgroErpService.MODULE,
            f"request:{request_number}:erp:{erp_status}",
        )

    @staticmethod
    def attach_document(
        deal_id: int,
        document_type: str,
        uploaded_by: int,
        file_id: int = None,
        title: str = None,
        comment: str = None,
    ) -> int:
        """Deal → Document → File Storage."""
        from database import attach_agro_document_to_deal

        return attach_agro_document_to_deal(
            deal_id=deal_id,
            document_type=document_type,
            uploaded_by=uploaded_by,
            file_id=file_id,
            title=title,
            comment=comment,
        )
