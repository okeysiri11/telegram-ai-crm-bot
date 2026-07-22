"""Drone Cloud core — manager, registry, sync, backup, storage, gateway, API, auth, audit (Sprint 11.8)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CloudManager:
    """Cloud Manager + Registry + Sync + Backup + Storage + Gateway + API + Auth + Audit."""

    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def register_node(
        self,
        *,
        name: str,
        region: str = "eu-central",
        node_type: str = "edge",
        company_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("cloud node name required")
        cid = f"cld_{uuid.uuid4().hex[:12]}"
        item = {
            "cloud_id": cid,
            "name": name,
            "region": region,
            "node_type": node_type,
            "company_id": company_id,
            "status": "online",
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.cloud_nodes.save(cid, item)
        return item

    def get_node(self, cloud_id: str) -> dict[str, Any]:
        item = self.store.cloud_nodes.get(cloud_id)
        if item is None:
            raise NotFoundError("cloud_node", cloud_id)
        return item

    def list_nodes(self) -> list[dict[str, Any]]:
        return self.store.cloud_nodes.list_all()

    def sync(self, *, source_id: str, target_id: str, entities: list[str] | None = None) -> dict[str, Any]:
        self.get_node(source_id)
        self.get_node(target_id)
        sid = f"sync_{uuid.uuid4().hex[:12]}"
        record = {
            "sync_id": sid,
            "source_id": source_id,
            "target_id": target_id,
            "entities": list(entities or ["missions", "fleet", "telemetry"]),
            "status": "completed",
            "synced_at": _now(),
        }
        self.store.cloud_syncs.save(sid, record)
        return record

    def backup(self, *, cloud_id: str, label: str = "scheduled") -> dict[str, Any]:
        self.get_node(cloud_id)
        bid = f"bak_{uuid.uuid4().hex[:12]}"
        record = {
            "backup_id": bid,
            "cloud_id": cloud_id,
            "label": label,
            "object_count": len(self.store.cloud_objects.list_all()) + len(self.store.ops_missions.list_all()),
            "status": "stored",
            "created_at": _now(),
        }
        self.store.cloud_backups.save(bid, record)
        return record

    def store_object(self, *, key: str, content: str = "", content_type: str = "application/json", cloud_id: str = "") -> dict[str, Any]:
        if not key:
            raise ValidationError("storage key required")
        oid = f"obj_{uuid.uuid4().hex[:12]}"
        item = {
            "object_id": oid,
            "key": key,
            "content_type": content_type,
            "size_bytes": len(content.encode("utf-8")),
            "cloud_id": cloud_id,
            "checksum": hashlib.sha256(content.encode("utf-8")).hexdigest()[:16],
            "created_at": _now(),
        }
        self.store.cloud_objects.save(oid, item)
        return item

    def gateway_route(self, *, path: str, method: str = "GET", target: str = "mission_ops") -> dict[str, Any]:
        return {
            "gateway": "drone_cloud",
            "path": path,
            "method": method.upper(),
            "target": target,
            "routed": True,
            "at": _now(),
        }

    def authenticate(self, *, principal: str, token: str = "", role: str = "operator") -> dict[str, Any]:
        if not principal:
            raise ValidationError("principal required")
        session_token = token or hashlib.sha256(f"{principal}:{_now()}".encode()).hexdigest()[:24]
        sid = f"cauth_{uuid.uuid4().hex[:12]}"
        session = {
            "auth_id": sid,
            "principal": principal,
            "role": role,
            "token": session_token,
            "authenticated": True,
            "created_at": _now(),
        }
        self.store.cloud_sessions.save(sid, session)
        return session

    def audit(self, *, actor: str, action: str, resource: str = "", details: dict[str, Any] | None = None) -> dict[str, Any]:
        aid = f"aud_{uuid.uuid4().hex[:12]}"
        entry = {
            "audit_id": aid,
            "actor": actor,
            "action": action,
            "resource": resource,
            "details": dict(details or {}),
            "created_at": _now(),
        }
        self.store.cloud_audit.save(aid, entry)
        return entry

    def list_audit(self) -> list[dict[str, Any]]:
        return self.store.cloud_audit.list_all()

    def cloud_api_info(self) -> dict[str, Any]:
        return {
            "api": "drone_cloud",
            "version": "1.0",
            "endpoints": ["/cloud", "/cloud/remote", "/cloud/fleet", "/cloud/command", "/cloud/twins", "/cloud/security", "/cloud/enterprise"],
        }

    def status(self) -> dict[str, Any]:
        return {
            "cloud_manager": "1.0",
            "nodes": len(self.list_nodes()),
            "syncs": len(self.store.cloud_syncs.list_all()),
            "backups": len(self.store.cloud_backups.list_all()),
            "objects": len(self.store.cloud_objects.list_all()),
            "audit_entries": len(self.list_audit()),
            "ready": True,
        }


cloud_manager = CloudManager()
