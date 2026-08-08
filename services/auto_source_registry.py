"""Sprint 46.1 — Auto Search Source Registry (Telegram + public web + dealer)."""

from __future__ import annotations

import copy
import threading
from typing import Any

from services.auto_source_models import AutoSourceConfig

# Built-in sources — never hardcode these inside conversation engine.
# Priority: lower number = higher rank weight (does NOT exclude others).
_BUILTIN: list[AutoSourceConfig] = [
    AutoSourceConfig(
        id="dealer_warehouse",
        name="Моя база",
        source_type="dealer_warehouse",
        source_url="internal://dealer_warehouse",
        enabled=True,
        priority=1,
        status="active",
        category="warehouse",
    ),
    AutoSourceConfig(
        id="tg_keepcar",
        name="KEEP CAR",
        source_type="telegram_channel",
        source_url="https://t.me/keepcar",
        enabled=True,
        priority=2,
        status="requires_configuration",
        category="telegram",
        searchable=True,
        region="Ukraine",
        metadata={"username": "keepcar"},
    ),
    AutoSourceConfig(
        id="tg_isauto99",
        name="IsAuto",
        source_type="telegram_channel",
        source_url="https://t.me/isAuto99",
        enabled=True,
        priority=2,
        status="requires_configuration",
        category="telegram",
        searchable=True,
        region="Ukraine",
        metadata={"username": "isAuto99"},
    ),
    AutoSourceConfig(
        id="tg_kievavto",
        name="KIEVAVTO",
        source_type="telegram_channel",
        source_url="https://t.me/KievavtoLocation",
        enabled=True,
        priority=2,
        status="requires_configuration",
        category="telegram",
        searchable=True,
        region="Kyiv / Ukraine",
        metadata={"username": "KievavtoLocation"},
    ),
    AutoSourceConfig(
        id="tg_avtosale_odessa777",
        name="avto_batya777",
        source_type="telegram_channel",
        source_url="https://t.me/avtosale_odessa777",
        enabled=True,
        priority=2,
        status="requires_configuration",
        category="telegram",
        searchable=True,
        region="Odessa / Ukraine",
        metadata={
            "username": "avtosale_odessa777",
            "resolved_name": "avto_batya777",
        },
    ),
    AutoSourceConfig(
        id="tg_imperiya_auto",
        name="Імперія Авто / Imperiya Auto",
        source_type="telegram_channel",
        source_url="https://t.me/imperiya_auto",
        enabled=True,
        priority=2,
        status="requires_configuration",
        category="telegram",
        searchable=True,
        region="Ukraine",
        metadata={"username": "imperiya_auto"},
    ),
    AutoSourceConfig(
        id="web_autoria",
        name="AUTO.RIA",
        source_type="public_web",
        source_url="https://auto.ria.com",
        enabled=True,
        priority=4,
        status="active",
        category="websites",
        searchable=True,
        metadata={"adapter": "autoria"},
    ),
    AutoSourceConfig(
        id="web_olx_auto",
        name="OLX Auto",
        source_type="public_web",
        source_url="https://www.olx.ua/transport/legkovye-avtomobili/",
        enabled=True,
        priority=4,
        status="active",
        category="websites",
        searchable=True,
        metadata={"adapter": "olx_auto"},
    ),
    AutoSourceConfig(
        id="web_rst",
        name="RST",
        source_type="public_web",
        source_url="https://rst.ua",
        enabled=True,
        priority=4,
        status="active",
        category="websites",
        searchable=True,
        metadata={"adapter": "rst"},
    ),
]


OWNER_SOURCE_SECTIONS = (
    ("warehouse", "Моя база"),
    ("telegram", "Telegram-каналы"),
    ("websites", "Автосайты"),
    ("extra", "Дополнительные источники"),
)


class AutoSourceRegistry:
    """Mutable registry: builtins + owner overrides. Thread-safe in-process store."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sources: dict[str, AutoSourceConfig] = {
            s.id: copy.deepcopy(s) for s in _BUILTIN
        }

    def list_all(self) -> list[AutoSourceConfig]:
        with self._lock:
            return sorted(
                (copy.deepcopy(s) for s in self._sources.values()),
                key=lambda s: (s.priority, s.name),
            )

    def list_enabled(self) -> list[AutoSourceConfig]:
        return [s for s in self.list_all() if s.enabled and s.searchable]

    def list_telegram_channels(self) -> list[AutoSourceConfig]:
        return [s for s in self.list_all() if s.source_type == "telegram_channel"]

    def telegram_pool_urls(self) -> list[str]:
        return [s.source_url for s in self.list_telegram_channels() if s.enabled]

    def get(self, source_id: str) -> AutoSourceConfig | None:
        with self._lock:
            s = self._sources.get(source_id)
            return copy.deepcopy(s) if s else None

    def set_enabled(self, source_id: str, enabled: bool) -> AutoSourceConfig | None:
        with self._lock:
            s = self._sources.get(source_id)
            if not s:
                return None
            s.enabled = bool(enabled)
            return copy.deepcopy(s)

    def set_priority(self, source_id: str, priority: int) -> AutoSourceConfig | None:
        with self._lock:
            s = self._sources.get(source_id)
            if not s:
                return None
            s.priority = int(priority)
            return copy.deepcopy(s)

    def set_status(self, source_id: str, status: str) -> AutoSourceConfig | None:
        with self._lock:
            s = self._sources.get(source_id)
            if not s:
                return None
            s.status = status
            return copy.deepcopy(s)

    def add_telegram_channel(
        self,
        *,
        name: str,
        url: str,
        source_id: str | None = None,
        enabled: bool = True,
        priority: int = 2,
        searchable: bool = True,
        region: str | None = None,
        resolved_name: str | None = None,
    ) -> AutoSourceConfig:
        """Owner Settings path — add Telegram channel without code changes."""
        username = url.rstrip("/").split("/")[-1]
        sid = source_id or f"tg_owner_{abs(hash(url)) % 10_000_000}"
        meta: dict[str, Any] = {"username": username}
        if resolved_name:
            meta["resolved_name"] = resolved_name
        cfg = AutoSourceConfig(
            id=sid,
            name=(resolved_name or name).strip() or sid,
            source_type="telegram_channel",
            source_url=url.strip(),
            enabled=enabled,
            priority=priority,
            status="requires_configuration",
            category="telegram",
            owner_added=True,
            searchable=searchable,
            region=region,
            metadata=meta,
        )
        with self._lock:
            self._sources[sid] = cfg
            return copy.deepcopy(cfg)

    def add_web_source(
        self,
        *,
        name: str,
        url: str,
        source_id: str | None = None,
        enabled: bool = True,
        priority: int = 5,
    ) -> AutoSourceConfig:
        sid = source_id or f"web_owner_{abs(hash(url)) % 10_000_000}"
        cfg = AutoSourceConfig(
            id=sid,
            name=name.strip() or sid,
            source_type="public_web",
            source_url=url.strip(),
            enabled=enabled,
            priority=priority,
            status="active",
            category="extra",
            owner_added=True,
        )
        with self._lock:
            self._sources[sid] = cfg
            return copy.deepcopy(cfg)

    def by_category(self, category: str) -> list[AutoSourceConfig]:
        return [s for s in self.list_all() if s.category == category]

    def menu_text_ru(self) -> str:
        lines = ["🔍 Источники поиска", ""]
        for cat, title in OWNER_SOURCE_SECTIONS:
            lines.append(f"• {title}")
            for s in self.by_category(cat):
                flag = "🟢" if s.enabled else "⚪"
                st = {
                    "active": "ок",
                    "requires_configuration": "нужна настройка",
                    "unavailable": "недоступен",
                }.get(s.status, s.status)
                lines.append(f"  {flag} {s.name} (p{s.priority}, {st})")
            lines.append("")
        lines.append("[+ Добавить Telegram-канал]")
        lines.append("[+ Добавить веб-источник]")
        lines.append("[Вкл/Выкл] [Приоритет] [Проверить источник]")
        return "\n".join(lines).strip()

    def probe(self, source_id: str) -> dict[str, Any]:
        """Mark connectivity without breaking search. No scraping of private APIs."""
        s = self.get(source_id)
        if not s:
            return {"ok": False, "message_ru": "Источник не найден."}
        if s.source_type == "telegram_channel":
            # Public channel scrape is not assumed available — require bot/admin config
            if s.status == "requires_configuration":
                return {
                    "ok": False,
                    "source_id": s.id,
                    "status": s.status,
                    "message_ru": (
                        f"{s.name}: канал включён, но чтение требует настройки бота/доступа. "
                        "Поиск по остальным источникам продолжается."
                    ),
                }
            return {
                "ok": True,
                "source_id": s.id,
                "status": s.status,
                "message_ru": f"{s.name}: источник доступен.",
            }
        if s.source_type == "public_web":
            self.set_status(source_id, "active")
            return {
                "ok": True,
                "source_id": s.id,
                "status": "active",
                "message_ru": f"{s.name}: веб-источник активен.",
            }
        return {
            "ok": True,
            "source_id": s.id,
            "status": s.status,
            "message_ru": f"{s.name}: готов.",
        }

    def reset_builtins(self) -> None:
        with self._lock:
            for s in _BUILTIN:
                if not self._sources.get(s.id) or not self._sources[s.id].owner_added:
                    self._sources[s.id] = copy.deepcopy(s)


auto_source_registry = AutoSourceRegistry()
