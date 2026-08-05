"""AI Skills & SDK engine — Sprint 36.8.

Extends platform_ai.skills: registry enrichment, install/runtime sandbox,
marketplace, SDK templates (Python/TS/REST/MCP).
"""

from __future__ import annotations

import time
from typing import Any

from platform_ai.skills.skill_manager import skill_manager
from platform_ai.skills_sdk_models import (
    InstalledSkill,
    MarketplaceListing,
    SdkKind,
    SdkTemplate,
    SkillDefinition,
    SkillExecution,
    SkillInstallState,
    SkillVersion,
    SkillVisibility,
    new_id,
    sign_skill,
)


class SkillsSdkEngine:
    def __init__(self) -> None:
        self.skills: dict[str, SkillDefinition] = {}
        self.versions: dict[str, list[SkillVersion]] = {}
        self.installed: dict[str, InstalledSkill] = {}  # key skill_id
        self.marketplace: dict[str, MarketplaceListing] = {}
        self.executions: list[SkillExecution] = []
        self.templates: dict[str, SdkTemplate] = {}
        self._stats = {
            "registered": 0,
            "installed": 0,
            "executed": 0,
            "failed": 0,
            "marketplace_downloads": 0,
        }
        self._seeded = False

    def reset(self) -> None:
        self.skills.clear()
        self.versions.clear()
        self.installed.clear()
        self.marketplace.clear()
        self.executions.clear()
        self.templates.clear()
        self._stats = {k: 0 for k in self._stats}
        skill_manager.reset()
        self._seeded = False

    def ensure_seed(self) -> None:
        if self._seeded:
            return
        try:
            skill_manager.initialize()
        except Exception:
            pass
        # Mirror builtin skills into product registry
        try:
            builtin_records = skill_manager.list_skills()
        except Exception:
            builtin_records = []
        for record in builtin_records:
            if not isinstance(record, dict):
                continue
            skill_id = str(record.get("skill_id") or "")
            if not skill_id or skill_id in self.skills:
                continue
            self._register_internal(
                {
                    "skill_id": skill_id,
                    "name": str(record.get("name") or skill_id),
                    "description": str(record.get("description") or ""),
                    "category": str(record.get("category") or "analysis"),
                    "version": str(record.get("version") or "1.0.0"),
                    "permissions": list(record.get("permissions") or ["skill.execute"]),
                    "visibility": SkillVisibility.ENTERPRISE.value,
                    "tags": list(record.get("tags") or []),
                    "dependencies": [],
                }
            )

        # Demo marketplace skills
        demos = [
            {
                "skill_id": "skill.summarize_report",
                "name": "Summarize Report",
                "description": "Summarize enterprise documents into executive briefs.",
                "category": "summarization",
                "visibility": "public",
                "tags": ["docs", "executive"],
                "permissions": ["skill.execute", "docs.read"],
                "dependencies": [],
                "rating": 4.6,
            },
            {
                "skill_id": "skill.crm_enrich",
                "name": "CRM Enrichment",
                "description": "Enrich CRM leads with firmographic context.",
                "category": "recommendation",
                "visibility": "enterprise",
                "tags": ["crm"],
                "permissions": ["skill.execute", "crm.write"],
                "dependencies": ["skill.summarize_report"],
                "rating": 4.2,
            },
            {
                "skill_id": "skill.private_audit",
                "name": "Private Audit",
                "description": "Tenant-private compliance audit skill.",
                "category": "risk",
                "visibility": "private",
                "tags": ["security"],
                "permissions": ["skill.execute", "audit.read"],
                "dependencies": [],
                "rating": 4.8,
            },
            {
                "skill_id": "skill.local_draft",
                "name": "Local Draft Helper",
                "description": "Local-only drafting skill for offline agents.",
                "category": "analysis",
                "visibility": "local",
                "tags": ["local"],
                "permissions": ["skill.execute"],
                "dependencies": [],
                "rating": 4.0,
            },
        ]
        for item in demos:
            self._register_internal(item)
            listing = MarketplaceListing(
                listing_id=new_id("slist"),
                skill_id=item["skill_id"],
                repository=str(item["visibility"]),
                featured=item["skill_id"] == "skill.summarize_report",
                downloads=10,
                rating=float(item.get("rating") or 0),
            )
            self.marketplace[item["skill_id"]] = listing

        self._seed_templates()
        self._seeded = True

    def _seed_templates(self) -> None:
        self.templates = {
            "tpl_python": SdkTemplate(
                template_id="tpl_python",
                kind=SdkKind.PYTHON,
                name="Python Skill SDK",
                description="Create an AISkill subclass for the platform_ai skills runtime.",
                files={
                    "skill.py": (
                        "from platform_ai.skills.skill_base import AISkill\n"
                        "from platform_ai.skills.models import SkillMetadata, SkillExecutionResult\n\n"
                        "class MySkill(AISkill):\n"
                        "    @classmethod\n"
                        "    def metadata(cls) -> SkillMetadata:\n"
                        "        return SkillMetadata(skill_id='skill.my', name='My Skill')\n\n"
                        "    async def execute(self, request, context):\n"
                        "        return SkillExecutionResult(skill_id=self.metadata().skill_id, "
                        "execution_id='x', success=True, output={'ok': True})\n"
                    )
                },
                example="from platform_ai.skills_sdk_service import skills_sdk_service\n"
                "await skills_sdk_service.execute({'skill_id': 'skill.summarize_report', 'input': {}})",
            ),
            "tpl_ts": SdkTemplate(
                template_id="tpl_ts",
                kind=SdkKind.TYPESCRIPT,
                name="TypeScript Skill SDK",
                description="Client SDK for calling /api/skills from TypeScript agents.",
                files={
                    "skillClient.ts": (
                        "export async function runSkill(skillId: string, input: Record<string, unknown>) {\n"
                        "  const res = await fetch('/api/skills/execute', {\n"
                        "    method: 'POST',\n"
                        "    headers: { 'Content-Type': 'application/json' },\n"
                        "    body: JSON.stringify({ skill_id: skillId, input }),\n"
                        "  });\n"
                        "  return res.json();\n"
                        "}\n"
                    )
                },
                example="await runSkill('skill.crm_enrich', { lead_id: 'L1' });",
            ),
            "tpl_rest": SdkTemplate(
                template_id="tpl_rest",
                kind=SdkKind.REST,
                name="REST Skills API",
                description="HTTP contract for skill lifecycle and execution.",
                files={
                    "openapi.snippet.yaml": (
                        "paths:\n"
                        "  /api/skills/execute:\n"
                        "    post:\n"
                        "      summary: Execute an installed skill\n"
                    )
                },
                example="curl -X POST /api/skills/execute -d '{\"skill_id\":\"skill.summarize_report\"}'",
            ),
            "tpl_mcp": SdkTemplate(
                template_id="tpl_mcp",
                kind=SdkKind.MCP,
                name="MCP Skills Tool",
                description="Expose skills as MCP tools for agent hosts.",
                files={
                    "mcp_tool.json": (
                        '{"name":"skills.execute","description":"Execute an ADOS skill",'
                        '"inputSchema":{"type":"object","properties":{"skill_id":{"type":"string"}}}}'
                    )
                },
                example='{"tool":"skills.execute","arguments":{"skill_id":"skill.summarize_report"}}',
            ),
        }

    def _register_internal(self, body: dict[str, Any]) -> SkillDefinition:
        skill_id = str(body.get("skill_id") or new_id("skill"))
        version = str(body.get("version") or body.get("latest_version") or "1.0.0")
        skill = SkillDefinition(
            skill_id=skill_id,
            name=str(body.get("name") or skill_id),
            description=str(body.get("description") or ""),
            category=str(body.get("category") or "analysis"),
            latest_version=version,
            visibility=str(body.get("visibility") or SkillVisibility.ENTERPRISE.value),
            tags=list(body.get("tags") or []),
            permissions=list(body.get("permissions") or ["skill.execute"]),
            dependencies=list(body.get("dependencies") or []),
            author=str(body.get("author") or "platform"),
            rating=float(body.get("rating") or 0),
            ratings_count=int(body.get("ratings_count") or (1 if body.get("rating") else 0)),
            changelog=list(body.get("changelog") or [{"version": version, "notes": "Initial release"}]),
            metadata=dict(body.get("metadata") or {}),
            signature=str(body.get("signature") or sign_skill(skill_id, version)),
        )
        self.skills[skill_id] = skill
        ver = SkillVersion(
            version_id=new_id("sver"),
            skill_id=skill_id,
            version=version,
            changelog=str((skill.changelog[0] or {}).get("notes") if skill.changelog else ""),
            signature=skill.signature,
            manifest={"permissions": skill.permissions, "dependencies": skill.dependencies},
        )
        self.versions.setdefault(skill_id, [])
        if not any(v.version == version for v in self.versions[skill_id]):
            self.versions[skill_id].append(ver)
        self._stats["registered"] = len(self.skills)
        return skill

    # --- Registry ---

    def register(self, body: dict[str, Any]) -> SkillDefinition:
        self.ensure_seed()
        skill = self._register_internal(body)
        # marketplace entry
        vis = skill.visibility.value if isinstance(skill.visibility, SkillVisibility) else str(skill.visibility)
        self.marketplace.setdefault(
            skill.skill_id,
            MarketplaceListing(
                listing_id=new_id("slist"),
                skill_id=skill.skill_id,
                repository=vis,
                rating=skill.rating,
            ),
        )
        return skill

    def list_skills(self, *, category: str | None = None, visibility: str | None = None) -> list[SkillDefinition]:
        self.ensure_seed()
        rows = list(self.skills.values())
        if category:
            rows = [s for s in rows if s.category == category]
        if visibility:
            rows = [
                s
                for s in rows
                if (s.visibility.value if isinstance(s.visibility, SkillVisibility) else s.visibility) == visibility
            ]
        return sorted(rows, key=lambda s: s.updated_at, reverse=True)

    def get_skill(self, skill_id: str) -> SkillDefinition:
        self.ensure_seed()
        skill = self.skills.get(skill_id)
        if skill is None:
            raise KeyError(f"skill not found: {skill_id}")
        return skill

    def list_versions(self, skill_id: str) -> list[SkillVersion]:
        self.get_skill(skill_id)
        return list(self.versions.get(skill_id, []))

    def publish_version(self, skill_id: str, body: dict[str, Any]) -> SkillVersion:
        skill = self.get_skill(skill_id)
        version = str(body.get("version") or "1.0.1")
        notes = str(body.get("changelog") or body.get("notes") or f"Release {version}")
        ver = SkillVersion(
            version_id=new_id("sver"),
            skill_id=skill_id,
            version=version,
            changelog=notes,
            signature=sign_skill(skill_id, version),
            manifest=dict(body.get("manifest") or {"permissions": skill.permissions}),
        )
        self.versions.setdefault(skill_id, []).append(ver)
        skill.latest_version = version
        skill.signature = ver.signature
        skill.changelog.append({"version": version, "notes": notes})
        skill.updated_at = time.time()
        return ver

    # --- Install / Runtime ---

    def install(self, skill_id: str, body: dict[str, Any] | None = None) -> InstalledSkill:
        body = body or {}
        skill = self.get_skill(skill_id)
        # dependency check
        for dep in skill.dependencies:
            if dep not in self.installed and dep != skill_id:
                if dep in self.skills:
                    self.install(dep, {"principal": body.get("principal") or "system"})
                else:
                    raise ValueError(f"missing dependency: {dep}")
        version = str(body.get("version") or skill.latest_version)
        inst = InstalledSkill(
            install_id=new_id("sinst"),
            skill_id=skill_id,
            version=version,
            state=SkillInstallState.ENABLED,
            principal=str(body.get("principal") or "system"),
            sandbox=bool(body.get("sandbox", True)),
            resource_limits=dict(
                body.get("resource_limits")
                or {"cpu_ms": 5000, "memory_mb": 128, "timeout_sec": float(body.get("timeout_sec") or 30)}
            ),
        )
        self.installed[skill_id] = inst
        self._stats["installed"] = len(self.installed)
        listing = self.marketplace.get(skill_id)
        if listing:
            listing.downloads += 1
            self._stats["marketplace_downloads"] += 1
        return inst

    def uninstall(self, skill_id: str) -> InstalledSkill:
        inst = self.installed.get(skill_id)
        if inst is None:
            raise KeyError(f"skill not installed: {skill_id}")
        inst.state = SkillInstallState.UNINSTALLED
        inst.updated_at = time.time()
        self.installed.pop(skill_id, None)
        self._stats["installed"] = len(self.installed)
        return inst

    def enable(self, skill_id: str) -> InstalledSkill:
        inst = self.installed.get(skill_id)
        if inst is None:
            raise KeyError(f"skill not installed: {skill_id}")
        inst.state = SkillInstallState.ENABLED
        inst.updated_at = time.time()
        return inst

    def disable(self, skill_id: str) -> InstalledSkill:
        inst = self.installed.get(skill_id)
        if inst is None:
            raise KeyError(f"skill not installed: {skill_id}")
        inst.state = SkillInstallState.DISABLED
        inst.updated_at = time.time()
        return inst

    def list_installed(self) -> list[InstalledSkill]:
        self.ensure_seed()
        return list(self.installed.values())

    async def execute(self, body: dict[str, Any]) -> SkillExecution:
        self.ensure_seed()
        skill_id = str(body.get("skill_id") or "")
        skill = self.get_skill(skill_id)
        inst = self.installed.get(skill_id)
        if inst is None:
            # auto-install for agents when requested
            if body.get("auto_install", True):
                inst = self.install(skill_id, {"principal": body.get("agent_id") or body.get("principal") or "agent"})
            else:
                raise RuntimeError(f"skill not installed: {skill_id}")

        started = time.monotonic()
        sandboxed = bool(inst.sandbox and body.get("sandbox", True))
        limits = dict(inst.resource_limits)
        timeout = float(limits.get("timeout_sec") or 30)

        try:
            if inst.state == SkillInstallState.DISABLED:
                raise RuntimeError(f"skill disabled: {skill_id}")
            records = skill_manager.list_skills()
            native_ids = {str(r.get("skill_id")) for r in records if isinstance(r, dict) and r.get("skill_id")}
            if skill_id in native_ids:
                from platform_ai.skills.models import SkillExecutionRequest

                result = await skill_manager.execute(
                    SkillExecutionRequest(
                        skill_id=skill_id,
                        input=dict(body.get("input") or body.get("payload") or {}),
                        user_id=str(body.get("user_id") or body.get("agent_id") or "system"),
                        use_cache=bool(body.get("use_cache", False)),
                    )
                )
                output = result.to_dict() if hasattr(result, "to_dict") else dict(result)
                success = bool(getattr(result, "success", True))
            else:
                # Sandbox simulated execution
                payload = dict(body.get("input") or body.get("payload") or {})
                if sandboxed and len(str(payload)) > int(limits.get("memory_mb", 128)) * 1024:
                    raise RuntimeError("sandbox memory limit exceeded")
                signature_ok = skill.signature == sign_skill(skill_id, inst.version)
                if not signature_ok:
                    raise RuntimeError("skill signature verification failed")
                output = {
                    "skill_id": skill_id,
                    "version": inst.version,
                    "echo": payload,
                    "message": f"Executed {skill.name} in sandbox",
                    "signature_ok": signature_ok,
                }
                success = True
                # soft timeout awareness
                _ = timeout
            duration = round((time.monotonic() - started) * 1000, 2)
            exe = SkillExecution(
                execution_id=new_id("sexec"),
                skill_id=skill_id,
                version=inst.version,
                success=success,
                output=output if isinstance(output, dict) else {"result": output},
                sandboxed=sandboxed,
                duration_ms=duration,
                agent_id=body.get("agent_id"),
            )
            self.executions.append(exe)
            self.executions = self.executions[-2000:]
            self._stats["executed"] += 1
            return exe
        except Exception as exc:  # noqa: BLE001
            duration = round((time.monotonic() - started) * 1000, 2)
            exe = SkillExecution(
                execution_id=new_id("sexec"),
                skill_id=skill_id,
                version=inst.version if inst else skill.latest_version,
                success=False,
                output={},
                sandboxed=sandboxed,
                duration_ms=duration,
                error=str(exc),
                agent_id=body.get("agent_id"),
            )
            self.executions.append(exe)
            self._stats["failed"] += 1
            return exe

    # --- Marketplace ---

    def marketplace_list(self, *, repository: str | None = None) -> list[dict[str, Any]]:
        self.ensure_seed()
        out = []
        for listing in self.marketplace.values():
            if repository and listing.repository != repository:
                continue
            skill = self.skills.get(listing.skill_id)
            out.append(
                {
                    **listing.to_dict(),
                    "skill": skill.to_dict() if skill else None,
                }
            )
        return sorted(out, key=lambda x: (-float(x.get("rating") or 0), -int(x.get("downloads") or 0)))

    def rate(self, skill_id: str, score: float, *, comment: str = "") -> SkillDefinition:
        skill = self.get_skill(skill_id)
        score = max(0.0, min(5.0, float(score)))
        total = skill.rating * skill.ratings_count + score
        skill.ratings_count += 1
        skill.rating = round(total / skill.ratings_count, 2)
        skill.updated_at = time.time()
        if comment:
            skill.changelog.append({"version": skill.latest_version, "notes": f"rating: {comment}"})
        listing = self.marketplace.get(skill_id)
        if listing:
            listing.rating = skill.rating
        return skill

    def check_updates(self, skill_id: str) -> dict[str, Any]:
        skill = self.get_skill(skill_id)
        inst = self.installed.get(skill_id)
        versions = [v.version for v in self.versions.get(skill_id, [])]
        return {
            "skill_id": skill_id,
            "installed_version": inst.version if inst else None,
            "latest_version": skill.latest_version,
            "update_available": bool(inst and inst.version != skill.latest_version),
            "versions": versions,
            "changelog": skill.changelog,
        }

    # --- SDK ---

    def list_templates(self, *, kind: str | None = None) -> list[SdkTemplate]:
        self.ensure_seed()
        rows = list(self.templates.values())
        if kind:
            rows = [t for t in rows if (t.kind.value if isinstance(t.kind, SdkKind) else t.kind) == kind]
        return rows

    def get_template(self, template_id: str) -> SdkTemplate:
        self.ensure_seed()
        tpl = self.templates.get(template_id)
        if tpl is None:
            raise KeyError(f"template not found: {template_id}")
        return tpl

    def sdk_manifest(self) -> dict[str, Any]:
        self.ensure_seed()
        return {
            "sdks": [k.value for k in SdkKind],
            "templates": [t.to_dict() for t in self.templates.values()],
            "endpoints": {
                "python": "platform_ai.skills_sdk_service.skills_sdk_service",
                "rest": "/api/skills",
                "mcp": "skills.execute",
                "typescript": "/api/sdk/templates/tpl_ts",
            },
        }

    def statistics(self) -> dict[str, Any]:
        self.ensure_seed()
        by_vis: dict[str, int] = {}
        for s in self.skills.values():
            v = s.visibility.value if isinstance(s.visibility, SkillVisibility) else str(s.visibility)
            by_vis[v] = by_vis.get(v, 0) + 1
        return {
            **self._stats,
            "skills": len(self.skills),
            "versions": sum(len(v) for v in self.versions.values()),
            "installed": len(self.installed),
            "marketplace": len(self.marketplace),
            "executions": len(self.executions),
            "templates": len(self.templates),
            "by_visibility": by_vis,
        }

    def list_executions(self, *, limit: int = 50) -> list[SkillExecution]:
        return list(reversed(self.executions[-limit:]))


skills_sdk_engine = SkillsSdkEngine()
