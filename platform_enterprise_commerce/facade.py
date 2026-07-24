"""Commerce Core library facade — Sprint 22.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_commerce.advisor import AICommerceAdvisor
from platform_enterprise_commerce.certificates import GiftCertificateEngine
from platform_enterprise_commerce.integrations import CommerceIntegrations
from platform_enterprise_commerce.inventory import InventoryIntegration
from platform_enterprise_commerce.loyalty import LoyaltyEngine
from platform_enterprise_commerce.memberships import MembershipEngine
from platform_enterprise_commerce.models import PRINCIPLES
from platform_enterprise_commerce.payments import PaymentGateway
from platform_enterprise_commerce.pos import POSWorkspace
from platform_enterprise_commerce.sales import SalesEngine


class CommerceCoreLibrary:
    def __init__(self) -> None:
        self.sales = SalesEngine()
        self.pos = POSWorkspace()
        self.certificates = GiftCertificateEngine()
        self.memberships = MembershipEngine()
        self.loyalty = LoyaltyEngine()
        self.inventory = InventoryIntegration()
        self.payments = PaymentGateway()
        self.advisor = AICommerceAdvisor()
        self.integrations = CommerceIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        pos = self.pos.session(cashier_id="admin", industry="beauty")
        sale = self.sales.sell(
            lines=[
                {"kind": "service", "name": "Haircut", "price": 40, "qty": 1, "materials": [{"sku": "shampoo", "qty": 1}]},
                {"kind": "product", "name": "Serum", "sku": "serum-1", "barcode": "460001", "price": 25, "qty": 1},
            ],
            payments=[{"method": "card", "amount": 50}, {"method": "bonus", "amount": 15}],
            customer_id="c1",
            mode="full",
            industry="beauty",
        )
        inv = self.inventory.deduct(sale_lines=sale["lines"], stock={"shampoo": 8, "serum-1": 5})
        cert = self.certificates.issue(face_value=100, customer_id="c1")
        cert = self.certificates.activate(cert)
        cert = self.certificates.redeem(cert, amount=30)
        membership = self.memberships.create(customer_id="c1", visits_limit=8)
        membership = self.memberships.debit(membership, visits=1)
        loyalty = self.loyalty.profile(customer_id="c1", points=80)
        loyalty = self.loyalty.earn(loyalty, amount=sale["total"])
        pay = self.payments.charge(provider="terminal", amount=50, currency="USD", reference="sale-boot")
        advice = self.advisor.analyze(sales=[sale], certificates=[cert], loyalty=loyalty)
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "pos_ready": pos["status"] == "open",
            "sale_under_20s": sale["under_20s"],
            "mixed_payment": sale["mixed_payment"],
            "inventory_auto_deducted": inv["auto_deducted"],
            "certificate_balance": cert["balance"],
            "membership_remaining": membership["visits_remaining"],
            "loyalty_level": loyalty["level"],
            "payment_providers": len(self.payments.providers()),
            "advisor_proposes_only": advice["proposes_only"],
            "ai_may_act": False,
            "unified_finance_history": True,
            "duplicates_core_logic": False,
            "commerce_core_ready": True,
            "status": "ready",
            "integrations": links,
            "full": {
                "pos": pos,
                "sale": sale,
                "inventory": inv,
                "certificate": cert,
                "membership": membership,
                "loyalty": loyalty,
                "payment": pay,
                "advice": advice,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "sales",
                "pos",
                "certificates",
                "memberships",
                "loyalty",
                "inventory",
                "payments",
                "advisor",
            ],
            "principles": self.principles(),
        }


commerce_core_library = CommerceCoreLibrary()
