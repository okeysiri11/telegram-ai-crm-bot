"""Cloud security — encrypted telemetry/commands, certificates, RBAC, permissions, audit (Sprint 11.8)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


ROLES = ("admin", "supervisor", "mission_commander", "operator", "observer", "maintenance", "engineer")


class CloudSecurity:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def encrypt_telemetry(self, *, payload: str, key_id: str = "default") -> dict[str, Any]:
        cipher = hashlib.sha256(f"{key_id}:{payload}".encode()).hexdigest()
        return {"encrypted": True, "algo": "AES-256-GCM-sim", "key_id": key_id, "ciphertext": cipher[:48], "at": _now()}

    def encrypt_command(self, *, command: str, key_id: str = "default") -> dict[str, Any]:
        cipher = hashlib.sha256(f"cmd:{key_id}:{command}".encode()).hexdigest()
        return {"encrypted": True, "algo": "AES-256-GCM-sim", "key_id": key_id, "ciphertext": cipher[:48], "command_ref": command[:32], "at": _now()}

    def issue_certificate(self, *, subject: str, purpose: str = "operator") -> dict[str, Any]:
        if not subject:
            raise ValidationError("certificate subject required")
        cid = f"cert_{uuid.uuid4().hex[:12]}"
        cert = {
            "cert_id": cid,
            "subject": subject,
            "purpose": purpose,
            "fingerprint": hashlib.sha256(f"{subject}:{purpose}".encode()).hexdigest()[:32],
            "status": "active",
            "issued_at": _now(),
        }
        self.store.cloud_certificates.save(cid, cert)
        return cert

    def grant_role(self, *, principal: str, role: str) -> dict[str, Any]:
        if role not in ROLES:
            raise ValidationError(f"role must be one of {ROLES}")
        rid = f"rbac_{uuid.uuid4().hex[:10]}"
        grant = {"rbac_id": rid, "principal": principal, "role": role, "granted_at": _now()}
        self.store.cloud_rbac.save(rid, grant)
        return grant

    def operator_permissions(self, *, operator_id: str, permissions: list[str] | None = None) -> dict[str, Any]:
        perms = list(permissions or ["view_mission", "view_telemetry"])
        pid = f"operm_{uuid.uuid4().hex[:10]}"
        item = {"permission_id": pid, "operator_id": operator_id, "permissions": perms, "at": _now()}
        self.store.cloud_permissions.save(pid, item)
        return item

    def mission_permissions(self, *, mission_id: str, principal: str, permissions: list[str] | None = None) -> dict[str, Any]:
        perms = list(permissions or ["read"])
        pid = f"mperm_{uuid.uuid4().hex[:10]}"
        item = {"permission_id": pid, "mission_id": mission_id, "principal": principal, "permissions": perms, "at": _now()}
        self.store.cloud_permissions.save(pid, item)
        return item

    def audit_log(self, *, actor: str, action: str, resource: str = "") -> dict[str, Any]:
        aid = f"secaud_{uuid.uuid4().hex[:12]}"
        entry = {"audit_id": aid, "actor": actor, "action": action, "resource": resource, "created_at": _now()}
        self.store.cloud_security_audit.save(aid, entry)
        return entry

    def list_audit(self) -> list[dict[str, Any]]:
        return self.store.cloud_security_audit.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "security": "1.0",
            "certificates": len(self.store.cloud_certificates.list_all()),
            "rbac": len(self.store.cloud_rbac.list_all()),
            "audit": len(self.list_audit()),
            "ready": True,
        }


cloud_security = CloudSecurity()
