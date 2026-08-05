"""API handlers — Enterprise Identity, Security & Access Management (Sprint 19.8)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return enterprise_hub.isam


async def isam_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_isam_ready": health.get("enterprise_isam_ready"),
            "authentication_ready": health.get("authentication_ready"),
            "authorization_ready": health.get("authorization_ready"),
            "security_monitoring_ready": health.get("security_monitoring_ready"),
            "suite": _suite().status(),
        }
    )


async def isam_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def isam_identity_handler(request: web.Request) -> web.Response:
    try:
        identity = _suite().identity
        if request.method == "GET":
            return json_response(identity.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "deactivate":
            return json_response(identity.deactivate(identity_id=body.get("identity_id", "")), status=201)
        return json_response(
            identity.register(
                subject=body.get("subject", ""),
                identity_type=body.get("identity_type", "user"),
                roles=body.get("roles") if isinstance(body.get("roles"), list) else None,
                attributes=body.get("attributes") if isinstance(body.get("attributes"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def isam_auth_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(
                {
                    "authentication": suite.authentication.status(),
                    "authorization": suite.authorization.status(),
                }
            )
        body = await _read_json(request)
        action = body.get("action", "login")
        if action == "authorize":
            return json_response(
                suite.authorization.authorize(
                    identity_id=body.get("identity_id", ""),
                    permission=body.get("permission", ""),
                    mode=body.get("mode", "rbac"),
                    attributes=body.get("attributes") if isinstance(body.get("attributes"), dict) else None,
                ),
                status=201,
            )
        if action == "google_login":
            result = suite.authentication.login_google(
                id_token=body.get("id_token") or body.get("secret") or "",
                subject_hint=body.get("subject", ""),
                default_role=body.get("role", "employee"),
            )
            identity = result["identity"]
            access = suite.tokens.issue(identity_id=identity["identity_id"], token_type="access")
            refresh = suite.tokens.issue(identity_id=identity["identity_id"], token_type="refresh")
            session = suite.sessions.create(
                identity_id=identity["identity_id"],
                device=body.get("device", "enterprise_web"),
                ip=body.get("ip", ""),
                remember_me=bool(body.get("remember_me")),
                browser=body.get("browser", ""),
            )
            suite.audit.record(
                action="google_login",
                actor=identity.get("subject", ""),
                subject=identity["identity_id"],
                detail=f"mode={result['claims'].get('mode')}",
            )
            return json_response(
                {
                    **result,
                    "access_token": access.get("value"),
                    "refresh_token": refresh.get("value"),
                    "session": session,
                },
                status=201,
            )
        if action == "register":
            result = suite.authentication.register_local(
                email=body.get("email") or body.get("subject") or "",
                password=body.get("password") or body.get("secret") or "",
                name=body.get("name", ""),
                role=body.get("role", "employee"),
            )
            suite.audit.record(
                action="register",
                actor=result["identity"].get("subject", ""),
                subject=result["identity"]["identity_id"],
            )
            return json_response(result, status=201)
        if action == "password_reset":
            result = suite.authentication.request_password_reset(
                email=body.get("email") or body.get("subject") or ""
            )
            suite.audit.record(
                action="password_reset",
                actor=result.get("email", ""),
                detail="request",
            )
            return json_response(result, status=201)
        return json_response(
            suite.authentication.login(
                subject=body.get("subject", ""),
                provider=body.get("provider", "local"),
                secret=body.get("secret", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def isam_roles_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(
                {"roles": suite.roles.status(), "permissions": suite.permissions.status()}
            )
        body = await _read_json(request)
        action = body.get("action", "assign")
        if action == "grant":
            return json_response(
                suite.permissions.grant(
                    identity_id=body.get("identity_id", ""),
                    permission=body.get("permission", ""),
                ),
                status=201,
            )
        if action == "resolve":
            return json_response(suite.permissions.resolve(identity_id=body.get("identity_id", "")), status=201)
        return json_response(
            suite.roles.assign(identity_id=body.get("identity_id", ""), role=body.get("role", "employee")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def isam_session_handler(request: web.Request) -> web.Response:
    try:
        sessions = _suite().sessions
        if request.method == "GET":
            identity_id = request.rel_url.query.get("identity_id", "")
            if identity_id:
                return json_response(
                    {
                        "sessions": sessions.list_for_identity(identity_id=identity_id),
                        "last_login": sessions.last_login(identity_id=identity_id),
                        "status": sessions.status(),
                    }
                )
            return json_response(sessions.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "terminate":
            return json_response(sessions.terminate(session_id=body.get("session_id", "")), status=201)
        if action == "terminate_all":
            result = sessions.terminate_all(identity_id=body.get("identity_id", ""))
            _suite().audit.record(
                action="session_revoke_all",
                actor=body.get("identity_id", ""),
                subject=body.get("identity_id", ""),
                detail=f"revoked={result.get('revoked')}",
            )
            return json_response(result, status=201)
        if action == "trust":
            return json_response(
                sessions.trust_device(
                    session_id=body.get("session_id", ""),
                    trusted=bool(body.get("trusted", True)),
                ),
                status=201,
            )
        return json_response(
            sessions.create(
                identity_id=body.get("identity_id", ""),
                device=body.get("device", "unknown"),
                ip=body.get("ip", ""),
                ttl_seconds=int(body.get("ttl_seconds", 3600) or 3600),
                remember_me=bool(body.get("remember_me")),
                trusted=bool(body.get("trusted")),
                browser=body.get("browser", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def isam_token_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(
                {"tokens": suite.tokens.status(), "api_keys": suite.api_keys.status()}
            )
        body = await _read_json(request)
        action = body.get("action", "issue")
        if action == "rotate":
            return json_response(suite.tokens.rotate(token_id=body.get("token_id", "")), status=201)
        if action == "revoke":
            return json_response(suite.tokens.revoke(token_id=body.get("token_id", "")), status=201)
        if action == "api_key":
            return json_response(
                suite.api_keys.create(
                    identity_id=body.get("identity_id", ""),
                    name=body.get("name", "default"),
                ),
                status=201,
            )
        if action == "revoke_key":
            return json_response(suite.api_keys.revoke(key_id=body.get("key_id", "")), status=201)
        return json_response(
            suite.tokens.issue(
                identity_id=body.get("identity_id", ""),
                token_type=body.get("token_type", "access"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def isam_mfa_handler(request: web.Request) -> web.Response:
    try:
        mfa = _suite().mfa
        if request.method == "GET":
            identity_id = request.rel_url.query.get("identity_id", "")
            org = request.rel_url.query.get("organization_id", "")
            if identity_id:
                return json_response(
                    {
                        **mfa.status(),
                        "requirement": mfa.required_for(
                            identity_id=identity_id, organization_id=org
                        ),
                    }
                )
            return json_response(mfa.status())
        body = await _read_json(request)
        action = body.get("action", "challenge")
        if action == "enable":
            result = mfa.set_user_mfa(identity_id=body.get("identity_id", ""), enabled=True)
            _suite().audit.record(
                action="mfa_enable",
                actor=body.get("identity_id", ""),
                subject=body.get("identity_id", ""),
            )
            return json_response(result, status=201)
        if action == "disable":
            result = mfa.set_user_mfa(identity_id=body.get("identity_id", ""), enabled=False)
            _suite().audit.record(
                action="mfa_disable",
                actor=body.get("identity_id", ""),
                subject=body.get("identity_id", ""),
            )
            return json_response(result, status=201)
        if action == "org_policy":
            return json_response(
                mfa.set_org_policy(
                    organization_id=body.get("organization_id", ""),
                    require_mfa=bool(body.get("require_mfa")),
                ),
                status=201,
            )
        return json_response(
            mfa.challenge(
                method=body.get("method", "totp"),
                subject=body.get("subject", ""),
                code=body.get("code", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def isam_policy_handler(request: web.Request) -> web.Response:
    try:
        policies = _suite().policies
        if request.method == "GET":
            return json_response(policies.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "evaluate":
            return json_response(
                policies.evaluate(
                    policy_id=body.get("policy_id", ""),
                    context=body.get("context") if isinstance(body.get("context"), dict) else None,
                ),
                status=201,
            )
        return json_response(
            policies.create(
                kind=body.get("kind", "ip"),
                name=body.get("name", ""),
                rule=body.get("rule") if isinstance(body.get("rule"), dict) else None,
                company_id=body.get("company_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def isam_monitor_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(
                {
                    "intrusion": suite.intrusion.status(),
                    "anomaly": suite.anomaly.status(),
                    "risk": suite.risk.status(),
                }
            )
        body = await _read_json(request)
        action = body.get("action", "intrusion")
        if action == "anomaly":
            return json_response(
                suite.anomaly.flag(
                    subject=body.get("subject", ""),
                    kind=body.get("kind", "unusual_activity"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "risk":
            return json_response(
                suite.risk.score(
                    subject=body.get("subject", ""),
                    factors=body.get("factors") if isinstance(body.get("factors"), dict) else None,
                ),
                status=201,
            )
        return json_response(
            suite.intrusion.flag(
                subject=body.get("subject", ""),
                kind=body.get("kind", "brute_force"),
                detail=body.get("detail", ""),
                severity=body.get("severity", "medium"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def isam_audit_handler(request: web.Request) -> web.Response:
    try:
        audit = _suite().audit
        if request.method == "GET":
            return json_response(audit.status())
        body = await _read_json(request)
        return json_response(
            audit.record(
                action=body.get("action", ""),
                actor=body.get("actor", ""),
                subject=body.get("subject", ""),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def isam_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dt = request.rel_url.query.get("dashboard_type", "")
            if dt:
                return json_response(dashboard.render(dashboard_type=dt))
            return json_response(dashboard.status())
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "identity")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
