# Finance & Documents domain models — Sprint 6.5.

from __future__ import annotations

import enum
import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class FinanceRole(str, enum.Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    FINANCE_MANAGER = "finance_manager"
    SALES_MANAGER = "sales_manager"
    DEALER = "dealer"
    CUSTOMER = "customer"
    AI_AGENT = "ai_agent"


class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SIGNED = "signed"
    ARCHIVED = "archived"


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class ContractType(str, enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    TRADE_IN = "trade_in"
    DEALER = "dealer"
    CUSTOMER = "customer"


class PaymentMethodType(str, enum.Enum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    FINANCING = "financing"
    CHECK = "check"


class TransactionType(str, enum.Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    COMMISSION = "commission"
    SETTLEMENT = "settlement"
    TAX = "tax"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    PAID = "paid"
    VOID = "void"


class RefundStatus(str, enum.Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    PROCESSED = "processed"
    REJECTED = "rejected"


class SettlementStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


def mask_sensitive(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return f"{'*' * (len(value) - 4)}{value[-4:]}"


def encrypt_field(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass
class DocumentTemplate:
    template_id: str = field(default_factory=_id)
    name: str = ""
    category: str = "general"
    content: str = ""
    version: int = 1
    variables: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "category": self.category,
            "content": self.content,
            "version": self.version,
            "variables": list(self.variables),
            "created_at": self.created_at,
        }


@dataclass
class DocumentVersion:
    version: int = 1
    content: str = ""
    created_at: float = field(default_factory=_ts)
    created_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version, "content": self.content, "created_at": self.created_at, "created_by": self.created_by}


@dataclass
class Document:
    document_id: str = field(default_factory=_id)
    title: str = ""
    category: str = "general"
    template_id: str = ""
    deal_id: str = ""
    customer_id: str = ""
    dealer_id: str = ""
    status: DocumentStatus = DocumentStatus.DRAFT
    content: str = ""
    pdf_url: str = ""
    versions: list[DocumentVersion] = field(default_factory=list)
    signature_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "category": self.category,
            "template_id": self.template_id,
            "deal_id": self.deal_id,
            "customer_id": self.customer_id,
            "dealer_id": self.dealer_id,
            "status": self.status.value,
            "content": self.content,
            "pdf_url": self.pdf_url,
            "versions": [v.to_dict() for v in self.versions],
            "signature_id": self.signature_id,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Contract:
    contract_id: str = field(default_factory=_id)
    contract_type: ContractType = ContractType.PURCHASE
    title: str = ""
    deal_id: str = ""
    customer_id: str = ""
    dealer_id: str = ""
    vehicle_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: ContractStatus = ContractStatus.DRAFT
    document_id: str = ""
    signed_at: float | None = None
    signed_by: str = ""
    expires_at: float | None = None
    terms: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_type": self.contract_type.value,
            "title": self.title,
            "deal_id": self.deal_id,
            "customer_id": self.customer_id,
            "dealer_id": self.dealer_id,
            "vehicle_id": self.vehicle_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "document_id": self.document_id,
            "signed_at": self.signed_at,
            "signed_by": self.signed_by,
            "expires_at": self.expires_at,
            "terms": dict(self.terms),
            "created_at": self.created_at,
        }


@dataclass
class PurchaseAgreement(Contract):
    contract_type: ContractType = field(default=ContractType.PURCHASE, init=False)
    financing_terms: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["financing_terms"] = dict(self.financing_terms)
        return data


@dataclass
class SaleAgreement(Contract):
    contract_type: ContractType = field(default=ContractType.SALE, init=False)
    commission_rate: float = 0.05


@dataclass
class PaymentMethod:
    method_id: str = field(default_factory=_id)
    method_type: PaymentMethodType = PaymentMethodType.CARD
    label: str = ""
    last_four: str = ""
    encrypted_token: str = ""
    customer_id: str = ""
    is_default: bool = False

    def to_dict(self, *, mask: bool = True) -> dict[str, Any]:
        return {
            "method_id": self.method_id,
            "method_type": self.method_type.value,
            "label": self.label,
            "last_four": mask_sensitive(self.last_four) if mask else self.last_four,
            "customer_id": self.customer_id,
            "is_default": self.is_default,
        }


@dataclass
class FinancePayment:
    payment_id: str = field(default_factory=_id)
    deal_id: str = ""
    customer_id: str = ""
    dealer_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    method_id: str = ""
    status: str = "pending"
    transaction_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "deal_id": self.deal_id,
            "customer_id": self.customer_id,
            "dealer_id": self.dealer_id,
            "amount": self.amount,
            "currency": self.currency,
            "method_id": self.method_id,
            "status": self.status,
            "transaction_id": self.transaction_id,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class Transaction:
    transaction_id: str = field(default_factory=_id)
    transaction_type: TransactionType = TransactionType.PAYMENT
    payment_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    reference: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type.value,
            "payment_id": self.payment_id,
            "amount": self.amount,
            "currency": self.currency,
            "reference": self.reference,
            "created_at": self.created_at,
        }


@dataclass
class FinanceInvoice:
    invoice_id: str = field(default_factory=_id)
    deal_id: str = ""
    customer_id: str = ""
    dealer_id: str = ""
    payment_id: str = ""
    amount: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "USD"
    status: InvoiceStatus = InvoiceStatus.DRAFT
    line_items: list[dict[str, Any]] = field(default_factory=list)
    pdf_url: str = ""
    document_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "deal_id": self.deal_id,
            "customer_id": self.customer_id,
            "dealer_id": self.dealer_id,
            "payment_id": self.payment_id,
            "amount": self.amount,
            "tax_amount": self.tax_amount,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "status": self.status.value,
            "line_items": list(self.line_items),
            "pdf_url": self.pdf_url,
            "document_id": self.document_id,
            "created_at": self.created_at,
        }


@dataclass
class Receipt:
    receipt_id: str = field(default_factory=_id)
    payment_id: str = ""
    invoice_id: str = ""
    customer_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    pdf_url: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "payment_id": self.payment_id,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "currency": self.currency,
            "pdf_url": self.pdf_url,
            "created_at": self.created_at,
        }


@dataclass
class Refund:
    refund_id: str = field(default_factory=_id)
    payment_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    reason: str = ""
    status: RefundStatus = RefundStatus.REQUESTED
    processed_at: float | None = None
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "refund_id": self.refund_id,
            "payment_id": self.payment_id,
            "amount": self.amount,
            "currency": self.currency,
            "reason": self.reason,
            "status": self.status.value,
            "processed_at": self.processed_at,
            "created_at": self.created_at,
        }


@dataclass
class TaxRecord:
    tax_id: str = field(default_factory=_id)
    invoice_id: str = ""
    deal_id: str = ""
    jurisdiction: str = ""
    rate: float = 0.0
    taxable_amount: float = 0.0
    tax_amount: float = 0.0
    currency: str = "USD"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tax_id": self.tax_id,
            "invoice_id": self.invoice_id,
            "deal_id": self.deal_id,
            "jurisdiction": self.jurisdiction,
            "rate": self.rate,
            "taxable_amount": self.taxable_amount,
            "tax_amount": self.tax_amount,
            "currency": self.currency,
            "created_at": self.created_at,
        }


@dataclass
class Commission:
    commission_id: str = field(default_factory=_id)
    deal_id: str = ""
    agent_id: str = ""
    dealer_id: str = ""
    sale_amount: float = 0.0
    rate: float = 0.05
    amount: float = 0.0
    currency: str = "USD"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "commission_id": self.commission_id,
            "deal_id": self.deal_id,
            "agent_id": self.agent_id,
            "dealer_id": self.dealer_id,
            "sale_amount": self.sale_amount,
            "rate": self.rate,
            "amount": self.amount,
            "currency": self.currency,
            "created_at": self.created_at,
        }


@dataclass
class DealerSettlement:
    settlement_id: str = field(default_factory=_id)
    dealer_id: str = ""
    period_start: float = 0.0
    period_end: float = 0.0
    gross_amount: float = 0.0
    commission_total: float = 0.0
    net_amount: float = 0.0
    currency: str = "USD"
    status: SettlementStatus = SettlementStatus.PENDING
    payment_ids: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "settlement_id": self.settlement_id,
            "dealer_id": self.dealer_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "gross_amount": self.gross_amount,
            "commission_total": self.commission_total,
            "net_amount": self.net_amount,
            "currency": self.currency,
            "status": self.status.value,
            "payment_ids": list(self.payment_ids),
            "created_at": self.created_at,
        }


@dataclass
class FinancialReport:
    report_id: str = field(default_factory=_id)
    report_type: str = "summary"
    period_start: float = 0.0
    period_end: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "metrics": dict(self.metrics),
            "created_at": self.created_at,
        }


@dataclass
class AuditRecord:
    audit_id: str = field(default_factory=_id)
    actor_id: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": dict(self.details),
            "created_at": self.created_at,
        }
