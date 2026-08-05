"""Platform State HTTP API — Sprint 34.2C."""

from __future__ import annotations

from aiohttp import web

from platform_management.permissions import ManagementRole, require_role
from platform_state.service import platform_state


@require_role(ManagementRole.READ_ONLY)
async def platform_state_status_handler(request: web.Request) -> web.Response:
    return web.json_response({"success": True, "data": platform_state.status()})


@require_role(ManagementRole.READ_ONLY)
async def platform_state_snapshot_handler(request: web.Request) -> web.Response:
    user_id = request.query.get("user_id")
    telegram_raw = request.query.get("telegram_id")
    telegram_id = int(telegram_raw) if telegram_raw and str(telegram_raw).isdigit() else None
    workspace_id = request.query.get("workspace_id")
    slices_raw = request.query.get("slices")
    slices = [s.strip() for s in slices_raw.split(",") if s.strip()] if slices_raw else None
    snap = platform_state.snapshot(
        user_id=user_id,
        telegram_id=telegram_id,
        workspace_id=workspace_id,
        slices=slices,
    )
    return web.json_response({"success": True, "data": snap.to_dict()})


@require_role(ManagementRole.READ_ONLY)
async def platform_state_delta_handler(request: web.Request) -> web.Response:
    last = request.query.get("since") or request.query.get("revision")
    slices_raw = request.query.get("slices")
    slices = [s.strip() for s in slices_raw.split(",") if s.strip()] if slices_raw else None
    return web.json_response({"success": True, "data": platform_state.delta(last, slices=slices)})


@require_role(ManagementRole.ADMINISTRATOR)
async def platform_state_cursor_handler(request: web.Request) -> web.Response:
    body = await request.json() if request.body_exists else {}
    client_id = str(body.get("client_id") or request.query.get("client_id") or "anonymous")
    last_revision = body.get("last_revision") or request.query.get("last_revision")
    slices = body.get("slices")
    data = platform_state.register_client_cursor(
        client_id,
        last_revision=last_revision,
        slices=slices,
    )
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.ADMINISTRATOR)
async def platform_state_mutate_handler(request: web.Request) -> web.Response:
    """
    Unified write entry for adapters.
    body: { op, source_client, ...op-specific fields }
    """
    body = await request.json()
    op = str(body.get("op") or "")
    source_client = str(body.get("source_client") or "api")
    actor_id = body.get("actor_id")
    skip_db = bool(body.get("skip_db", False))

    if op == "task.create":
        data = await platform_state.tasks.create(
            title=str(body["title"]),
            creator_telegram_id=int(body.get("telegram_id") or 0),
            source_client=source_client,
            description=str(body.get("description") or ""),
            actor_id=actor_id,
            skip_db=skip_db,
        )
    elif op == "task.complete":
        data = await platform_state.tasks.complete(
            task_id=body["task_id"],
            user_telegram_id=int(body.get("telegram_id") or 0),
            source_client=source_client,
            actor_id=actor_id,
            skip_db=skip_db,
        )
    elif op == "calendar.create":
        data = await platform_state.calendar.create_event(
            title=str(body["title"]),
            start_time=str(body["start_time"]),
            creator_telegram_id=int(body.get("telegram_id") or 0),
            source_client=source_client,
            actor_id=actor_id,
            skip_db=skip_db,
        )
    elif op == "notification.create":
        data = await platform_state.notifications.create(
            title=str(body.get("title") or "Notification"),
            body=str(body.get("body") or ""),
            user_id=body.get("user_id"),
            telegram_id=body.get("telegram_id"),
            source_client=source_client,
            actor_id=actor_id,
        )
    elif op == "conversation.ensure":
        data = await platform_state.conversations.ensure(
            source_client=source_client,
            external_id=str(body["external_id"]),
            user_id=body.get("user_id"),
            telegram_id=body.get("telegram_id"),
            workspace_id=body.get("workspace_id"),
        )
    elif op == "conversation.append":
        data = await platform_state.conversations.append(
            conversation_id=str(body["conversation_id"]),
            role=str(body.get("role") or "user"),
            content=str(body["content"]),
            source_client=source_client,
            actor_id=actor_id,
            attachments=body.get("attachments"),
        )
    elif op == "memory.store":
        data = await platform_state.memory.store(
            scope=str(body.get("scope") or "user"),
            scope_id=str(body["scope_id"]),
            content=str(body["content"]),
            source_client=source_client,
            category=str(body.get("category") or "general"),
            actor_id=actor_id,
            conversation_id=body.get("conversation_id"),
        )
    elif op == "file.upload":
        data = await platform_state.files.upload(
            name=str(body["name"]),
            source_client=source_client,
            conversation_id=body.get("conversation_id"),
            mime=body.get("mime"),
            actor_id=actor_id,
        )
    elif op == "crm.lead.upsert":
        data = await platform_state.crm.update_lead(
            dict(body.get("lead") or body),
            source_client=source_client,
            actor_id=actor_id,
        )
    elif op == "workspace.change":
        data = await platform_state.workspaces.change(
            str(body["workspace_id"]),
            source_client=source_client,
            actor_id=actor_id,
            changes=body.get("changes"),
        )
    else:
        raise web.HTTPBadRequest(text=f"unknown op: {op}")

    return web.json_response(
        {
            "success": True,
            "data": data,
            "revision": platform_state.sync.revision,
        }
    )


@require_role(ManagementRole.READ_ONLY)
async def platform_state_enterprise_handler(request: web.Request) -> web.Response:
    return web.json_response({"success": True, "data": platform_state.enterprise.status()})


@require_role(ManagementRole.READ_ONLY)
async def platform_state_events_handler(request: web.Request) -> web.Response:
    after = int(request.query.get("after_seq") or 0)
    limit = min(int(request.query.get("limit") or 500), 10_000)
    entity_type = request.query.get("entity_type")
    entity_id = request.query.get("entity_id")
    workspace_id = request.query.get("workspace_id")
    if entity_type and entity_id:
        events = platform_state.events.stream(entity_type, entity_id, after_seq=after, limit=limit)
    elif workspace_id:
        events = platform_state.events.workspace_stream(workspace_id, after_seq=after, limit=limit)
    else:
        events = platform_state.events.since_seq(after, limit=limit)
    return web.json_response(
        {"success": True, "data": {"events": [e.to_dict() for e in events], "max_seq": platform_state.events.max_seq()}}
    )


@require_role(ManagementRole.READ_ONLY)
async def platform_state_versions_handler(request: web.Request) -> web.Response:
    entity_type = request.match_info["entity_type"]
    entity_id = request.match_info["entity_id"]
    return web.json_response(
        {
            "success": True,
            "data": {
                "head": (platform_state.versions.get(entity_type, entity_id) or None)
                and platform_state.versions.get(entity_type, entity_id).to_dict(),
                "history": platform_state.versions.history(entity_type, entity_id),
            },
        }
    )


@require_role(ManagementRole.READ_ONLY)
async def platform_state_timeline_handler(request: web.Request) -> web.Response:
    entity_type = request.match_info["entity_type"]
    entity_id = request.match_info["entity_id"]
    return web.json_response(
        {
            "success": True,
            "data": {"timeline": platform_state.timeline.for_entity(entity_type, entity_id)},
        }
    )


@require_role(ManagementRole.ADMINISTRATOR)
async def platform_state_replay_handler(request: web.Request) -> web.Response:
    body = await request.json() if request.body_exists else {}
    mode = str(body.get("mode") or request.query.get("mode") or "all")
    after_seq = int(body.get("after_seq") or 0)
    if mode == "entity":
        result = platform_state.replay.replay_entity(
            str(body["entity_type"]),
            str(body["entity_id"]),
            after_seq=after_seq,
        )
    elif mode == "workspace":
        result = platform_state.replay.replay_workspace(str(body["workspace_id"]), after_seq=after_seq)
    elif mode == "time_travel":
        result = platform_state.replay.time_travel(
            at_or_before=str(body["at"]),
            entity_type=body.get("entity_type"),
            entity_id=body.get("entity_id"),
            workspace_id=body.get("workspace_id"),
        )
    else:
        result = platform_state.replay.replay_all(after_seq=after_seq)
    return web.json_response({"success": True, "data": result.to_dict()})


@require_role(ManagementRole.ADMINISTRATOR)
async def platform_state_heal_handler(request: web.Request) -> web.Response:
    body = await request.json() if request.body_exists else {}
    kind = str(body.get("kind") or "reconnect")
    if kind == "worker_restart":
        data = platform_state.healing.on_worker_restart()
    elif kind == "replay_failure":
        data = platform_state.healing.on_replay_failure(
            error=str(body.get("error") or "unknown"),
            after_seq=int(body.get("after_seq") or 0),
        )
    else:
        data = platform_state.healing.on_reconnect(
            str(body.get("client_id") or "anonymous"),
            last_revision=body.get("last_revision"),
            slices=body.get("slices"),
            client_kind=str(body.get("client_kind") or "generic"),
        )
    return web.json_response({"success": True, "data": data})


@require_role(ManagementRole.READ_ONLY)
async def platform_state_telemetry_handler(request: web.Request) -> web.Response:
    return web.json_response({"success": True, "data": platform_state.telemetry.snapshot()})


def register_platform_state_routes(app: web.Application) -> None:
    from platform_api.versioning import MANAGEMENT_V1_PREFIX, register_dual_prefix_routes

    route_specs = [
        ("GET", "", platform_state_status_handler),
        ("GET", "snapshot", platform_state_snapshot_handler),
        ("GET", "delta", platform_state_delta_handler),
        ("GET", "enterprise", platform_state_enterprise_handler),
        ("GET", "events", platform_state_events_handler),
        ("GET", "versions/{entity_type}/{entity_id}", platform_state_versions_handler),
        ("GET", "timeline/{entity_type}/{entity_id}", platform_state_timeline_handler),
        ("GET", "telemetry", platform_state_telemetry_handler),
        ("POST", "cursor", platform_state_cursor_handler),
        ("POST", "mutate", platform_state_mutate_handler),
        ("POST", "replay", platform_state_replay_handler),
        ("POST", "heal", platform_state_heal_handler),
    ]
    register_dual_prefix_routes(
        app,
        route_specs=route_specs,
        v1_prefix=f"{MANAGEMENT_V1_PREFIX}/platform-state",
        legacy_prefix="/management/platform-state",
    )
