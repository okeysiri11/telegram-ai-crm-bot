# Cross-application shared services.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ecosystem.shared.store import EcosystemStore, ecosystem_store


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


@dataclass
class SharedFile:
    file_id: str = field(default_factory=_id)
    owner_id: str = ""
    name: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    application_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "application_id": self.application_id,
            "created_at": self.created_at,
        }


@dataclass
class CalendarEvent:
    event_id: str = field(default_factory=_id)
    owner_id: str = ""
    title: str = ""
    starts_at: float = field(default_factory=_ts)
    ends_at: float = field(default_factory=lambda: _ts() + 3600)
    application_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "owner_id": self.owner_id,
            "title": self.title,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "application_id": self.application_id,
            "created_at": self.created_at,
        }


@dataclass
class SharedContact:
    contact_id: str = field(default_factory=_id)
    owner_id: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    application_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contact_id": self.contact_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "application_id": self.application_id,
            "created_at": self.created_at,
        }


@dataclass
class SharedTask:
    task_id: str = field(default_factory=_id)
    owner_id: str = ""
    title: str = ""
    status: str = "open"
    due_at: float = 0.0
    application_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "owner_id": self.owner_id,
            "title": self.title,
            "status": self.status,
            "due_at": self.due_at,
            "application_id": self.application_id,
            "created_at": self.created_at,
        }


@dataclass
class AIMemoryEntry:
    memory_id: str = field(default_factory=_id)
    user_id: str = ""
    application_id: str = ""
    content: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "application_id": self.application_id,
            "content": self.content,
            "tags": list(self.tags),
            "created_at": self.created_at,
        }


class CrossApplicationServices:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def add_file(self, owner_id: str, name: str, *, mime_type: str = "", application_id: str = "") -> SharedFile:
        file = SharedFile(owner_id=owner_id, name=name, mime_type=mime_type, application_id=application_id)
        self._store.shared_files.save(file.file_id, file)
        return file

    def list_files(self, owner_id: str) -> list[SharedFile]:
        return [f for f in self._store.shared_files.list_all() if f.owner_id == owner_id]

    def add_calendar_event(self, owner_id: str, title: str, *, starts_at: float = 0, application_id: str = "") -> CalendarEvent:
        event = CalendarEvent(owner_id=owner_id, title=title, starts_at=starts_at or _ts(), application_id=application_id)
        self._store.shared_calendar.save(event.event_id, event)
        return event

    def list_calendar(self, owner_id: str) -> list[CalendarEvent]:
        return sorted([e for e in self._store.shared_calendar.list_all() if e.owner_id == owner_id], key=lambda e: e.starts_at)

    def add_contact(self, owner_id: str, name: str, *, email: str = "", application_id: str = "") -> SharedContact:
        contact = SharedContact(owner_id=owner_id, name=name, email=email, application_id=application_id)
        self._store.shared_contacts.save(contact.contact_id, contact)
        return contact

    def list_contacts(self, owner_id: str) -> list[SharedContact]:
        return [c for c in self._store.shared_contacts.list_all() if c.owner_id == owner_id]

    def add_task(self, owner_id: str, title: str, *, due_at: float = 0, application_id: str = "") -> SharedTask:
        task = SharedTask(owner_id=owner_id, title=title, due_at=due_at, application_id=application_id)
        self._store.shared_tasks.save(task.task_id, task)
        return task

    def list_tasks(self, owner_id: str) -> list[SharedTask]:
        return [t for t in self._store.shared_tasks.list_all() if t.owner_id == owner_id]

    async def remember(self, user_id: str, content: str, *, application_id: str = "", tags: list[str] | None = None) -> AIMemoryEntry:
        entry = AIMemoryEntry(user_id=user_id, content=content, application_id=application_id, tags=tags or [])
        self._store.ai_memory.save(entry.memory_id, entry)
        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            await platform_bridge.store_memory(user_id, content, application_id=application_id)
        except Exception:
            pass
        return entry

    def recall(self, user_id: str, *, application_id: str = "") -> list[AIMemoryEntry]:
        entries = [m for m in self._store.ai_memory.list_all() if m.user_id == user_id]
        if application_id:
            entries = [m for m in entries if m.application_id in ("", application_id)]
        return sorted(entries, key=lambda m: m.created_at, reverse=True)


cross_app_services = CrossApplicationServices()
