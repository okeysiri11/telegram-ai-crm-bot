"""Workflow models and constants — Sprint 19.5."""

from __future__ import annotations

BLOCK_TYPES = (
    "start",
    "decision",
    "delay",
    "approval",
    "ai_decision",
    "notification",
    "api_call",
    "database_update",
    "finish",
)

TRIGGERS = (
    "lead_created",
    "status_changed",
    "message_received",
    "payment_received",
    "document_changed",
    "schedule",
    "webhook",
    "api",
    "ai_agent",
)

CONDITION_TYPES = (
    "user",
    "role",
    "date",
    "time",
    "field",
    "status",
    "project",
    "module",
    "ai_decision",
    "expression",
)

ACTION_TYPES = (
    "email",
    "telegram",
    "push",
    "create_task",
    "change_status",
    "assign",
    "ai_agent",
    "sql",
    "api",
    "python",
    "custom",
    "webhook",
    "crm",
    "approval",
)

APPROVAL_MODES = (
    "single",
    "multi",
    "sequential",
    "parallel",
    "ai",
    "auto",
)

TEMPLATE_KINDS = (
    "crm_lead_processing",
    "invoice_approval",
    "purchase_request",
    "employee_onboarding",
    "contract_approval",
    "ai_task_processing",
    "customer_support",
    "equipment_maintenance",
)

SCHEDULE_KINDS = ("cron", "interval", "once", "recurring", "delayed", "calendar")
