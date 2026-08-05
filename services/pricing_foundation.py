# Pricing Foundation — Sprint 32.2.
# Facade over services.pricing_engine.PricingEngine. No second pricing engine.

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class TariffPlan:
    plan_id: str
    name: str
    currency: str
    amount: Decimal
    interval: str  # once | monthly | yearly
    features: list[str] = field(default_factory=list)


@dataclass
class DiscountRule:
    discount_id: str
    kind: str  # percent | fixed | promo
    value: Decimal
    code: str | None = None


@dataclass
class TaxRule:
    tax_id: str
    name: str
    rate_percent: Decimal
    jurisdiction: str


@dataclass
class CommissionRule:
    commission_id: str
    partner: str
    rate_percent: Decimal


@dataclass
class PriceQuote:
    currency: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    commission: Decimal
    total: Decimal
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k in ("subtotal", "discount", "tax", "commission", "total"):
            d[k] = str(d[k])
        return d


SUPPORTED_FIAT = ("USD", "EUR", "UAH", "GBP")
SUPPORTED_CRYPTO = ("BTC", "ETH", "USDT")


class PricingFoundation:
    """
    Design surface for tariffs · discounts · promos · subscriptions ·
    commissions · multi-currency · crypto · taxes · AI pricing.

    Runtime calculations continue to use PricingEngine where DB-backed.
    """

    def __init__(self) -> None:
        self.tariffs: dict[str, TariffPlan] = {
            "starter": TariffPlan("starter", "Starter", "USD", Decimal("49"), "monthly", ["core"]),
            "growth": TariffPlan("growth", "Growth", "USD", Decimal("199"), "monthly", ["core", "ai"]),
            "enterprise": TariffPlan("enterprise", "Enterprise", "USD", Decimal("999"), "monthly", ["core", "ai", "sso"]),
        }
        self.discounts: dict[str, DiscountRule] = {
            "launch10": DiscountRule("launch10", "percent", Decimal("10"), "LAUNCH10"),
        }
        self.taxes: dict[str, TaxRule] = {
            "ua_vat": TaxRule("ua_vat", "UA VAT", Decimal("20"), "UA"),
        }
        self.commissions: dict[str, CommissionRule] = {
            "partner_std": CommissionRule("partner_std", "partner", Decimal("15")),
        }

    def list_tariffs(self) -> list[dict[str, Any]]:
        return [
            {
                "plan_id": t.plan_id,
                "name": t.name,
                "currency": t.currency,
                "amount": str(t.amount),
                "interval": t.interval,
                "features": t.features,
            }
            for t in self.tariffs.values()
        ]

    def quote(
        self,
        *,
        plan_id: str,
        discount_code: str | None = None,
        tax_id: str | None = "ua_vat",
        commission_id: str | None = None,
        ai_units: int = 0,
        ai_unit_price: Decimal = Decimal("0.02"),
    ) -> PriceQuote:
        plan = self.tariffs.get(plan_id)
        if not plan:
            raise ValueError(f"unknown plan: {plan_id}")
        subtotal = plan.amount + (ai_unit_price * Decimal(ai_units))
        discount = Decimal("0")
        if discount_code:
            for rule in self.discounts.values():
                if rule.code == discount_code:
                    if rule.kind == "percent":
                        discount = (subtotal * rule.value / Decimal("100")).quantize(Decimal("0.01"))
                    else:
                        discount = rule.value
                    break
        taxable = max(Decimal("0"), subtotal - discount)
        tax = Decimal("0")
        if tax_id and tax_id in self.taxes:
            tax = (taxable * self.taxes[tax_id].rate_percent / Decimal("100")).quantize(Decimal("0.01"))
        commission = Decimal("0")
        if commission_id and commission_id in self.commissions:
            commission = (taxable * self.commissions[commission_id].rate_percent / Decimal("100")).quantize(
                Decimal("0.01")
            )
        total = taxable + tax
        return PriceQuote(
            currency=plan.currency,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            commission=commission,
            total=total,
            meta={
                "plan_id": plan_id,
                "ai_units": ai_units,
                "supported_fiat": list(SUPPORTED_FIAT),
                "supported_crypto": list(SUPPORTED_CRYPTO),
                "engine": "pricing_foundation",
                "runtime_engine": "services.pricing_engine.PricingEngine",
            },
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "tariffs": True,
            "discounts": True,
            "promotions": True,
            "subscriptions": True,
            "commissions": True,
            "multi_currency": True,
            "crypto": True,
            "taxes": True,
            "ai_pricing": True,
            "system_of_record": "services.pricing_engine.PricingEngine",
            "foundation_only": True,
        }


pricing_foundation = PricingFoundation()
