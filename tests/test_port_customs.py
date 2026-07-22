"""Tests — Port ERP Customs & International Trade (Sprint 9.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_erp import port_erp
from applications.port_erp.api.register import register_port_erp_routes
from applications.port_erp.customs.models import (
    BrokerCase,
    CargoFlowStage,
    CertificateType,
    CustomsDeclaration,
    CustomsProcedure,
    DocumentType,
    TariffRate,
    TradeCertificate,
    TradeDocument,
    TradeShipment,
)


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_erp_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_erp.reset()
    yield
    port_erp.reset()


def test_version_customs_docs_bridges():
    health = port_erp.health()
    assert health["application_version"] == "1.5.0-alpha"
    assert health["customs_engine"] == "1.0"
    assert "customs" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "PORT_CUSTOMS.md"
    assert docs.exists()
    assert "Customs Engine" in docs.read_text(encoding="utf-8")
    assert port_erp.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert port_erp.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    root = Path(__file__).resolve().parents[1] / "applications" / "port_erp"
    for name in (
        "customs",
        "compliance",
        "certificates",
        "cargo_flow",
        "inspection",
        "international_trade",
        "incoterms",
        "tariffs",
        "broker",
        "documents",
    ):
        assert (root / name).is_dir()


@pytest.mark.asyncio
async def test_documents_and_certificates():
    types = port_erp.customs.documents.document_types()
    assert "bill_of_lading" in types
    assert "dangerous_goods_declaration" in types
    assert len(types) == 16

    doc = port_erp.customs.documents.create(
        TradeDocument(
            document_type=DocumentType.BILL_OF_LADING,
            title="B/L Ocean",
            shipment_id="ship-1",
            cargo_id="cargo-1",
        )
    )
    issued = port_erp.customs.documents.issue(doc.document_id)
    assert issued.status.value == "issued"
    signed = await port_erp.customs.documents.sign(doc.document_id, signed_by="agent@port")
    assert signed.status.value == "signed"
    assert signed.signed_by == "agent@port"

    cert = port_erp.customs.certificates.create(
        TradeCertificate(
            certificate_type=CertificateType.ORIGIN,
            cargo_id="cargo-1",
            shipment_id="ship-1",
            issuer="Chamber",
        )
    )
    issued_cert = await port_erp.customs.certificates.issue(cert.certificate_id)
    assert issued_cert.status.value == "issued"
    assert issued_cert.issued_at > 0


@pytest.mark.asyncio
async def test_trade_flow_incoterms_and_duties():
    assert len(port_erp.customs.trade.incoterms()) == 10
    assert port_erp.customs.trade.flow_stages()[0] == "booking"
    assert port_erp.customs.trade.flow_stages()[-1] == "completed"

    port_erp.customs.tariffs.register(
        TariffRate(hs_code="100590", description="Maize", duty_rate_pct=10, vat_rate_pct=16, country="KE")
    )
    shipment = port_erp.customs.trade.create_shipment(
        TradeShipment(
            cargo_id="cargo-maize",
            seller="FarmCo",
            buyer="TradeKE",
            origin_country="UA",
            destination_country="KE",
            incoterm="CIF",
            declared_value=10000,
        )
    )
    assert shipment.incoterm.value == "CIF"
    port_erp.customs.trade.advance_flow(shipment.shipment_id, CargoFlowStage.DOCUMENTATION)
    duties = port_erp.customs.trade.duty_estimate(shipment.shipment_id, hs_code="100590")
    assert duties["tariff_found"] is True
    assert duties["duty"] == 1000.0
    assert duties["total"] > 10000


@pytest.mark.asyncio
async def test_customs_channels_hold_release_complete():
    # Low risk → green → auto release
    low = port_erp.customs.customs.create_declaration(
        CustomsDeclaration(
            procedure=CustomsProcedure.IMPORT,
            cargo_id="c-low",
            hs_code="100590",
            declared_value=1000,
            country_of_destination="KE",
        )
    )
    submitted = await port_erp.customs.customs.submit(low.declaration_id)
    assert submitted.channel.value == "green"
    assert submitted.status.value == "released"

    # High value → yellow/red → inspection
    high = port_erp.customs.customs.create_declaration(
        CustomsDeclaration(
            procedure=CustomsProcedure.EXPORT,
            cargo_id="c-high",
            shipment_id="s-high",
            declared_value=250000,
            country_of_destination="KE",
        )
    )
    assessed = await port_erp.customs.customs.submit(high.declaration_id)
    assert assessed.channel.value in ("yellow", "red")
    assert assessed.status.value == "inspection"
    assert len(port_erp.customs.inspection.list_inspections(declaration_id=high.declaration_id)) >= 1

    held = await port_erp.customs.customs.hold(high.declaration_id, reason="docs_missing")
    assert held.status.value == "hold"
    released = await port_erp.customs.customs.release(high.declaration_id)
    assert released.status.value == "released"
    completed = await port_erp.customs.customs.complete(high.declaration_id)
    assert completed.status.value == "completed"


@pytest.mark.asyncio
async def test_compliance_and_broker():
    shipment = port_erp.customs.trade.create_shipment(
        TradeShipment(cargo_id="c-comp", seller="A", buyer="B", incoterm="FOB")
    )
    check_missing = port_erp.customs.compliance.evaluate_documents(
        shipment_id=shipment.shipment_id, direction="export"
    )
    assert check_missing.status.value == "non_compliant"
    assert any(f.startswith("missing:") for f in check_missing.findings)

    for dtype in (
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.EXPORT_DECLARATION,
        DocumentType.BILL_OF_LADING,
    ):
        port_erp.customs.documents.create(
            TradeDocument(document_type=dtype, shipment_id=shipment.shipment_id, title=dtype.value)
        )
    port_erp.customs.certificates.create(
        TradeCertificate(
            certificate_type=CertificateType.ORIGIN,
            shipment_id=shipment.shipment_id,
            issuer="Chamber",
        )
    )
    check_ok = port_erp.customs.compliance.evaluate_documents(
        shipment_id=shipment.shipment_id, direction="export"
    )
    assert check_ok.status.value == "compliant"

    case = port_erp.customs.broker.open_case(
        BrokerCase(broker_id="broker-1", shipment_id=shipment.shipment_id)
    )
    cleared = port_erp.customs.broker.clear(case.case_id, notes="cleared")
    assert cleared.status.value == "cleared"


@pytest.mark.asyncio
async def test_customs_rest_api(client: TestClient):
    health = await client.get("/api/port/v1/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "1.5.0-alpha"
    assert body["customs_engine"] == "1.0"

    customs = await client.get("/api/port/v1/customs")
    assert customs.status == 200

    types = await client.get("/api/port/v1/documents/types")
    assert types.status == 200
    assert len((await types.json())["items"]) == 16

    shipment_resp = await client.post(
        "/api/port/v1/trade",
        json={
            "cargo_id": "api-c1",
            "seller": "S",
            "buyer": "B",
            "incoterm": "FOB",
            "declared_value": 5000,
            "destination_country": "KE",
        },
    )
    assert shipment_resp.status == 201
    shipment = await shipment_resp.json()

    doc = await client.post(
        "/api/port/v1/documents",
        json={
            "document_type": "commercial_invoice",
            "shipment_id": shipment["shipment_id"],
            "title": "Invoice",
        },
    )
    assert doc.status == 201
    document = await doc.json()
    signed = await client.post(
        f"/api/port/v1/documents/{document['document_id']}/sign",
        json={"signed_by": "ops"},
    )
    assert signed.status == 200

    cert = await client.post(
        "/api/port/v1/certificates",
        json={
            "certificate_type": "certificate_of_origin",
            "shipment_id": shipment["shipment_id"],
            "issuer": "Chamber",
        },
    )
    assert cert.status == 201
    certificate = await cert.json()
    issued = await client.post(
        f"/api/port/v1/certificates/{certificate['certificate_id']}/issue",
        json={},
    )
    assert issued.status == 200

    broker = await client.post(
        "/api/port/v1/broker",
        json={"broker_id": "br-1", "shipment_id": shipment["shipment_id"]},
    )
    assert broker.status == 201

    compliance = await client.post(
        "/api/port/v1/compliance/evaluate",
        json={"shipment_id": shipment["shipment_id"], "direction": "export"},
    )
    assert compliance.status == 200

    incoterms = await client.get("/api/port/v1/trade/incoterms")
    assert incoterms.status == 200
    assert len((await incoterms.json())["items"]) == 10
