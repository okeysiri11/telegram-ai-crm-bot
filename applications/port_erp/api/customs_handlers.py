# Port ERP customs / trade / documentation REST handlers — Sprint 9.4.

from __future__ import annotations

from aiohttp import web

from applications.port_erp import port_erp
from applications.port_erp.api.middleware import error_response, json_response
from applications.port_erp.customs.models import (
    BrokerCase,
    CertificateType,
    CustomsDeclaration,
    CustomsProcedure,
    DocumentType,
    TariffRate,
    TradeCertificate,
    TradeDocument,
    TradeShipment,
)
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError


async def customs_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "customs_engine": port_erp.config.customs_engine,
            "application_version": port_erp.config.application_version,
            "metrics": port_erp.customs.metrics(),
            "procedures": port_erp.customs.customs.procedures(),
            "channels": port_erp.customs.customs.channels(),
        }
    )


async def customs_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        decl = port_erp.customs.customs.create_declaration(
            CustomsDeclaration(
                procedure=CustomsProcedure(data.get("procedure", "import")),
                cargo_id=data.get("cargo_id", ""),
                shipment_id=data.get("shipment_id", ""),
                broker_id=data.get("broker_id", ""),
                hs_code=data.get("hs_code", ""),
                country_of_origin=data.get("country_of_origin", ""),
                country_of_destination=data.get("country_of_destination", ""),
                declared_value=float(data.get("declared_value", 0) or 0),
                currency=data.get("currency", "USD"),
            )
        )
        return json_response(decl.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def customs_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [d.to_dict() for d in port_erp.customs.customs.list_declarations()]})


async def customs_submit_handler(request: web.Request) -> web.Response:
    try:
        decl = await port_erp.customs.customs.submit(request.match_info["declaration_id"])
        return json_response(decl.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def customs_hold_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        decl = await port_erp.customs.customs.hold(
            request.match_info["declaration_id"],
            reason=(data or {}).get("reason", "customs_hold"),
        )
        return json_response(decl.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def customs_release_handler(request: web.Request) -> web.Response:
    try:
        decl = await port_erp.customs.customs.release(request.match_info["declaration_id"])
        return json_response(decl.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def customs_complete_handler(request: web.Request) -> web.Response:
    try:
        decl = await port_erp.customs.customs.complete(request.match_info["declaration_id"])
        return json_response(decl.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def documents_types_handler(_request: web.Request) -> web.Response:
    return json_response({"items": port_erp.customs.documents.document_types()})


async def documents_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        doc = port_erp.customs.documents.create(
            TradeDocument(
                document_type=DocumentType(data.get("document_type", "bill_of_lading")),
                title=data.get("title", ""),
                reference=data.get("reference", ""),
                cargo_id=data.get("cargo_id", ""),
                shipment_id=data.get("shipment_id", ""),
                party_from=data.get("party_from", ""),
                party_to=data.get("party_to", ""),
            )
        )
        return json_response(doc.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def documents_list_handler(request: web.Request) -> web.Response:
    items = port_erp.customs.documents.list_documents(
        shipment_id=request.query.get("shipment_id") or None,
        cargo_id=request.query.get("cargo_id") or None,
    )
    return json_response({"items": [d.to_dict() for d in items]})


async def documents_sign_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        doc = await port_erp.customs.documents.sign(
            request.match_info["document_id"],
            signed_by=data.get("signed_by", ""),
        )
        return json_response(doc.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def certificates_types_handler(_request: web.Request) -> web.Response:
    return json_response({"items": port_erp.customs.certificates.certificate_types()})


async def certificates_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        cert = port_erp.customs.certificates.create(
            TradeCertificate(
                certificate_type=CertificateType(data.get("certificate_type", "certificate_of_origin")),
                title=data.get("title", ""),
                cargo_id=data.get("cargo_id", ""),
                shipment_id=data.get("shipment_id", ""),
                issuer=data.get("issuer", ""),
            )
        )
        return json_response(cert.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def certificates_list_handler(request: web.Request) -> web.Response:
    items = port_erp.customs.certificates.list_certificates(
        shipment_id=request.query.get("shipment_id") or None,
        cargo_id=request.query.get("cargo_id") or None,
    )
    return json_response({"items": [c.to_dict() for c in items]})


async def certificates_issue_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        cert = await port_erp.customs.certificates.issue(
            request.match_info["certificate_id"],
            issuer=(data or {}).get("issuer", ""),
        )
        return json_response(cert.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def trade_incoterms_handler(_request: web.Request) -> web.Response:
    return json_response({"items": port_erp.customs.trade.incoterms()})


async def trade_stages_handler(_request: web.Request) -> web.Response:
    return json_response({"items": port_erp.customs.trade.flow_stages()})


async def trade_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        shipment = port_erp.customs.trade.create_shipment(
            TradeShipment(
                cargo_id=data.get("cargo_id", ""),
                seller=data.get("seller", ""),
                buyer=data.get("buyer", ""),
                origin_country=data.get("origin_country", ""),
                destination_country=data.get("destination_country", ""),
                incoterm=data.get("incoterm", "FOB"),
                mode=data.get("mode", "sea"),
                declared_value=float(data.get("declared_value", 0) or 0),
                currency=data.get("currency", "USD"),
                broker_id=data.get("broker_id", ""),
            )
        )
        return json_response(shipment.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def trade_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [s.to_dict() for s in port_erp.customs.trade.list_shipments()]})


async def trade_advance_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        shipment = port_erp.customs.trade.advance_flow(
            request.match_info["shipment_id"],
            data.get("stage", ""),
        )
        return json_response(shipment.to_dict())
    except (ValidationError, NotFoundError, ValueError) as exc:
        return error_response(str(exc), status=400 if not isinstance(exc, NotFoundError) else 404)


async def trade_customs_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        decl = await port_erp.customs.trade.start_customs(
            request.match_info["shipment_id"],
            procedure=data.get("procedure", "import"),
            hs_code=data.get("hs_code", ""),
            broker_id=data.get("broker_id", ""),
        )
        return json_response(decl.to_dict())
    except (ValidationError, NotFoundError, ValueError) as exc:
        return error_response(str(exc), status=400 if not isinstance(exc, NotFoundError) else 404)


async def trade_duties_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        result = port_erp.customs.trade.duty_estimate(
            request.match_info["shipment_id"],
            hs_code=data.get("hs_code", ""),
        )
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def broker_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        case = port_erp.customs.broker.open_case(
            BrokerCase(
                broker_id=data.get("broker_id", ""),
                shipment_id=data.get("shipment_id", ""),
                declaration_id=data.get("declaration_id", ""),
                notes=data.get("notes", ""),
            )
        )
        return json_response(case.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def broker_list_handler(request: web.Request) -> web.Response:
    items = port_erp.customs.broker.list_cases(broker_id=request.query.get("broker_id") or None)
    return json_response({"items": [c.to_dict() for c in items]})


async def broker_clear_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        case = port_erp.customs.broker.clear(
            request.match_info["case_id"],
            notes=(data or {}).get("notes", ""),
        )
        return json_response(case.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def compliance_evaluate_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        check = port_erp.customs.compliance.evaluate_documents(
            shipment_id=data.get("shipment_id", ""),
            cargo_id=data.get("cargo_id", ""),
            direction=data.get("direction", "export"),
        )
        return json_response(check.to_dict())
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def compliance_list_handler(request: web.Request) -> web.Response:
    items = port_erp.customs.compliance.list_checks(
        shipment_id=request.query.get("shipment_id") or None
    )
    return json_response({"items": [c.to_dict() for c in items]})


async def tariffs_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        tariff = port_erp.customs.tariffs.register(
            TariffRate(
                hs_code=data.get("hs_code", ""),
                description=data.get("description", ""),
                duty_rate_pct=float(data.get("duty_rate_pct", 0) or 0),
                vat_rate_pct=float(data.get("vat_rate_pct", 0) or 0),
                country=data.get("country", ""),
            )
        )
        return json_response(tariff.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def tariffs_list_handler(request: web.Request) -> web.Response:
    items = port_erp.customs.tariffs.list_tariffs(country=request.query.get("country") or None)
    return json_response({"items": [t.to_dict() for t in items]})
