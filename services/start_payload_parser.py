# Start payload parser — deep link codes, UTM and referral extraction.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StartPayload:
    link_code: str | None = None
    utm_source: str | None = None
    utm_campaign: str | None = None
    utm_medium: str | None = None
    referral_code: str | None = None


_UTM_KEYS = {
    "utm_source": "utm_source",
    "utm_campaign": "utm_campaign",
    "utm_medium": "utm_medium",
    "us": "utm_source",
    "uc": "utm_campaign",
    "um": "utm_medium",
}


def parse_start_payload(args: str | None) -> StartPayload:
    if not args:
        return StartPayload()

    text = args.strip()
    if not text:
        return StartPayload()

    tokens = text.split()
    base = tokens[0].lower()
    payload = StartPayload()

    if "-ref-" in base:
        link_part, ref_part = base.split("-ref-", 1)
        payload.link_code = link_part or None
        payload.referral_code = ref_part or None
        base = link_part

    segments = base.split("__")
    payload.link_code = payload.link_code or segments[0] or None

    for segment in segments[1:]:
        _apply_segment(payload, segment)

    for token in tokens[1:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if key in _UTM_KEYS:
            setattr(payload, _UTM_KEYS[key], value)
        elif key == "ref" and value:
            payload.referral_code = value

    return payload


def _apply_segment(payload: StartPayload, segment: str) -> None:
    for prefix, field in (
        ("utm_source_", "utm_source"),
        ("utm_campaign_", "utm_campaign"),
        ("utm_medium_", "utm_medium"),
        ("ref_", "referral_code"),
    ):
        if segment.startswith(prefix):
            setattr(payload, field, segment[len(prefix):] or None)
            return

    if segment.startswith("utm_"):
        parts = segment.split("_", 2)
        if len(parts) == 3 and parts[1] in {"source", "campaign", "medium"}:
            setattr(payload, f"utm_{parts[1]}", parts[2] or None)
