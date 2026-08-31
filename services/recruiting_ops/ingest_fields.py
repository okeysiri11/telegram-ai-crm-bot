"""Parse Vanguard application fields for HMAC ingest without changing auth."""

from __future__ import annotations

from typing import Any

from services.recruiting_ops.whatsapp_ops import normalize_phone

AGE_MIN = 18
AGE_MAX = 99

TRUE_TOKENS = {"true", "yes", "1"}
FALSE_TOKENS = {"false", "no", "0"}


class ApplicationFieldError(ValueError):
    def __init__(self, message_ru: str) -> None:
        super().__init__(message_ru)
        self.message_ru = message_ru


def _txt(value: Any) -> str:
    return str(value or "").strip()


def validation_error(message_ru: str) -> dict[str, Any]:
    return {"ok": False, "error": "validation", "message_ru": message_ru}


def parse_age(value: Any, *, present: bool) -> int | None:
    if not present or value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ApplicationFieldError(f"Возраст должен быть целым числом от {AGE_MIN} до {AGE_MAX}")
    if isinstance(value, int):
        age = value
    elif isinstance(value, float):
        if not value.is_integer():
            raise ApplicationFieldError(f"Возраст должен быть целым числом от {AGE_MIN} до {AGE_MAX}")
        age = int(value)
    else:
        raw = _txt(value)
        if not raw:
            return None
        try:
            if isinstance(value, str) and "." in raw:
                as_float = float(raw)
                if not as_float.is_integer():
                    raise ApplicationFieldError(
                        f"Возраст должен быть целым числом от {AGE_MIN} до {AGE_MAX}"
                    )
                age = int(as_float)
            else:
                age = int(raw)
        except (TypeError, ValueError) as exc:
            raise ApplicationFieldError(
                f"Возраст должен быть целым числом от {AGE_MIN} до {AGE_MAX}"
            ) from exc
    if age < AGE_MIN or age > AGE_MAX:
        raise ApplicationFieldError(f"Возраст должен быть от {AGE_MIN} до {AGE_MAX}")
    return age


def parse_contact_consent(body: dict[str, Any]) -> bool | None:
    """Preserve exact submitted boolean. Never default True when omitted."""
    if "contact_consent" not in body:
        return None
    value = body.get("contact_consent")
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value in (0, 1):
        return bool(int(value))
    token = _txt(value).lower()
    if token in TRUE_TOKENS:
        return True
    if token in FALSE_TOKENS:
        return False
    raise ApplicationFieldError("Поле contact_consent должно быть true или false")


def persist_phone(value: Any) -> str | None:
    raw = _txt(value)
    if not raw:
        return None
    normalized = normalize_phone(raw)
    return normalized or raw


def extract_click_ids(body: dict[str, Any]) -> dict[str, str | None]:
    """Keep gclid / fbclid / click_id as separate values. Do not collapse ads ids."""
    return {
        "gclid": _txt(body.get("gclid")) or None,
        "fbclid": _txt(body.get("fbclid")) or None,
        "click_id": _txt(body.get("click_id")) or None,
    }


def parse_application_fields(body: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        clicks = extract_click_ids(body)
        fields = {
            "age": parse_age(body.get("age"), present="age" in body),
            "contact_consent": parse_contact_consent(body),
            "phone": persist_phone(body.get("phone")),
            "gclid": clicks["gclid"],
            "fbclid": clicks["fbclid"],
            "click_id": clicks["click_id"],
        }
        return fields, None
    except ApplicationFieldError as exc:
        return None, validation_error(exc.message_ru)


def _consent_unset(existing: dict[str, Any]) -> bool:
    return existing.get("contact_consent") is None


def fill_missing_application_fields(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """On duplicate retry, fill previously empty candidate/attribution fields only."""
    patch: dict[str, Any] = {}
    if existing.get("age") is None and incoming.get("age") is not None:
        patch["age"] = incoming["age"]
    if _consent_unset(existing) and incoming.get("contact_consent") is not None:
        patch["contact_consent"] = incoming.get("contact_consent")
    if not _txt(existing.get("phone")) and incoming.get("phone"):
        patch["phone"] = incoming["phone"]
    for key in ("gclid", "fbclid", "click_id"):
        if not _txt(existing.get(key)) and _txt(incoming.get(key)):
            patch[key] = incoming.get(key)
    return patch


def application_fields_from_lead(lead: dict[str, Any]) -> dict[str, Any]:
    return {
        "age": lead.get("age"),
        "contact_consent": lead.get("contact_consent"),
        "phone": lead.get("phone"),
        "source": lead.get("source"),
        "project_key": lead.get("project_key"),
        "utm_source": lead.get("utm_source"),
        "utm_medium": lead.get("utm_medium"),
        "utm_campaign": lead.get("utm_campaign"),
        "utm_content": lead.get("utm_content"),
        "utm_term": lead.get("utm_term"),
        "gclid": lead.get("gclid"),
        "fbclid": lead.get("fbclid"),
        "click_id": lead.get("click_id"),
        "country": lead.get("country"),
        "preferred_language": lead.get("preferred_language"),
        "unit_of_interest": lead.get("unit_of_interest"),
        "program_of_interest": lead.get("program_of_interest"),
        "application_message": lead.get("application_message"),
    }
