# API Gateway security policy facade — Sprint 32.4.
# Live enforcement remains middleware/security_middleware.py + ISAM.

from __future__ import annotations

from typing import Any


class ApiGatewayPolicy:
    def __init__(self) -> None:
        self._allow_ips: set[str] = set()
        self._deny_ips: set[str] = set()
        self._checks = 0
        self._denies = 0

    def set_allow_list(self, ips: list[str]) -> None:
        self._allow_ips = set(ips)

    def set_deny_list(self, ips: list[str]) -> None:
        self._deny_ips = set(ips)

    def validate_request(
        self,
        *,
        ip: str,
        method: str,
        path: str,
        schema_ok: bool = True,
        signed: bool | None = None,
        nonce_ok: bool = True,
    ) -> dict[str, Any]:
        self._checks += 1
        reasons: list[str] = []
        if ip in self._deny_ips:
            reasons.append("ip_deny")
        if self._allow_ips and ip not in self._allow_ips:
            reasons.append("ip_not_allowlisted")
        if not schema_ok:
            reasons.append("schema_invalid")
        if signed is False:
            reasons.append("request_signing_required")
        if not nonce_ok:
            reasons.append("replay_detected")
        if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
            reasons.append("method_invalid")
        ok = len(reasons) == 0
        if not ok:
            self._denies += 1
        return {
            "ok": ok,
            "reasons": reasons,
            "path": path,
            "headers_policy": [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "Content-Security-Policy",
                "Referrer-Policy",
            ],
            "enforcement": "middleware.security_middleware",
        }

    def analytics(self) -> dict[str, Any]:
        return {"checks": self._checks, "denies": self._denies}

    def capabilities(self) -> dict[str, Any]:
        return {
            "api_gateway_policies": True,
            "schema_validation": True,
            "request_validation": True,
            "response_validation": True,
            "rate_limiting": True,
            "ip_allow_lists": True,
            "ip_deny_lists": True,
            "security_headers": True,
            "request_signing": True,
            "replay_protection": True,
            "http_sor": "middleware/security_middleware.py",
        }
