# Unified Assistant API handlers — Sprint 7.3.

from __future__ import annotations

from aiohttp import web

from ecosystem import ecosystem
from ecosystem.api.middleware import error_response, json_response
from ecosystem.assistant.models import SkillType
from ecosystem.shared.exceptions import EcosystemError, NotFoundError, ValidationError


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, ValidationError):
        return error_response(str(exc), status=400)
    if isinstance(exc, NotFoundError):
        return error_response(str(exc), status=404)
    if isinstance(exc, EcosystemError):
        return error_response(str(exc), status=400)
    raise exc


def _user_id(request: web.Request, data: dict | None = None) -> str:
    user = request.get("ecosystem_user")
    if user is not None:
        return user.user_id
    if data and data.get("user_id"):
        return data["user_id"]
    raise ValidationError("Authentication or user_id required")


async def assistant_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.assistant.metrics())


async def assistant_invoke_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user_id = _user_id(request, data)
        result = await ecosystem.engine.assistant.invoke(
            user_id,
            data["message"],
            application_id=data.get("application_id", ""),
            organization_id=data.get("organization_id", ""),
            conversation_id=data.get("conversation_id", ""),
            locale=data.get("locale", "en"),
            context=data.get("context"),
        )
        return json_response(result)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError("message required"))


async def assistant_orchestrate_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user_id = _user_id(request, data)
        result = await ecosystem.engine.assistant.orchestrate(
            user_id,
            data["goal"],
            agents=data.get("agents"),
        )
        return json_response(result)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError("goal required"))


async def knowledge_upsert_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        node = await ecosystem.engine.assistant.knowledge.upsert_node(
            data["label"],
            data.get("content", ""),
            node_type=data.get("node_type", "concept"),
            application_id=data.get("application_id", ""),
            tags=data.get("tags"),
            metadata=data.get("metadata"),
        )
        return json_response(node.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError("label required"))


async def knowledge_search_handler(request: web.Request) -> web.Response:
    query = request.query.get("q", "")
    application_id = request.query.get("application_id", "")
    hits = ecosystem.engine.assistant.knowledge.semantic_search(query, application_id=application_id)
    return json_response({"query": query, "hits": hits})


async def knowledge_link_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        edge = ecosystem.engine.assistant.knowledge.link(
            data["source_id"],
            data["target_id"],
            relation=data.get("relation", "related_to"),
            weight=float(data.get("weight", 1.0)),
        )
        return json_response(edge.to_dict(), status=201)
    except (KeyError, EcosystemError, ValueError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def knowledge_sync_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        nodes = await ecosystem.engine.assistant.knowledge.synchronize(
            data["application_id"],
            data.get("nodes", []),
        )
        return json_response({"nodes": [n.to_dict() for n in nodes]})
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def conversation_create_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user_id = _user_id(request, data)
        conversation = await ecosystem.engine.assistant.conversations.create(
            user_id,
            application_id=data.get("application_id", ""),
            organization_id=data.get("organization_id", ""),
            title=data.get("title", ""),
            locale=data.get("locale", "en"),
            voice_ready=bool(data.get("voice_ready", False)),
        )
        return json_response(conversation.to_dict(), status=201)
    except EcosystemError as exc:
        return _handle_error(exc)


async def conversation_list_handler(request: web.Request) -> web.Response:
    try:
        user_id = request.query.get("user_id") or _user_id(request)
        conversations = ecosystem.engine.assistant.conversations.list_for_user(user_id)
        return json_response({"conversations": [c.to_dict() for c in conversations]})
    except EcosystemError as exc:
        return _handle_error(exc)


async def conversation_get_handler(request: web.Request) -> web.Response:
    try:
        conversation = ecosystem.engine.assistant.conversations.get(request.match_info["conversation_id"])
        return json_response(conversation.to_dict())
    except EcosystemError as exc:
        return _handle_error(exc)


async def conversation_summarize_handler(request: web.Request) -> web.Response:
    try:
        conversation = ecosystem.engine.assistant.conversations.summarize(request.match_info["conversation_id"])
        return json_response(conversation.to_dict())
    except EcosystemError as exc:
        return _handle_error(exc)


async def conversation_restore_handler(request: web.Request) -> web.Response:
    try:
        conversation_id = request.match_info["conversation_id"]
        restored = ecosystem.engine.assistant.conversations.restore_context(conversation_id)
        user_id = restored.get("context_snapshot", {}).get("user", {}).get("user_id", "")
        if not user_id:
            conversation = ecosystem.engine.assistant.conversations.get(conversation_id)
            user_id = conversation.user_id
        await ecosystem.engine.assistant.context.restore(user_id, conversation_id)
        return json_response(restored)
    except EcosystemError as exc:
        return _handle_error(exc)


async def skills_list_handler(request: web.Request) -> web.Response:
    skill_type_raw = request.query.get("type")
    skill_type = SkillType(skill_type_raw) if skill_type_raw else None
    application_id = request.query.get("application_id", "")
    skills = ecosystem.engine.assistant.skills.list_skills(skill_type=skill_type, application_id=application_id)
    return json_response({"skills": [s.to_dict() for s in skills]})


async def skills_register_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        skill = ecosystem.engine.assistant.skills.register(
            data["name"],
            skill_type=SkillType(data.get("skill_type", "application")),
            description=data.get("description", ""),
            application_id=data.get("application_id", ""),
            handler_key=data.get("handler_key", ""),
            parameters_schema=data.get("parameters_schema"),
            priority=int(data.get("priority", 100)),
        )
        return json_response(skill.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def skills_execute_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user_id = _user_id(request, data)
        result = await ecosystem.engine.assistant.skills.execute(
            data["skill_id"],
            user_id,
            data.get("parameters"),
        )
        return json_response(result)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def context_get_handler(request: web.Request) -> web.Response:
    try:
        user_id = request.query.get("user_id") or _user_id(request)
        return json_response(ecosystem.engine.assistant.context.assemble(user_id))
    except EcosystemError as exc:
        return _handle_error(exc)


async def context_update_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user_id = _user_id(request, data)
        bundle = ecosystem.engine.assistant.context.update(
            user_id,
            global_context=data.get("global_context"),
            application_context=data.get("application_context"),
            user_context=data.get("user_context"),
            organization_context=data.get("organization_context"),
            conversation_context=data.get("conversation_context"),
            task_context=data.get("task_context"),
        )
        return json_response(bundle.to_dict())
    except EcosystemError as exc:
        return _handle_error(exc)


async def memory_recall_handler(request: web.Request) -> web.Response:
    try:
        user_id = request.query.get("user_id") or _user_id(request)
        memories = ecosystem.engine.assistant.memory.recall(
            user_id,
            application_id=request.query.get("application_id", ""),
            query=request.query.get("q", ""),
        )
        return json_response({"memories": [m.to_dict() for m in memories]})
    except EcosystemError as exc:
        return _handle_error(exc)
