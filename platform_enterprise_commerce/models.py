"""Enterprise Commerce constants — Sprint 22.7."""

from __future__ import annotations

PAYMENT_METHODS = (
    "cash",
    "card",
    "online",
    "apple_pay",
    "google_pay",
    "bank_transfer",
    "certificate",
    "membership",
    "bonus",
)

PAYMENT_MODES = ("full", "partial", "prepay", "postpay")

LINE_KINDS = ("service", "product", "combo")

LOYALTY_LEVELS = ("new", "bronze", "silver", "gold", "platinum")

PAYMENT_PROVIDERS = (
    "terminal",
    "online_checkout",
    "apple_pay",
    "google_pay",
    "bank_transfer",
)

INDUSTRIES = (
    "beauty",
    "cafe",
    "retail",
    "medical",
    "construction",
    "manufacturing",
    "generic",
)

KPI_TARGETS = {
    "sale_under_20s": True,
    "mixed_payments": True,
    "auto_material_deduction": True,
    "certificates_memberships": True,
    "unified_finance_history": True,
}

INTEGRATION_TARGETS = (
    "beauty_os",
    "enterprise_crm",
    "enterprise_finance",
    "warehouse",
    "ai_business_advisor",
    "ai_marketing_os",
    "communications_hub",
    "product_intelligence",
)

PRINCIPLES = (
    "universal_commerce_engine",
    "industry_agnostic_api",
    "reuse_finance_warehouse_crm",
    "ai_advises_never_acts",
    "no_duplicated_business_logic",
    "provider_pluggable_payments",
)
