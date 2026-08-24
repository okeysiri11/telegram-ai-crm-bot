"""Legal external data providers — Sprint Lawyer 3.3.

CRITICAL: Do not simulate Ukrainian government registries as live APIs.
Providers expose honest status: CONNECTED / REQUIRES_CONFIGURATION / MANUAL / UNAVAILABLE / ERROR.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol

PROVIDER_STATUSES = (
    "CONNECTED",
    "REQUIRES_CONFIGURATION",
    "MANUAL",
    "UNAVAILABLE",
    "ERROR",
)


class LegalDataProvider(Protocol):
    provider_id: str

    def status(self) -> dict[str, Any]: ...

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]: ...

    def get_case(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]: ...

    def get_decisions(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]: ...

    def get_events(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]: ...

    def get_enforcement(self, production_number: str, **kwargs: Any) -> dict[str, Any]: ...

    def check_updates(self, watch_item: dict[str, Any]) -> dict[str, Any]: ...


def _base_status(
    *,
    provider_id: str,
    label_ru: str,
    status: str,
    message_ru: str,
    official_source: str,
    access_mode: str,
    limitations: list[str],
    authentication: str,
    rate_limits: str,
) -> dict[str, Any]:
    return {
        "provider": provider_id,
        "label_ru": label_ru,
        "status": status,
        "message_ru": message_ru,
        "official_source": official_source,
        "access_mode": access_mode,
        "authentication": authentication,
        "rate_limits": rate_limits,
        "limitations": limitations,
        "automatic_integration": status == "CONNECTED",
        "ready": status == "CONNECTED",
        "implemented": True,
    }


class ManualImportProvider:
    """Manual / import workflow — always available for lawyer-entered data."""

    provider_id = "manual_import"

    def status(self) -> dict[str, Any]:
        return _base_status(
            provider_id=self.provider_id,
            label_ru="Ручной ввод / импорт",
            status="MANUAL",
            message_ru="Автоматическая интеграция недоступна / требует подключения. Используйте ручной импорт состояния.",
            official_source="Lawyer-provided documents and metadata",
            access_mode="manual",
            authentication="ADOS RBAC",
            rate_limits="n/a",
            limitations=[
                "Нет автоматической выгрузки из государственных реестров",
                "Юрист отвечает за актуальность импортированных данных",
            ],
        )

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "ok": True,
            "provider": self.provider_id,
            "items": [],
            "message_ru": "Поиск во внешних реестрах недоступен — используйте ручной импорт",
        }

    def get_case(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]:
        imported = kwargs.get("imported_state")
        if not imported:
            return {
                "ok": False,
                "provider": self.provider_id,
                "status": "MANUAL",
                "message_ru": "Нет импортированного состояния. Загрузите снимок вручную.",
            }
        return {"ok": True, "provider": self.provider_id, "item": imported}

    def get_decisions(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]:
        imported = kwargs.get("imported_state") or {}
        return {"ok": True, "provider": self.provider_id, "items": imported.get("decisions") or []}

    def get_events(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]:
        imported = kwargs.get("imported_state") or {}
        return {"ok": True, "provider": self.provider_id, "items": imported.get("events") or []}

    def get_enforcement(self, production_number: str, **kwargs: Any) -> dict[str, Any]:
        imported = kwargs.get("imported_state")
        if not imported:
            return {
                "ok": False,
                "provider": self.provider_id,
                "message_ru": "Нет импортированного ИП — заполните вручную",
            }
        return {"ok": True, "provider": self.provider_id, "item": imported}

    def check_updates(self, watch_item: dict[str, Any]) -> dict[str, Any]:
        """Compare imported_state fingerprint; does not invent court data."""
        state = watch_item.get("imported_state") or watch_item.get("payload", {}).get("imported_state")
        if not state:
            return {
                "ok": True,
                "provider": self.provider_id,
                "changed": False,
                "status": "MANUAL",
                "message_ru": "Автоматическая проверка внешней системы недоступна. Импортируйте состояние вручную.",
                "fingerprint": watch_item.get("fingerprint"),
                "normalized": None,
            }
        normalized = normalize_external_state(state, provider=self.provider_id)
        fp = fingerprint_state(normalized)
        prev = watch_item.get("fingerprint")
        changed = bool(prev) and prev != fp
        return {
            "ok": True,
            "provider": self.provider_id,
            "changed": changed or (not prev and bool(state)),
            "fingerprint": fp,
            "normalized": normalized,
            "status": "MANUAL",
            "message_ru": "Состояние обновлено из ручного импорта" if changed or not prev else "Изменений нет",
        }


class EdrrsUnavailableProvider:
    """Ukrainian court decisions register — no public automated API claimed."""

    provider_id = "ua_edrsr"

    def status(self) -> dict[str, Any]:
        return _base_status(
            provider_id=self.provider_id,
            label_ru="ЄДРСР (реєстр судових рішень)",
            status="UNAVAILABLE",
            message_ru="Источник не подключен. Для автоматического обновления требуется официальный или лицензированный источник данных.",
            official_source="https://reyestr.court.gov.ua/ (Единый государственный реестр судебных решений)",
            access_mode="web / commercial or partner API if contracted",
            authentication="Требуется официальный доступ / договор — не реализован",
            rate_limits="Неизвестны без договора",
            limitations=[
                "Не имитируем ответы реестра",
                "Скрапинг сайта без разрешения не используется",
                "Используйте manual_import для сохранения найденных решений",
            ],
        )

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("search")

    def get_case(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("get_case")

    def get_decisions(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("get_decisions")

    def get_events(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("get_events")

    def get_enforcement(self, production_number: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("get_enforcement")

    def check_updates(self, watch_item: dict[str, Any]) -> dict[str, Any]:
        st = self.status()
        return {
            "ok": False,
            "provider": self.provider_id,
            "changed": False,
            "status": st["status"],
            "message_ru": st["message_ru"],
            "error": "provider_unavailable",
        }

    def _blocked(self, op: str) -> dict[str, Any]:
        st = self.status()
        return {
            "ok": False,
            "provider": self.provider_id,
            "operation": op,
            "status": st["status"],
            "message_ru": st["message_ru"],
        }


class EnforcementUnavailableProvider:
    """Enforcement proceedings — honest unavailable until official API."""

    provider_id = "ua_enforcement"

    def status(self) -> dict[str, Any]:
        return _base_status(
            provider_id=self.provider_id,
            label_ru="Исполнительные производства (АСВП / открытые данные)",
            status="REQUIRES_CONFIGURATION",
            message_ru="Источник не подключен. Для автоматического обновления требуется официальный или лицензированный источник данных.",
            official_source="Официальные порталы исполнительного производства / open data (при наличии лицензии)",
            access_mode="API или open data — не подключено",
            authentication="Требуется конфигурация провайдера",
            rate_limits="n/a до подключения",
            limitations=[
                "Модуль ИП в Legal Ops работает в manual/import режиме",
                "Не выдаём выдуманные статусы исполнителя",
            ],
        )

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("search")

    def get_case(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("get_case")

    def get_decisions(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("get_decisions")

    def get_events(self, external_case_number: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("get_events")

    def get_enforcement(self, production_number: str, **kwargs: Any) -> dict[str, Any]:
        return self._blocked("get_enforcement")

    def check_updates(self, watch_item: dict[str, Any]) -> dict[str, Any]:
        st = self.status()
        return {
            "ok": False,
            "provider": self.provider_id,
            "changed": False,
            "status": st["status"],
            "message_ru": st["message_ru"],
            "error": "requires_configuration",
        }

    def _blocked(self, op: str) -> dict[str, Any]:
        st = self.status()
        return {
            "ok": False,
            "provider": self.provider_id,
            "operation": op,
            "status": st["status"],
            "message_ru": st["message_ru"],
        }


def normalize_external_state(state: dict[str, Any], *, provider: str) -> dict[str, Any]:
    """Normalize imported/provider payload for fingerprinting."""
    events = state.get("events") or state.get("hearings") or []
    docs = state.get("documents") or state.get("decisions") or []
    return {
        "provider": provider,
        "external_case_number": str(state.get("external_case_number") or state.get("case_number") or ""),
        "status": str(state.get("status") or ""),
        "events": sorted(
            [
                {
                    "title": str(e.get("title") or ""),
                    "starts_at": str(e.get("starts_at") or e.get("scheduled_at") or ""),
                    "kind": str(e.get("kind") or e.get("event_type") or "hearing"),
                }
                for e in events
                if isinstance(e, dict)
            ],
            key=lambda x: (x["starts_at"], x["title"]),
        ),
        "documents": sorted(
            [
                {
                    "title": str(d.get("title") or ""),
                    "external_id": str(d.get("external_id") or d.get("id") or ""),
                    "url": str(d.get("url") or d.get("source_url") or ""),
                    "date": str(d.get("date") or d.get("document_date") or ""),
                }
                for d in docs
                if isinstance(d, dict)
            ],
            key=lambda x: (x["external_id"], x["title"]),
        ),
        "enforcement_status": str(state.get("enforcement_status") or state.get("status") or ""),
        "notes": str(state.get("notes") or ""),
    }


def fingerprint_state(normalized: dict[str, Any]) -> str:
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def diff_states(prev: dict[str, Any] | None, curr: dict[str, Any]) -> list[dict[str, Any]]:
    """Return structured change records (real diffs only)."""
    changes: list[dict[str, Any]] = []
    prev = prev or {}
    if str(prev.get("status") or "") != str(curr.get("status") or ""):
        changes.append(
            {
                "change_type": "status",
                "title": "Изменён статус",
                "detail": {"from": prev.get("status"), "to": curr.get("status")},
            }
        )
    prev_events = {(e["starts_at"], e["title"]): e for e in (prev.get("events") or [])}
    for e in curr.get("events") or []:
        key = (e["starts_at"], e["title"])
        if key not in prev_events:
            changes.append(
                {
                    "change_type": "hearing",
                    "title": "Новое заседание",
                    "detail": e,
                }
            )
    prev_docs = {(d["external_id"], d["title"]): d for d in (prev.get("documents") or [])}
    for d in curr.get("documents") or []:
        key = (d["external_id"], d["title"])
        if key not in prev_docs:
            changes.append(
                {
                    "change_type": "document",
                    "title": "Добавлен судебный документ",
                    "detail": d,
                }
            )
    if str(prev.get("enforcement_status") or "") != str(curr.get("enforcement_status") or "") and (
        prev.get("enforcement_status") or curr.get("enforcement_status")
    ):
        changes.append(
            {
                "change_type": "enforcement_status",
                "title": "Изменён статус исполнительного производства",
                "detail": {"from": prev.get("enforcement_status"), "to": curr.get("enforcement_status")},
            }
        )
    return changes


class LegalDataProviderRegistry:
    def __init__(self) -> None:
        self.manual = ManualImportProvider()
        self.edrsr = EdrrsUnavailableProvider()
        self.enforcement = EnforcementUnavailableProvider()

    def catalog(self) -> list[dict[str, Any]]:
        return [self.manual.status(), self.edrsr.status(), self.enforcement.status()]

    def get(self, provider_id: str | None) -> LegalDataProvider:
        pid = (provider_id or "manual_import").lower()
        if pid in {"ua_edrsr", "edrsr", "court_decisions"}:
            return self.edrsr
        if pid in {"ua_enforcement", "enforcement", "asvp"}:
            return self.enforcement
        return self.manual


_REG: LegalDataProviderRegistry | None = None


def get_legal_data_providers() -> LegalDataProviderRegistry:
    global _REG
    if _REG is None:
        _REG = LegalDataProviderRegistry()
    return _REG
