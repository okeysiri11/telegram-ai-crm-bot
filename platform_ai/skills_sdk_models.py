"""AI Skills & SDK models — Sprint 36.8 (extends platform_ai.skills SoR)."""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SkillVisibility(str, Enum):
    LOCAL = "local"
    ENTERPRISE = "enterprise"
    PRIVATE = "private"
    PUBLIC = "public"


class SkillInstallState(str, Enum):
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNINSTALLED = "uninstalled"


class SdkKind(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    REST = "rest"
    MCP = "mcp"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _skills_signing_secret(explicit: bytes | None = None) -> bytes:
    if explicit is not None:
        return explicit
    import os

    env = (os.getenv("SKILLS_SIGNING_SECRET") or "").strip()
    if env:
        return env.encode()
    return b"ados-skills-demo"


def sign_skill(skill_id: str, version: str, *, secret: bytes | None = None) -> str:
    material = _skills_signing_secret(secret)
    return hmac.new(material, f"{skill_id}:{version}".encode(), hashlib.sha256).hexdigest()[:32]


@dataclass
class SkillDefinition:
    skill_id: str
    name: str
    description: str = ""
    category: str = "analysis"
    latest_version: str = "1.0.0"
    visibility: SkillVisibility | str = SkillVisibility.ENTERPRISE
    tags: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    signature: str = ""
    author: str = "platform"
    rating: float = 0.0
    ratings_count: int = 0
    changelog: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.visibility, str):
            self.visibility = SkillVisibility(self.visibility)
        if not self.signature:
            self.signature = sign_skill(self.skill_id, self.latest_version)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "latest_version": self.latest_version,
            "visibility": self.visibility.value if isinstance(self.visibility, SkillVisibility) else self.visibility,
            "tags": list(self.tags),
            "permissions": list(self.permissions),
            "dependencies": list(self.dependencies),
            "signature": self.signature,
            "author": self.author,
            "rating": self.rating,
            "ratings_count": self.ratings_count,
            "changelog": list(self.changelog),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class SkillVersion:
    version_id: str
    skill_id: str
    version: str
    changelog: str = ""
    signature: str = ""
    manifest: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InstalledSkill:
    install_id: str
    skill_id: str
    version: str
    state: SkillInstallState | str = SkillInstallState.ENABLED
    principal: str = "system"
    sandbox: bool = True
    resource_limits: dict[str, Any] = field(default_factory=lambda: {"cpu_ms": 5000, "memory_mb": 128, "timeout_sec": 30})
    installed_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.state, str):
            self.state = SkillInstallState(self.state)

    def to_dict(self) -> dict[str, Any]:
        return {
            "install_id": self.install_id,
            "skill_id": self.skill_id,
            "version": self.version,
            "state": self.state.value if isinstance(self.state, SkillInstallState) else self.state,
            "principal": self.principal,
            "sandbox": self.sandbox,
            "resource_limits": dict(self.resource_limits),
            "installed_at": self.installed_at,
            "updated_at": self.updated_at,
        }


@dataclass
class SkillExecution:
    execution_id: str
    skill_id: str
    version: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    sandboxed: bool = True
    duration_ms: float = 0.0
    error: str | None = None
    agent_id: str | None = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MarketplaceListing:
    listing_id: str
    skill_id: str
    repository: str  # local | enterprise | private | public
    featured: bool = False
    downloads: int = 0
    rating: float = 0.0
    published: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SdkTemplate:
    template_id: str
    kind: SdkKind | str
    name: str
    description: str
    files: dict[str, str] = field(default_factory=dict)
    example: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.kind, str):
            self.kind = SdkKind(self.kind)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "kind": self.kind.value if isinstance(self.kind, SdkKind) else self.kind,
            "name": self.name,
            "description": self.description,
            "files": dict(self.files),
            "example": self.example,
        }
