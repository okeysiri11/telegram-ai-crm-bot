from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.api_standardization.models import STANDARD_REST_RESOURCES


class OpenApiBuilder:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def build(self, *, title: str = "Enterprise AI CRM API", version: str = "v1") -> dict[str, Any]:
        paths: dict[str, Any] = {}
        for resource in STANDARD_REST_RESOURCES:
            paths[f"/api/{version}/{resource}"] = {
                "get": {"summary": f"List {resource}", "responses": {"200": {"description": "OK"}}},
                "post": {"summary": f"Create {resource}", "responses": {"201": {"description": "Created"}}},
            }
            paths[f"/api/{version}/{resource}/{{id}}"] = {
                "get": {"summary": f"Get {resource}", "responses": {"200": {"description": "OK"}}},
                "put": {"summary": f"Replace {resource}", "responses": {"200": {"description": "OK"}}},
                "patch": {"summary": f"Update {resource}", "responses": {"200": {"description": "OK"}}},
                "delete": {"summary": f"Delete {resource}", "responses": {"204": {"description": "No Content"}}},
            }
        oid = _id("eas_oas")
        spec = {
            "openapi": "3.1.0",
            "info": {"title": title, "version": version, "description": "Enterprise API Standardization"},
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
                    "apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
                }
            },
            "security": [{"bearerAuth": []}, {"apiKey": []}],
        }
        record = {"openapi_id": oid, "spec": spec, "built_at": _now()}
        self.store.eas_openapi.save(oid, record)
        return record
