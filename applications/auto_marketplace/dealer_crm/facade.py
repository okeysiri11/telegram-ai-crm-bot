"""Dealer CRM Suite facade — Sprint 13.3."""

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.dealer_crm.crm import DealerCRM
from applications.auto_marketplace.dealer_crm.inventory import InventoryIntelligence
from applications.auto_marketplace.dealer_crm.services import DealerAnalytics, DealerIntegrations, SalesAI
from applications.auto_marketplace.dealer_crm.tradein import TradeInAI
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DealerCRMSuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.crm = DealerCRM(self.store)
        self.tradein = TradeInAI(self.store)
        self.inventory = InventoryIntelligence(self.store)
        self.sales_ai = SalesAI(self.store)
        self.analytics = DealerAnalytics(self.store)
        self.integrations = DealerIntegrations(self.store)

    def bootstrap(self) -> dict[str, Any]:
        dealer = self.crm.create_dealership(name="Prime Motors CRM", region="EU", contact="crm@prime.example")
        customer = self.crm.create_customer(name="Alex Buyer", email="alex@example.com", dealership_id=dealer["dealership_id"])
        lead = self.crm.create_lead(
            name="Alex Buyer",
            interest="Golf",
            source="referral",
            dealership_id=dealer["dealership_id"],
            customer_id=customer["customer_id"],
        )
        self.crm.advance_pipeline(lead["lead_id"], stage="qualified")
        self.crm.log_contact(channel="call", related_id=lead["lead_id"], summary="Intro call")
        self.crm.log_contact(channel="email", related_id=lead["lead_id"], summary="Brochure sent")
        self.crm.log_contact(channel="messenger", related_id=lead["lead_id"], summary="Telegram follow-up")
        self.crm.create_task(title="Prepare trade-in quote", assignee="sales-1", related_id=lead["lead_id"])
        self.crm.schedule_appointment(
            title="Test drive",
            starts_at="2026-07-25T10:00:00Z",
            customer_id=customer["customer_id"],
            dealership_id=dealer["dealership_id"],
        )

        inv = self.inventory.add_vehicle(
            vin="WVWZZZ1JZXW000001",
            make="Volkswagen",
            model="Golf",
            year=2020,
            price=18500,
            warehouse="eu-1",
            dealership_id=dealer["dealership_id"],
        )
        self.inventory.add_vehicle(
            vin="5YJ3E1EA1KF000001",
            make="Tesla",
            model="Model 3",
            year=2021,
            price=32000,
            warehouse="eu-1",
            dealership_id=dealer["dealership_id"],
            status="incoming",
        )
        evaluation = self.tradein.evaluate(
            vin="WVWZZZ1JZXW000001",
            mileage=45000,
            damage_score=0.25,
            market_value=18500,
            inspection_ref="ia-bootstrap",
            vin_decode_ref="vi-bootstrap",
        )
        offer = self.tradein.generate_offer(evaluation["evaluation_id"], customer_id=customer["customer_id"])
        qualification = self.sales_ai.qualify_lead(lead_id=lead["lead_id"], budget=20000, intent="trade_in")
        self.sales_ai.forecast(dealership_id=dealer["dealership_id"])
        self.inventory.optimize(dealership_id=dealer["dealership_id"])
        self.integrations.connect(target="vin_intelligence", endpoint="/api/vin-intelligence/v1")
        self.integrations.connect(target="inspection_ai", endpoint="/api/inspection-ai/v1")
        self.integrations.connect(target="marketplace", endpoint="/api/auto-marketplace/v1")
        board = self.analytics.render(dashboard_type="sales", dealership_id=dealer["dealership_id"])
        return {
            "bootstrap": True,
            "dealership_id": dealer["dealership_id"],
            "lead_id": lead["lead_id"],
            "inventory_id": inv["inventory_id"],
            "evaluation_id": evaluation["evaluation_id"],
            "offer_id": offer["offer_id"],
            "qualification_id": qualification["qualification_id"],
            "dashboard_id": board["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "crm": self.crm.status(),
            "tradein": self.tradein.status(),
            "inventory": self.inventory.status(),
            "sales_ai": self.sales_ai.status(),
            "analytics": self.analytics.status(),
            "integrations": self.integrations.status(),
        }


dealer_crm = DealerCRMSuite()
