"""Candidate identity matching — never collapses leads; never merges ambiguous people."""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.whatsapp_ops import normalize_phone, phones_match

APPLICATION_SNAPSHOT_KEYS = (
    "name",
    "email",
    "phone",
    "source",
    "campaign_id",
    "vacancy_id",
    "vacancy",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "first_touch_source",
    "first_touch_medium",
    "first_touch_campaign",
    "last_touch_source",
    "last_touch_medium",
    "last_touch_campaign",
    "external_id",
    "idempotency_key",
    "submitted_at",
    "created_at",
    "program_of_interest",
    "unit_of_interest",
    "application_message",
    "gclid",
    "fbclid",
    "click_id",
    "referrer",
    "landing_page",
    "project_key",
)


def _txt(value: Any) -> str:
    return str(value or "").strip()


def normalize_email(value: Any) -> str:
    return _txt(value).lower()


def identity_lock_key(organization_id: str, email: Any, phone: Any) -> str:
    mail = normalize_email(email)
    phone_n = normalize_phone(_txt(phone))
    return f"{organization_id}:{mail}:{phone_n}"


def identity_decision(left: dict[str, Any], right: dict[str, Any]) -> str:
    """Return match | ambiguous | distinct. Name is never an identity key."""
    email_a, email_b = normalize_email(left.get("email")), normalize_email(right.get("email"))
    phone_a_n = normalize_phone(_txt(left.get("phone")))
    phone_b_n = normalize_phone(_txt(right.get("phone")))
    email_same = bool(email_a and email_b and email_a == email_b)
    phone_same = bool(phone_a_n and phone_b_n and phones_match(_txt(left.get("phone")), _txt(right.get("phone"))))
    if email_same and phone_same:
        return "match"
    if email_same and not phone_a_n and not phone_b_n:
        return "match"
    if phone_same and not email_a and not email_b:
        return "match"
    if email_same or phone_same:
        return "ambiguous"
    return "distinct"


def application_snapshot(lead: dict[str, Any]) -> dict[str, Any]:
    snap: dict[str, Any] = {"lead_id": _txt(lead.get("id"))}
    for key in APPLICATION_SNAPSHOT_KEYS:
        if key in lead and lead.get(key) not in (None, ""):
            snap[key] = lead.get(key)
    return snap


def merge_safety(left: dict[str, Any], right: dict[str, Any]) -> str:
    """match | ambiguous | unsafe. Distinct identities are unsafe, never auto-merged."""
    decision = identity_decision(left, right)
    if decision == "distinct":
        return "unsafe"
    return decision


def is_merged_candidate(item: dict[str, Any] | None) -> bool:
    if not item:
        return False
    return bool(item.get("merged") or item.get("merged_into") or str(item.get("status") or "").upper() == "MERGED")


STAGE_RANK = {
    "NEW": 0,
    "QUALIFIED": 1,
    "INTERVIEW": 2,
    "APPROVED": 3,
    "HIRED": 4,
    "REJECTED": -1,
}


def advanced_pipeline_stage(left: dict[str, Any], right: dict[str, Any]) -> str:
    a = str(left.get("pipeline_stage") or left.get("status") or "NEW").upper()
    b = str(right.get("pipeline_stage") or right.get("status") or "NEW").upper()
    ra, rb = STAGE_RANK.get(a, 0), STAGE_RANK.get(b, 0)
    if ra == rb:
        return a if a in STAGE_RANK else b
    if ra > rb:
        return a
    return b


def union_ids(*groups: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for raw in group or []:
            value = _txt(raw)
            if not value or value in seen:
                continue
            seen.add(value)
            out.append(value)
    return out


def merge_application_snapshots(*groups: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for group in groups:
        for app in group or []:
            if not isinstance(app, dict):
                continue
            lid = _txt(app.get("lead_id"))
            key = lid or _txt(app.get("external_id")) or str(len(out))
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(app))
    return out


def detect_duplicate_groups(candidates: list[dict[str, Any]]) -> list[list[str]]:
    """Active candidates that share normalized email AND phone. Never auto-merges."""
    active = [item for item in candidates if item and not is_merged_candidate(item)]
    used: set[str] = set()
    groups: list[list[str]] = []
    for index, left in enumerate(active):
        left_id = _txt(left.get("id"))
        if not left_id or left_id in used:
            continue
        peers = [left_id]
        for right in active[index + 1 :]:
            right_id = _txt(right.get("id"))
            if not right_id or right_id in used:
                continue
            if identity_decision(left, right) == "match":
                peers.append(right_id)
        if len(peers) > 1:
            used.update(peers)
            groups.append(peers)
    return groups


def merge_text(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        text = _txt(value)
        if not text:
            continue
        if any(text == existing or text in existing for existing in parts):
            continue
        parts.append(text)
    return "\n".join(parts)


def annotate_duplicate_flags(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = detect_duplicate_groups(candidates)
    peers: dict[str, list[str]] = {}
    for group in groups:
        for cid in group:
            peers[cid] = [other for other in group if other != cid]
    out: list[dict[str, Any]] = []
    for item in candidates:
        row = dict(item)
        cid = _txt(row.get("id"))
        dupes = peers.get(cid) or []
        row["possible_duplicate"] = bool(dupes)
        row["duplicate_candidate_ids"] = dupes
        out.append(row)
    return out


def build_merge_preview(canonical: dict[str, Any], duplicate: dict[str, Any]) -> dict[str, Any]:
    apps = merge_application_snapshots(canonical.get("applications"), duplicate.get("applications"))
    lead_ids = union_ids(linked_lead_ids(canonical), linked_lead_ids(duplicate))
    have = {_txt(app.get("lead_id")) for app in apps}
    for lid in lead_ids:
        if lid and lid not in have:
            apps.append({"lead_id": lid})
            have.add(lid)
    sources = union_ids(
        [canonical.get("source")],
        [duplicate.get("source")],
        [app.get("source") for app in apps],
    )
    vacancies = union_ids(
        [canonical.get("vacancy_id"), canonical.get("vacancy")],
        [duplicate.get("vacancy_id"), duplicate.get("vacancy")],
        [app.get("vacancy_id") for app in apps],
        [app.get("vacancy") for app in apps],
        canonical.get("vacancy_ids"),
        duplicate.get("vacancy_ids"),
    )
    dates = [
        _txt(canonical.get("created_at") or canonical.get("submitted_at")),
        _txt(duplicate.get("created_at") or duplicate.get("submitted_at")),
        *[_txt(app.get("created_at") or app.get("submitted_at")) for app in apps],
    ]
    dates = [d for d in dates if d]
    assignee = _txt(canonical.get("assignee")) or _txt(duplicate.get("assignee"))
    return {
        "name": _txt(canonical.get("name")) or _txt(duplicate.get("name")),
        "application_count": len(apps) or len(lead_ids),
        "lead_count": len(lead_ids),
        "pipeline_stage": advanced_pipeline_stage(canonical, duplicate),
        "assignee": assignee,
        "source_count": len(sources),
        "sources": sources,
        "vacancies": vacancies,
        "first_application_at": min(dates) if dates else "",
        "last_application_at": max(dates) if dates else "",
        "email": normalize_email(canonical.get("email") or duplicate.get("email")),
        "phone": _txt(canonical.get("phone") or duplicate.get("phone")),
    }


def linked_lead_ids(candidate: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for raw in list(candidate.get("lead_ids") or []) + [_txt(candidate.get("lead_id"))]:
        lid = _txt(raw)
        if not lid or lid in seen:
            continue
        seen.add(lid)
        ids.append(lid)
    for app in candidate.get("applications") or []:
        lid = _txt(app.get("lead_id") if isinstance(app, dict) else "")
        if lid and lid not in seen:
            seen.add(lid)
            ids.append(lid)
    return ids
