"""API Standardization Suite facade — Sprint 21.2 / v6.0.0-rc2."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.api_standardization.docs_gen.openapi import OpenApiBuilder
from applications.enterprise_hub.api_standardization.docs_gen.redoc import ReDoc
from applications.enterprise_hub.api_standardization.docs_gen.swagger import SwaggerUi
from applications.enterprise_hub.api_standardization.endpoint_registry import EndpointRegistry
from applications.enterprise_hub.api_standardization.gateway_compat import GatewayCompatibility
from applications.enterprise_hub.api_standardization.governance_engine import ApiGovernance
from applications.enterprise_hub.api_standardization.inventory import ApiInventory
from applications.enterprise_hub.api_standardization.models import INTEGRATION_TARGETS
from applications.enterprise_hub.api_standardization.standards.auth import AuthStandard
from applications.enterprise_hub.api_standardization.standards.events import EventApiStandard
from applications.enterprise_hub.api_standardization.standards.response import error_response, success_response
from applications.enterprise_hub.api_standardization.standards.rest import RestStandard
from applications.enterprise_hub.api_standardization.standards.websocket import WebSocketStandard
from applications.enterprise_hub.api_standardization.versioning import ApiVersioning
from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class ApiStandardizationSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.inventory = ApiInventory(self.store)
        self.registry = EndpointRegistry(self.store)
        self.rest = RestStandard(self.store)
        self.versioning = ApiVersioning(self.store)
        self.auth = AuthStandard(self.store)
        self.websocket = WebSocketStandard(self.store)
        self.events = EventApiStandard(self.store)
        self.openapi = OpenApiBuilder(self.store)
        self.swagger = SwaggerUi(self.store)
        self.redoc = ReDoc(self.store)
        self.gateway = GatewayCompatibility(self.store)
        self.governance = ApiGovernance(self.store)

    def success(self, data: Any, **kwargs: Any) -> dict[str, Any]:
        return success_response(data, **kwargs)

    def error(self, **kwargs: Any) -> dict[str, Any]:
        return error_response(**kwargs)

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True}

    def bootstrap(self) -> dict[str, Any]:
        inv = self.inventory.scan()
        for item in inv["items"]:
            self.registry.register(
                path=item["path"],
                method="GET",
                category=item["category"],
                service=item["service"],
                version="v1",
            )
        rest = self.rest.catalog(version="v1")
        # also seed v2 catalog for compatibility matrix
        self.rest.catalog(version="v2")
        versions = self.versioning.matrix()
        auth = self.auth.policy()
        ws = self.websocket.channels()
        evt = self.events.contract()
        sample = self.events.publish(
            {
                "id": "evt_bootstrap",
                "type": "api.standardization.ready",
                "source": "api_standardization",
                "aggregate": "platform",
                "version": 1,
                "payload": {"sprint": "21.2"},
                "timestamp": inv["scanned_at"],
                "correlation_id": "corr_bootstrap",
            }
        )
        oas = self.openapi.build()
        swag = self.swagger.render(openapi_id=oas["openapi_id"])
        redoc = self.redoc.render(openapi_id=oas["openapi_id"])
        gw = self.gateway.validate()
        gov = self.governance.run_all()
        return {
            "bootstrap": True,
            "inventory_id": inv["inventory_id"],
            "endpoints": inv["total"],
            "by_category": inv["by_category"],
            "registered": self.registry.status()["registered"],
            "rest_standard_id": rest["standard_id"],
            "versioning_id": versions["versioning_id"],
            "auth_policy_id": auth["policy_id"],
            "websocket_standard_id": ws["standard_id"],
            "event_contract_id": evt["contract_id"],
            "sample_event_id": sample["id"],
            "openapi_id": oas["openapi_id"],
            "openapi_version": oas["spec"]["openapi"],
            "swagger_id": swag["swagger_id"],
            "redoc_id": redoc["redoc_id"],
            "gateway_validation_id": gw["validation_id"],
            "gateways_compatible": gw["all_compatible"],
            "governance_id": gov["governance_id"],
            "governance_passed": gov["overall_passed"],
            "unified_response": self.success({"status": "standardized"}),
            "integrations": self.integrations(),
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "inventory": self.inventory.status(),
            "registry": self.registry.status(),
            "openapi": len(self.store.eas_openapi.list_all()),
            "governance_runs": len(self.store.eas_governance_runs.list_all()),
        }


api_standardization = ApiStandardizationSuite()
