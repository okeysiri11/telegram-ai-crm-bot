# Sprint 9.7 — Finance, billing, contracts, commercial models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class FeeType(str, enum.Enum):
    PORT = "port_fees"
    TERMINAL = "terminal_fees"
    STORAGE = "storage_fees"
    CONTAINER = "container_fees"
    BERTH = "berth_fees"
    HANDLING = "handling_fees"
    DEMURRAGE = "demurrage"
    DETENTION = "detention"
    INSPECTION = "inspection"
    CUSTOM = "custom_services"


class ContractPartyType(str, enum.Enum):
    SHIPPING_LINE = "shipping_line"
    FREIGHT_FORWARDER = "freight_forwarder"
    CUSTOMER = "customer"
    IMPORTER = "importer"
    EXPORTER = "exporter"
    CARRIER = "carrier"
    GOVERNMENT = "government_agency"
    INSURANCE = "insurance"
    BANK = "bank"


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    CREDITED = "credited"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"


class PricingMode(str, enum.Enum):
    STANDARD = "standard"
    DYNAMIC = "dynamic"
    SEASONAL = "seasonal"
    VOLUME_DISCOUNT = "volume_discount"
    PRIORITY = "priority_handling"
    EMERGENCY = "emergency"


class AccountEntryType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"


@dataclass
class CommercialTariff:
    tariff_id: str = field(default_factory=_id)
    name: str = ""
    fee_type: FeeType = FeeType.PORT
    unit: str = "unit"
    rate: float = 0.0
    currency: str = "USD"
    pricing_mode: PricingMode = PricingMode.STANDARD
    min_qty: float = 0.0
    discount_pct: float = 0.0
    company_id: str = ""
    terminal_id: str = ""
    is_active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tariff_id": self.tariff_id,
            "name": self.name,
            "fee_type": self.fee_type.value,
            "unit": self.unit,
            "rate": self.rate,
            "currency": self.currency,
            "pricing_mode": self.pricing_mode.value,
            "min_qty": self.min_qty,
            "discount_pct": self.discount_pct,
            "company_id": self.company_id,
            "terminal_id": self.terminal_id,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class CommercialContract:
    contract_id: str = field(default_factory=_id)
    title: str = ""
    party_type: ContractPartyType = ContractPartyType.CUSTOMER
    party_id: str = ""
    party_name: str = ""
    status: ContractStatus = ContractStatus.DRAFT
    currency: str = "USD"
    value: float = 0.0
    valid_from: float = 0.0
    valid_to: float = 0.0
    terms: str = ""
    company_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "title": self.title,
            "party_type": self.party_type.value,
            "party_id": self.party_id,
            "party_name": self.party_name,
            "status": self.status.value,
            "currency": self.currency,
            "value": self.value,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "terms": self.terms,
            "company_id": self.company_id,
            "created_at": self.created_at,
        }


@dataclass
class ChargeLine:
    line_id: str = field(default_factory=_id)
    fee_type: FeeType = FeeType.PORT
    description: str = ""
    quantity: float = 1.0
    unit_rate: float = 0.0
    amount: float = 0.0
    tariff_id: str = ""
    tax_amount: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "line_id": self.line_id,
            "fee_type": self.fee_type.value,
            "description": self.description,
            "quantity": self.quantity,
            "unit_rate": self.unit_rate,
            "amount": self.amount,
            "tariff_id": self.tariff_id,
            "tax_amount": self.tax_amount,
        }


@dataclass
class CommercialInvoice:
    invoice_id: str = field(default_factory=_id)
    customer_id: str = ""
    contract_id: str = ""
    company_id: str = ""
    currency: str = "USD"
    status: InvoiceStatus = InvoiceStatus.DRAFT
    lines: list[ChargeLine] = field(default_factory=list)
    subtotal: float = 0.0
    tax_total: float = 0.0
    total: float = 0.0
    amount_paid: float = 0.0
    description: str = ""
    issued_at: float = 0.0
    due_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "contract_id": self.contract_id,
            "company_id": self.company_id,
            "currency": self.currency,
            "status": self.status.value,
            "lines": [line.to_dict() for line in self.lines],
            "subtotal": self.subtotal,
            "tax_total": self.tax_total,
            "total": self.total,
            "amount_paid": self.amount_paid,
            "outstanding": round(self.total - self.amount_paid, 2),
            "description": self.description,
            "issued_at": self.issued_at,
            "due_at": self.due_at,
            "created_at": self.created_at,
        }


@dataclass
class CreditNote:
    note_id: str = field(default_factory=_id)
    invoice_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    reason: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "currency": self.currency,
            "reason": self.reason,
            "note_type": "credit",
            "created_at": self.created_at,
        }


@dataclass
class DebitNote:
    note_id: str = field(default_factory=_id)
    invoice_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    reason: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "currency": self.currency,
            "reason": self.reason,
            "note_type": "debit",
            "created_at": self.created_at,
        }


@dataclass
class Payment:
    payment_id: str = field(default_factory=_id)
    invoice_id: str = ""
    customer_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    method: str = "transfer"
    installment_no: int = 0
    is_refund: bool = False
    reference: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "method": self.method,
            "installment_no": self.installment_no,
            "is_refund": self.is_refund,
            "reference": self.reference,
            "created_at": self.created_at,
        }


@dataclass
class JournalEntry:
    entry_id: str = field(default_factory=_id)
    account_code: str = ""
    entry_type: AccountEntryType = AccountEntryType.DEBIT
    amount: float = 0.0
    currency: str = "USD"
    reference: str = ""
    description: str = ""
    company_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "account_code": self.account_code,
            "entry_type": self.entry_type.value,
            "amount": self.amount,
            "currency": self.currency,
            "reference": self.reference,
            "description": self.description,
            "company_id": self.company_id,
            "created_at": self.created_at,
        }


@dataclass
class ExchangeRate:
    rate_id: str = field(default_factory=_id)
    base_currency: str = "USD"
    quote_currency: str = "EUR"
    rate: float = 1.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rate_id": self.rate_id,
            "base_currency": self.base_currency,
            "quote_currency": self.quote_currency,
            "rate": self.rate,
            "created_at": self.created_at,
        }


@dataclass
class TaxRate:
    tax_id: str = field(default_factory=_id)
    name: str = "VAT"
    rate_pct: float = 0.0
    country: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tax_id": self.tax_id,
            "name": self.name,
            "rate_pct": self.rate_pct,
            "country": self.country,
            "created_at": self.created_at,
        }


@dataclass
class Budget:
    budget_id: str = field(default_factory=_id)
    name: str = ""
    cost_center: str = ""
    company_id: str = ""
    period: str = ""
    amount: float = 0.0
    spent: float = 0.0
    currency: str = "USD"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "budget_id": self.budget_id,
            "name": self.name,
            "cost_center": self.cost_center,
            "company_id": self.company_id,
            "period": self.period,
            "amount": self.amount,
            "spent": self.spent,
            "remaining": round(self.amount - self.spent, 2),
            "currency": self.currency,
            "created_at": self.created_at,
        }


@dataclass
class CostCenter:
    cost_center_id: str = field(default_factory=_id)
    code: str = ""
    name: str = ""
    company_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cost_center_id": self.cost_center_id,
            "code": self.code,
            "name": self.name,
            "company_id": self.company_id,
            "created_at": self.created_at,
        }


@dataclass
class ExpenseRecord:
    expense_id: str = field(default_factory=_id)
    cost_center: str = ""
    company_id: str = ""
    category: str = ""
    amount: float = 0.0
    currency: str = "USD"
    description: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "expense_id": self.expense_id,
            "cost_center": self.cost_center,
            "company_id": self.company_id,
            "category": self.category,
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "created_at": self.created_at,
        }


@dataclass
class Supplier:
    supplier_id: str = field(default_factory=_id)
    name: str = ""
    country: str = ""
    contact_email: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "country": self.country,
            "contact_email": self.contact_email,
            "created_at": self.created_at,
        }


@dataclass
class CustomerAccount:
    account_id: str = field(default_factory=_id)
    customer_id: str = ""
    currency: str = "USD"
    credit_limit: float = 0.0
    balance: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "customer_id": self.customer_id,
            "currency": self.currency,
            "credit_limit": self.credit_limit,
            "balance": self.balance,
            "available_credit": round(self.credit_limit - self.balance, 2),
            "created_at": self.created_at,
        }
