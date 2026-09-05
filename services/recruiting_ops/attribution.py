"""First-touch / last-touch attribution for Vanguard leads."""

from __future__ import annotations

from typing import Any

TEST_TRAFFIC_CLASS = "TEST"
PRODUCTION_TRAFFIC_CLASS = "PRODUCTION"
TEST_TRAFFIC_MARKERS = (
    "e2e_test",
    "e2e-historical",
    "vanguard_e2e",
    "e2e-",
    "vanguard_pre_ads_test",
    "pre_ads_test",
)
_TEST_TRAFFIC_FIELDS = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "source",
    "first_touch_source",
    "first_touch_campaign",
    "last_touch_source",
    "last_touch_campaign",
    "campaign_code",
    "external_id",
    "traffic_class",
    "data_mode",
)


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _blob_is_test(item: dict[str, Any]) -> bool:
    if bool(item.get("is_test_traffic")):
        return True
    cls = _txt(item.get("traffic_class")).upper()
    if cls in {TEST_TRAFFIC_CLASS, "E2E"}:
        return True
    if _txt(item.get("data_mode")).upper() == TEST_TRAFFIC_CLASS:
        return True
    blob = " ".join(_txt(item.get(key)).lower() for key in _TEST_TRAFFIC_FIELDS)
    return any(marker in blob for marker in TEST_TRAFFIC_MARKERS)


def is_test_traffic(item: dict[str, Any] | None) -> bool:
    """True for E2E / TEST-tagged rows. Operational lists keep them; analytics drop them."""
    if not item:
        return False
    if _blob_is_test(item):
        return True
    for app in item.get("applications") or []:
        if isinstance(app, dict) and _blob_is_test(app):
            return True
    return False


def candidate_is_test_traffic(candidate: dict[str, Any] | None, test_lead_ids: set[str] | None = None) -> bool:
    if is_test_traffic(candidate):
        return True
    lids = { _txt((candidate or {}).get("lead_id")) }
    lids.update(_txt(x) for x in ((candidate or {}).get("lead_ids") or []) if x)
    lids.discard("")
    return bool(test_lead_ids and lids & test_lead_ids)


def classify_traffic(item: dict[str, Any] | None) -> str:
    return TEST_TRAFFIC_CLASS if is_test_traffic(item) else PRODUCTION_TRAFFIC_CLASS


def production_cohort(
    leads: list[dict[str, Any]],
    candidates: list[dict[str, Any]] | None = None,
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    prod_leads = [item for item in leads if not is_test_traffic(item)]
    test_lead_ids = { _txt(item.get("id")) for item in leads if is_test_traffic(item) }
    test_lead_ids.discard("")
    prod_cands = None
    if candidates is not None:
        prod_cands = [item for item in candidates if not candidate_is_test_traffic(item, test_lead_ids)]
    prod_events = None
    if events is not None:
        prod_events = [item for item in events if not is_test_traffic(item)]
    return {
        "leads": prod_leads,
        "candidates": prod_cands,
        "events": prod_events,
        "production_only": True,
        "excluded_test_leads": len(leads) - len(prod_leads),
        "excluded_test_candidates": (len(candidates) - len(prod_cands)) if candidates is not None else 0,
        "excluded_test_events": (len(events) - len(prod_events)) if events is not None else 0,
    }


def touch_payload(body: dict[str, Any]) -> dict[str, Any]:
    source = _txt(body.get("utm_source") or body.get("source")) or None
    medium = _txt(body.get("utm_medium") or body.get("medium")) or None
    campaign = _txt(body.get("utm_campaign") or body.get("campaign_code")) or None
    content = _txt(body.get("utm_content")) or None
    term = _txt(body.get("utm_term")) or None
    first_source = _txt(body.get("first_touch_source")) or source
    first_medium = _txt(body.get("first_touch_medium")) or medium
    first_campaign = _txt(body.get("first_touch_campaign")) or campaign
    return {
        "first_touch_source": first_source,
        "first_touch_medium": first_medium,
        "first_touch_campaign": first_campaign,
        "last_touch_source": source,
        "last_touch_medium": medium,
        "last_touch_campaign": campaign,
        "last_touch_content": content,
        "last_touch_term": term,
    }


def preserve_first_touch(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Last-touch updates; first-touch fields are never overwritten once set."""
    fresh = touch_payload(incoming)
    patch = {
        "last_touch_source": fresh["last_touch_source"],
        "last_touch_medium": fresh["last_touch_medium"],
        "last_touch_campaign": fresh["last_touch_campaign"],
        "last_touch_content": fresh["last_touch_content"],
        "last_touch_term": fresh["last_touch_term"],
        "utm_source": _txt(incoming.get("utm_source")) or existing.get("utm_source"),
        "utm_medium": _txt(incoming.get("utm_medium")) or existing.get("utm_medium"),
        "utm_campaign": _txt(incoming.get("utm_campaign")) or existing.get("utm_campaign"),
        "utm_content": _txt(incoming.get("utm_content")) or existing.get("utm_content"),
        "utm_term": _txt(incoming.get("utm_term")) or existing.get("utm_term"),
        "referrer": _txt(incoming.get("referrer")) or existing.get("referrer"),
        "landing_page": _txt(incoming.get("landing_page")) or existing.get("landing_page"),
        "gclid": _txt(incoming.get("gclid")) or existing.get("gclid"),
        "fbclid": _txt(incoming.get("fbclid")) or existing.get("fbclid"),
        "click_id": _txt(incoming.get("click_id")) or existing.get("click_id"),
    }
    for key in ("first_touch_source", "first_touch_medium", "first_touch_campaign"):
        if not _txt(existing.get(key)):
            patch[key] = fresh.get(key)
    return patch


def attribution_chain(lead: dict[str, Any], candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    stage = _txt((candidate or {}).get("pipeline_stage") or lead.get("pipeline_stage") or lead.get("status"))
    hire = stage.upper() == "HIRED" or _txt(lead.get("status")).lower() == "hired"
    interview = stage.upper() == "INTERVIEW" or hire
    qualified = _txt(lead.get("status")).lower() in {"qualified", "converted"} or interview
    return {
        "provider": _txt(lead.get("provider") or lead.get("utm_source") or lead.get("first_touch_source")) or None,
        "campaign": _txt(lead.get("utm_campaign") or lead.get("campaign_id") or lead.get("first_touch_campaign")) or None,
        "click_or_lead": _txt(
            lead.get("click_id") or lead.get("gclid") or lead.get("fbclid") or lead.get("external_id") or lead.get("id")
        )
        or None,
        "candidate": _txt((candidate or {}).get("id") or lead.get("candidate_id")) or None,
        "qualified": qualified,
        "interview": interview,
        "hire": hire,
        "first_touch": {
            "source": lead.get("first_touch_source"),
            "medium": lead.get("first_touch_medium"),
            "campaign": lead.get("first_touch_campaign"),
        },
        "last_touch": {
            "source": lead.get("last_touch_source"),
            "medium": lead.get("last_touch_medium"),
            "campaign": lead.get("last_touch_campaign"),
        },
        "multi_touch_ready": True,
    }


def source_analytics(leads: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    cand_ids = {_txt(item.get("lead_id")) for item in candidates}
    buckets: dict[str, dict[str, int]] = {}
    for lead in leads:
        src = _txt(lead.get("first_touch_source") or lead.get("utm_source") or lead.get("source")) or "unknown"
        bucket = buckets.setdefault(src, {"leads": 0, "candidates": 0})
        bucket["leads"] += 1
        if _txt(lead.get("id")) in cand_ids or _txt(lead.get("status")).lower() == "converted":
            bucket["candidates"] += 1
    rows = []
    for source, counts in sorted(buckets.items(), key=lambda x: (-x[1]["leads"], x[0])):
        leads_n = counts["leads"]
        cands_n = counts["candidates"]
        rows.append(
            {
                "source": source,
                "leads": leads_n,
                "candidates": cands_n,
                "conversion": round(cands_n / leads_n, 4) if leads_n else None,
            }
        )
    return {"items": rows, "has_data": bool(rows)}
