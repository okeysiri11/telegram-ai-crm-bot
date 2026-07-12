# Event Bus bridge — wires platform modules to EventBus subscribers.
# Modules should publish events; side effects happen here (not direct cross-calls).

from events import EventBus, PlatformEvent


def register_default_subscribers() -> None:
    """Register all default event handlers (idempotent)."""
    handlers = [
        ("AGRO_REQUEST_CREATED", _on_agro_request_created, "agro_lifecycle"),
        ("AGRO_REQUEST_CREATED", _on_agro_request_workflow, "agro_workflow_engine"),
        ("AGRO_REQUEST_CREATED", _on_agro_request_notify, "agro_notify"),
        ("AGRO_REQUEST_CREATED", _on_agro_erp_request_created, "agro_erp_workflow"),
        ("AGRO_REQUEST_ASSIGNED", _on_agro_request_assigned, "agro_assigned"),
        ("AGRO_REQUEST_ASSIGNED", _on_agro_erp_taken, "agro_erp_taken"),
        ("AGRO_REQUEST_STATUS_CHANGED", _on_agro_status_changed, "agro_status"),
        ("FINANCE_PAYMENT_CONFIRMED", _on_finance_payment_confirmed, "finance_audit"),
        ("FINANCE_COMMISSION_PAID", _on_finance_commission_paid, "finance_commission"),
        ("TASK_CREATED", _on_task_created, "task_workflow"),
        ("CALENDAR_EVENT_CREATED", _on_calendar_event_created, "calendar_workflow"),
        ("USER_CREATED", _on_user_created, "user_workflow"),
        ("AUTO_LEAD_CREATED", _on_auto_lead_created, "auto_stub"),
        ("AUTO_PAYMENT_RECEIVED", _on_auto_payment_received, "auto_payment_stub"),
        ("AUTO_TRADEIN_STARTED", _on_auto_tradein_started, "auto_tradein_stub"),
        ("LEGAL_CASE_CREATED", _on_legal_case_created, "legal_stub"),
        ("DRONE_PROJECT_CREATED", _on_drone_project_created, "drone_stub"),
        ("DEAL_CREATED", _on_deal_created, "deal_workflow"),
        ("DEAL_STATUS_CHANGED", _on_deal_status_changed, "deal_workflow"),
        ("DEAL_COMPLETED", _on_deal_completed, "deal_workflow"),
    ]
    for event_type, handler, sid in handlers:
        EventBus.subscribe(event_type, handler, subscriber_id=sid)


# ---------------------------------------------------------------------------
# Agro
# ---------------------------------------------------------------------------

def _on_agro_request_created(event: PlatformEvent) -> None:
    from services.workflow_triggers import WorkflowTriggers
    rn = event.entity_id
    product = event.payload.get("product")
    WorkflowTriggers.on_request_created(
        event.user_id, rn, module="agro_trading", product=product,
    )


def _on_agro_request_workflow(event: PlatformEvent) -> None:
    from services.workflow_engine import WorkflowEngine
    rn = event.entity_id
    WorkflowEngine.execute_workflow(
        "AGRO_REQUEST_CREATED",
        event.user_id,
        "agro_trading",
        entity_type="request",
        entity_id=rn,
        payload={
            "title": event.payload.get("title") or f"Новая заявка #{rn}",
            "product": event.payload.get("product"),
        },
    )


def _on_agro_request_notify(event: PlatformEvent) -> None:
    from database import notify_agro_managers_new_request
    notify_agro_managers_new_request(
        event.entity_id,
        product=event.payload.get("product"),
        client_name=event.payload.get("client_name"),
    )


def _on_agro_erp_request_created(event: PlatformEvent) -> None:
    from services.agro_erp_workflow import AgroErpWorkflow
    rn = event.entity_id
    AgroErpWorkflow.emit(
        "REQUEST_CREATED",
        event.user_id,
        entity_type="request",
        entity_id=rn,
        payload={
            "title": event.payload.get("title") or f"Заявка #{rn} создана",
            "message": event.payload.get("message", ""),
            "priority": event.payload.get("priority", "HIGH"),
        },
    )


def _on_agro_request_assigned(event: PlatformEvent) -> None:
    from services.workflow_triggers import WorkflowTriggers
    from services.agro_request_workflow import AgroRequestWorkflow
    rn = event.entity_id
    manager_id = event.payload.get("manager_id", event.user_id)
    WorkflowTriggers.on_manager_assigned(
        manager_id, rn, manager_id, module="agro_trading",
    )
    AgroRequestWorkflow.on_request_assigned(manager_id, rn, manager_id)


def _on_agro_erp_taken(event: PlatformEvent) -> None:
    from services.agro_erp import AgroErpService
    from database import sync_universal_deal_from_agro
    rn = event.entity_id
    manager_id = event.payload.get("manager_id", event.user_id)
    deal_id = AgroErpService.on_request_taken(manager_id, rn, manager_id)
    if deal_id:
        sync_universal_deal_from_agro(deal_id, manager_id)


def _on_agro_status_changed(event: PlatformEvent) -> None:
    from services.workflow_triggers import WorkflowTriggers
    from services.agro_request_workflow import AgroRequestWorkflow
    from services.agro_erp import AgroErpService
    rn = event.entity_id
    old_status = event.payload.get("old_status")
    new_status = event.payload.get("new_status")
    WorkflowTriggers.on_request_status_changed(
        event.user_id, rn, old_status, new_status, module="agro_trading",
    )
    if new_status == "DONE":
        AgroRequestWorkflow.on_request_done(event.user_id, rn)
    elif new_status == "CANCELLED":
        AgroRequestWorkflow.on_request_cancelled(event.user_id, rn)
    AgroErpService.on_request_status_changed(event.user_id, rn, new_status)


# ---------------------------------------------------------------------------
# Finance
# ---------------------------------------------------------------------------

def _on_finance_payment_confirmed(event: PlatformEvent) -> None:
    from services.timeline import TimelineService
    TimelineService.record(
        "FINANCE_TRANSACTION",
        event.entity_id,
        "FINANCE_PAYMENT_CONFIRMED",
        event.user_id,
        description=event.payload.get("notes", "Payment confirmed"),
    )


def _on_finance_commission_paid(event: PlatformEvent) -> None:
    from services.timeline import TimelineService
    TimelineService.record(
        "FINANCE_TRANSACTION",
        event.entity_id,
        "FINANCE_COMMISSION_PAID",
        event.user_id,
        description=event.payload.get("notes", "Commission paid"),
    )


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------

def _on_task_created(event: PlatformEvent) -> None:
    from services.workflow_triggers import WorkflowTriggers
    from services.workflow_engine import WorkflowEngine
    task_id = event.entity_id
    WorkflowTriggers.on_task_created(
        event.user_id,
        task_id,
        task_type=event.payload.get("task_type", "SYSTEM"),
        title=event.payload.get("title", ""),
        module=event.module,
    )
    WorkflowEngine.execute_workflow(
        "TASK_CREATED",
        event.user_id,
        event.module,
        entity_type="task",
        entity_id=task_id,
        payload={"title": event.payload.get("title", "")},
    )


def _on_calendar_event_created(event: PlatformEvent) -> None:
    from services.workflow_triggers import WorkflowTriggers
    from services.workflow_engine import WorkflowEngine
    event_id = event.entity_id
    title = event.payload.get("title", "")
    WorkflowTriggers.on_calendar_event_created(
        event.user_id, event_id, title, module=event.module,
    )
    WorkflowEngine.execute_workflow(
        "EVENT_CREATED",
        event.user_id,
        event.module,
        entity_type="event",
        entity_id=event_id,
        payload={"title": title},
    )


def _on_user_created(event: PlatformEvent) -> None:
    from services.workflow_engine import WorkflowEngine
    WorkflowEngine.execute_workflow(
        "USER_CREATED",
        event.user_id,
        "users",
        entity_type="user",
        entity_id=event.user_id,
        payload=event.payload,
    )


# ---------------------------------------------------------------------------
# Future vertical stubs (log-only until modules are built)
# ---------------------------------------------------------------------------

def _on_auto_lead_created(event: PlatformEvent) -> None:
    from database import log_audit
    log_audit(
        event.user_id, "auto_lead_created", "automotive",
        f"lead={event.entity_id}",
    )


def _on_auto_payment_received(event: PlatformEvent) -> None:
    from database import log_audit
    log_audit(
        event.user_id, "auto_payment_received", "automotive",
        f"payment={event.entity_id}|amount={event.payload.get('amount')}",
    )


def _on_auto_tradein_started(event: PlatformEvent) -> None:
    from database import log_audit
    log_audit(
        event.user_id, "auto_tradein_started", "automotive",
        f"tradein={event.entity_id}",
    )


def _on_legal_case_created(event: PlatformEvent) -> None:
    from database import log_audit
    log_audit(
        event.user_id, "legal_case_created", "law",
        f"case={event.entity_id}",
    )


def _on_drone_project_created(event: PlatformEvent) -> None:
    from database import log_audit
    log_audit(
        event.user_id, "drone_project_created", "drone",
        f"project={event.entity_id}",
    )


def _on_deal_created(event: PlatformEvent) -> None:
    from services.deal_workflow import DealWorkflowEngine
    module = event.payload.get("module", "AGRO")
    DealWorkflowEngine.on_created(
        event.entity_id, event.user_id, module, event.payload,
    )


def _on_deal_status_changed(event: PlatformEvent) -> None:
    from services.deal_workflow import DealWorkflowEngine
    module = event.payload.get("module", "AGRO")
    DealWorkflowEngine.on_status_changed(
        event.entity_id,
        event.user_id,
        module,
        event.payload.get("old_status", ""),
        event.payload.get("new_status", ""),
    )


def _on_deal_completed(event: PlatformEvent) -> None:
    from services.deal_workflow import DealWorkflowEngine
    module = event.payload.get("module", "AGRO")
    DealWorkflowEngine.on_completed(
        event.entity_id, event.user_id, module, event.payload,
    )
