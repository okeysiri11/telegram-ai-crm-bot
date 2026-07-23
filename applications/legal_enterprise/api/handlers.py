"""API handlers — Legal Enterprise (Sprint 17.0)."""

from __future__ import annotations

from aiohttp import web

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.middleware import json_response
from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError


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


async def health_handler(request: web.Request) -> web.Response:
    return json_response(legal_enterprise.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(legal_enterprise.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def registry_handler(request: web.Request) -> web.Response:
    try:
        registry = legal_enterprise.registry
        if request.method == "GET":
            return json_response(registry.status())
        body = await _read_json(request)
        action = body.get("action", "entity")
        if action == "individual":
            return json_response(
                registry.register_individual(
                    full_name=body.get("full_name", ""),
                    national_id=body.get("national_id", ""),
                    residency=body.get("residency", ""),
                ),
                status=201,
            )
        if action == "attorney":
            specs = body.get("specializations") if isinstance(body.get("specializations"), list) else None
            return json_response(
                registry.register_attorney(
                    full_name=body.get("full_name", ""),
                    bar_number=body.get("bar_number", ""),
                    firm=body.get("firm", ""),
                    specializations=specs,
                ),
                status=201,
            )
        if action == "judge":
            return json_response(
                registry.register_judge(
                    full_name=body.get("full_name", ""),
                    court_id=body.get("court_id", ""),
                    title=body.get("title", "Judge"),
                ),
                status=201,
            )
        if action == "agency":
            return json_response(
                registry.register_agency(
                    name=body.get("name", ""),
                    agency_type=body.get("agency_type", "ministry"),
                    country=body.get("country", ""),
                ),
                status=201,
            )
        if action == "role":
            return json_response(
                registry.register_role(
                    role_code=body.get("role_code", ""),
                    label=body.get("label", ""),
                    description=body.get("description", ""),
                ),
                status=201,
            )
        return json_response(
            registry.register_entity(
                name=body.get("name", ""),
                entity_type=body.get("entity_type", "corporation"),
                jurisdiction=body.get("jurisdiction", ""),
                registration_no=body.get("registration_no", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def legislation_handler(request: web.Request) -> web.Response:
    try:
        legislation = legal_enterprise.legislation
        if request.method == "GET":
            return json_response(legislation.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "version":
            return json_response(
                legislation.record_version(
                    legislation_id=body.get("legislation_id", ""),
                    version=body.get("version", ""),
                    change_summary=body.get("change_summary", ""),
                    legislation_type=body.get("legislation_type", ""),
                ),
                status=201,
            )
        kwargs = {
            "title": body.get("title", ""),
            "code": body.get("code", ""),
            "jurisdiction": body.get("jurisdiction", ""),
            "enacted_on": body.get("enacted_on", ""),
            "articles": int(body.get("articles", 0) or 0),
        }
        mapping = {
            "constitution": legislation.register_constitution,
            "civil": legislation.register_civil_code,
            "commercial": legislation.register_commercial_code,
            "criminal": legislation.register_criminal_code,
            "administrative": legislation.register_administrative_code,
            "tax": legislation.register_tax_code,
            "labor": legislation.register_labor_code,
            "treaty": legislation.register_treaty,
        }
        if action in mapping:
            return json_response(mapping[action](**kwargs), status=201)
        return json_response(
            legislation.register(
                legislation_type=body.get("legislation_type", "civil"),
                **kwargs,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def courts_handler(request: web.Request) -> web.Response:
    try:
        courts = legal_enterprise.courts
        if request.method == "GET":
            return json_response(courts.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "regional":
            return json_response(
                courts.register_regional(
                    name=body.get("name", ""),
                    region=body.get("region", ""),
                    jurisdiction_code=body.get("jurisdiction_code", ""),
                ),
                status=201,
            )
        if action == "appeal":
            return json_response(
                courts.register_appeal(
                    name=body.get("name", ""),
                    region=body.get("region", ""),
                    jurisdiction_code=body.get("jurisdiction_code", ""),
                ),
                status=201,
            )
        if action == "supreme":
            return json_response(
                courts.register_supreme(
                    name=body.get("name", ""),
                    jurisdiction_code=body.get("jurisdiction_code", "national"),
                ),
                status=201,
            )
        if action == "hierarchy":
            return json_response(
                courts.define_hierarchy(
                    lower_court_id=body.get("lower_court_id", ""),
                    higher_court_id=body.get("higher_court_id", ""),
                    relation=body.get("relation", "appeals_to"),
                ),
                status=201,
            )
        if action == "jurisdiction":
            return json_response(
                courts.register_jurisdiction(
                    code=body.get("code", ""),
                    name=body.get("name", ""),
                    territory=body.get("territory", ""),
                    court_id=body.get("court_id", ""),
                ),
                status=201,
            )
        if action == "category":
            return json_response(
                courts.register_case_category(
                    code=body.get("code", ""),
                    name=body.get("name", ""),
                    description=body.get("description", ""),
                ),
                status=201,
            )
        return json_response(
            courts.register_court(
                name=body.get("name", ""),
                level=body.get("level", "regional"),
                region=body.get("region", ""),
                jurisdiction_code=body.get("jurisdiction_code", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cases_handler(request: web.Request) -> web.Response:
    try:
        cases = legal_enterprise.cases
        if request.method == "GET":
            return json_response(cases.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "status":
            return json_response(
                cases.set_status(
                    case_id=body.get("case_id", ""),
                    status=body.get("status", "filed"),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        if action == "timeline":
            return json_response(
                cases.add_timeline_event(
                    case_id=body.get("case_id", ""),
                    event=body.get("event", ""),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "participant":
            return json_response(
                cases.add_participant(
                    case_id=body.get("case_id", ""),
                    role_code=body.get("role_code", ""),
                    party_name=body.get("party_name", ""),
                    party_ref=body.get("party_ref", ""),
                ),
                status=201,
            )
        if action == "document":
            return json_response(
                cases.register_document(
                    case_id=body.get("case_id", ""),
                    title=body.get("title", ""),
                    document_type=body.get("document_type", "filing"),
                    uri=body.get("uri", ""),
                ),
                status=201,
            )
        if action == "evidence":
            return json_response(
                cases.register_evidence(
                    case_id=body.get("case_id", ""),
                    label=body.get("label", ""),
                    evidence_type=body.get("evidence_type", "exhibit"),
                    description=body.get("description", ""),
                ),
                status=201,
            )
        if action == "task":
            return json_response(
                cases.create_task(
                    case_id=body.get("case_id", ""),
                    title=body.get("title", ""),
                    assignee=body.get("assignee", ""),
                    due_on=body.get("due_on", ""),
                ),
                status=201,
            )
        if action == "note":
            return json_response(
                cases.add_note(
                    case_id=body.get("case_id", ""),
                    author=body.get("author", ""),
                    body=body.get("body", ""),
                ),
                status=201,
            )
        return json_response(
            cases.register_case(
                title=body.get("title", ""),
                case_number=body.get("case_number", ""),
                court_id=body.get("court_id", ""),
                category_code=body.get("category_code", ""),
                status=body.get("status", "draft"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dashboard_handler(request: web.Request) -> web.Response:
    try:
        dtype = request.rel_url.query.get("type", "legal")
        if request.method == "POST":
            body = await _read_json(request)
            dtype = body.get("dashboard_type", dtype)
        return json_response(legal_enterprise.dashboard.render(dashboard_type=dtype))
    except Exception as exc:
        return _handle_error(exc)


async def knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = legal_enterprise.knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "relate":
            return json_response(
                knowledge.relate(
                    from_base=body.get("from_base", ""),
                    from_key=body.get("from_key", ""),
                    to_base=body.get("to_base", ""),
                    to_key=body.get("to_key", ""),
                    relation=body.get("relation", "related_to"),
                ),
                status=201,
            )
        return json_response(
            knowledge.publish(
                base=body.get("base", ""),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
