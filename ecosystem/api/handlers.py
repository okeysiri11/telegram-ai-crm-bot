# Ecosystem API handlers — Sprint 7.1.

from __future__ import annotations

from aiohttp import web

from ecosystem import ecosystem
from ecosystem.api.middleware import error_response, json_response
from ecosystem.shared.exceptions import AuthorizationError, EcosystemError, NotFoundError, ValidationError


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, ValidationError):
        return error_response(str(exc), status=400)
    if isinstance(exc, NotFoundError):
        return error_response(str(exc), status=404)
    if isinstance(exc, AuthorizationError):
        return error_response(str(exc), status=403)
    if isinstance(exc, EcosystemError):
        return error_response(str(exc), status=400)
    raise exc


async def health_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.health())


async def register_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user, session = await ecosystem.engine.identity.register(
            email=data["email"],
            password=data["password"],
            display_name=data.get("display_name", ""),
        )
        ecosystem.engine.profiles.get_or_create(user.user_id)
        return json_response({"user": user.to_dict(), "session": session.to_dict()}, status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError("email and password required"))


async def login_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user, session = await ecosystem.engine.identity.login(
            data["email"],
            data["password"],
            device_name=data.get("device_name", ""),
            platform=data.get("platform", "web"),
            ip_address=request.remote or "",
            user_agent=request.headers.get("User-Agent", ""),
        )
        return json_response({"user": user.to_dict(), "session": session.to_dict()})
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError("email and password required"))


async def sso_login_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user, session = await ecosystem.engine.identity.sso_login(
            data["provider"],
            data["external_id"],
            data["email"],
            display_name=data.get("display_name", ""),
        )
        return json_response({"user": user.to_dict(), "session": session.to_dict()})
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError("provider, external_id, email required"))


async def profile_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    if request.method == "GET":
        profile = ecosystem.engine.profiles.get_or_create(user.user_id)
        return json_response(profile.to_dict())
    data = await request.json()
    profile = ecosystem.engine.profiles.update(user.user_id, **{k: v for k, v in data.items() if k in ("first_name", "last_name", "locale", "timezone", "phone", "avatar_url")})
    return json_response(profile.to_dict())


async def devices_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    devices = ecosystem.engine.identity.list_devices(user.user_id)
    return json_response({"devices": [d.to_dict() for d in devices]})


async def session_history_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    history = ecosystem.engine.identity.session_history(user.user_id)
    return json_response({"history": [h.to_dict() for h in history]})


async def mfa_enroll_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    data = await request.json() if request.can_read_body else {}
    enrollment = ecosystem.engine.identity.enroll_mfa(user.user_id, method=data.get("method", "totp"))
    return json_response(enrollment.to_dict(), status=201)


async def create_organization_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    data = await request.json()
    org = await ecosystem.engine.organizations.create_organization(
        name=data["name"],
        owner_id=user.user_id,
        tenant_id=data.get("tenant_id", ""),
        slug=data.get("slug", ""),
    )
    return json_response(org.to_dict(), status=201)


async def list_organizations_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    orgs = ecosystem.engine.organizations.list_organizations(owner_id=user.user_id)
    return json_response({"organizations": [o.to_dict() for o in orgs]})


async def create_workspace_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    data = await request.json()
    workspace = await ecosystem.engine.organizations.create_workspace(
        organization_id=data["organization_id"],
        name=data["name"],
        owner_id=user.user_id,
        is_default=data.get("is_default", False),
    )
    return json_response(workspace.to_dict(), status=201)


async def invite_member_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    data = await request.json()
    invitation = ecosystem.engine.organizations.create_invitation(
        organization_id=data["organization_id"],
        email=data["email"],
        role_id=data["role_id"],
        invited_by=user.user_id,
    )
    return json_response(invitation.to_dict(), status=201)


async def list_roles_handler(_request: web.Request) -> web.Response:
    roles = ecosystem.engine.permissions.list_roles()
    return json_response({"roles": [r.to_dict() for r in roles]})


async def dashboard_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    workspace_id = request.query.get("workspace_id", "")
    return json_response(ecosystem.engine.workspace.dashboard(user.user_id, workspace_id=workspace_id))


async def global_search_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    query = request.query.get("q", "")
    return json_response(ecosystem.engine.workspace.global_search(user.user_id, query))


async def favorites_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    if request.method == "GET":
        favs = ecosystem.engine.workspace.favorites(user.user_id)
        return json_response({"favorites": [f.to_dict() for f in favs]})
    data = await request.json()
    fav = ecosystem.engine.workspace.add_favorite(user.user_id, data["item_type"], data["item_id"], label=data.get("label", ""))
    return json_response(fav.to_dict(), status=201)


async def notifications_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    if request.method == "GET":
        notes = ecosystem.engine.workspace.notifications(user.user_id)
        return json_response({"notifications": [n.to_dict() for n in notes]})
    data = await request.json()
    note = ecosystem.engine.workspace.send_notification(user.user_id, data["title"], data["body"], source_application=data.get("source_application", "ecosystem"))
    return json_response(note.to_dict(), status=201)


async def quick_actions_handler(_request: web.Request) -> web.Response:
    return json_response({"actions": ecosystem.engine.workspace.quick_actions()})


async def navigation_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    user_id = user.user_id if user else ""
    org_id = request.query.get("organization_id", "")
    return json_response(ecosystem.engine.navigation.navigation_tree(user_id=user_id, organization_id=org_id))


async def open_application_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    data = await request.json()
    result = await ecosystem.engine.navigation.open_application(
        user.user_id,
        data["application_id"],
        workspace_id=data.get("workspace_id", ""),
    )
    ecosystem.engine.workspace.record_activity(
        user.user_id,
        "open_application",
        application_id=data["application_id"],
        workspace_id=data.get("workspace_id", ""),
    )
    return json_response(result)


async def assistant_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    data = await request.json()
    result = await ecosystem.engine.assistant.invoke(
        user.user_id,
        data["message"],
        application_id=data.get("application_id", ""),
        context=data.get("context"),
    )
    return json_response(result)


async def shared_services_handler(request: web.Request) -> web.Response:
    user = request["ecosystem_user"]
    if user is None:
        return error_response("Authentication required", status=401)
    service = request.match_info.get("service", "")
    if request.method == "GET":
        mapping = {
            "files": ecosystem.engine.shared.list_files,
            "calendar": ecosystem.engine.shared.list_calendar,
            "contacts": ecosystem.engine.shared.list_contacts,
            "tasks": ecosystem.engine.shared.list_tasks,
            "memory": lambda uid: ecosystem.engine.shared.recall(uid),
        }
        fn = mapping.get(service)
        if fn is None:
            return error_response("Unknown service", status=404)
        items = fn(user.user_id)
        return json_response({service: [i.to_dict() for i in items]})
    data = await request.json()
    app_id = data.get("application_id", "")
    if service == "files":
        item = ecosystem.engine.shared.add_file(user.user_id, data["name"], mime_type=data.get("mime_type", ""), application_id=app_id)
    elif service == "calendar":
        item = ecosystem.engine.shared.add_calendar_event(user.user_id, data["title"], application_id=app_id)
    elif service == "contacts":
        item = ecosystem.engine.shared.add_contact(user.user_id, data["name"], email=data.get("email", ""), application_id=app_id)
    elif service == "tasks":
        item = ecosystem.engine.shared.add_task(user.user_id, data["title"], application_id=app_id)
    elif service == "memory":
        item = await ecosystem.engine.shared.remember(user.user_id, data["content"], application_id=app_id, tags=data.get("tags"))
    else:
        return error_response("Unknown service", status=404)
    return json_response(item.to_dict(), status=201)


async def manifest_handler(_request: web.Request) -> web.Response:
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "manifest.json"
    return json_response(json.loads(path.read_text(encoding="utf-8")))
