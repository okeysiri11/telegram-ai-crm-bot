#!/usr/bin/env python3
"""Knowledge Sprint 1.2 — AI Documentation Assistant.

Analyzes the repository via Git + filesystem scans, detects incremental
changes, and regenerates only affected Obsidian documentation under
knowledge/ (and maintains .obsidian/ metadata). Does not modify Platform
Core, Ecosystem packages, applications, or runtime APIs.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[2]
KNOWLEDGE = REPO / "knowledge"
OBSIDIAN = REPO / ".obsidian"
TOOLS = KNOWLEDGE / "tools"
DATA = KNOWLEDGE / "data"
SNAPSHOT_PATH = DATA / "project_snapshot.json"
REGISTRY_PATH = DATA / "ecosystem_registry.json"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")
NOW_ISO = datetime.now(timezone.utc).isoformat()
NL = "\n"

def bullets(items, empty="- None"):
    items = list(items)
    if not items:
        return [empty]
    out = []
    for i in items:
        s = str(i)
        out.append(s if s.lstrip().startswith("- ") else f"- {s}")
    return out

WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
REQUIRED_SECTIONS = [
    "## Overview",
    "## Architecture",
    "## Components",
    "## Relationships",
    "## Responsibilities",
    "## Interfaces",
    "## REST APIs",
    "## Events",
    "## Future roadmap",
    "## References",
    "## Related pages",
]


@dataclass
class GitContext:
    branch: str = ""
    latest_commit: str = ""
    latest_subject: str = ""
    status_lines: list[str] = field(default_factory=list)
    diff_stat: str = ""
    recent_log: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)


@dataclass
class ChangeSet:
    added_modules: list[str] = field(default_factory=list)
    removed_modules: list[str] = field(default_factory=list)
    modified_modules: list[str] = field(default_factory=list)
    renamed_modules: list[dict[str, str]] = field(default_factory=list)
    api_changes: list[str] = field(default_factory=list)
    architecture_changes: list[str] = field(default_factory=list)
    sprint_signals: list[str] = field(default_factory=list)
    agent_added: list[str] = field(default_factory=list)
    agent_removed: list[str] = field(default_factory=list)
    agent_updated: list[str] = field(default_factory=list)
    touched_areas: set[str] = field(default_factory=set)

    def has_changes(self) -> bool:
        return bool(
            self.added_modules
            or self.removed_modules
            or self.modified_modules
            or self.renamed_modules
            or self.api_changes
            or self.architecture_changes
            or self.sprint_signals
            or self.agent_added
            or self.agent_removed
            or self.agent_updated
            or self.touched_areas
        )


def run_git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        return (result.stdout or "").strip()
    except Exception:
        return ""


def write_md(rel: str, content: str) -> Path:
    path = KNOWLEDGE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n")
    return path


def frontmatter(title: str, aliases: list[str], tags: list[str]) -> str:
    alias_lines = NL.join(f"  - {a}" for a in aliases)
    tag_lines = NL.join(f"  - {t}" for t in tags)
    return (
        f"---\ntitle: {title}\naliases:\n{alias_lines}\ntags:\n{tag_lines}\n"
        f"generated: {NOW}\nsprint: Knowledge 1.2\n---\n"
    )


def std_sections(**kwargs: str) -> str:
    order = [
        ("Overview", "overview"),
        ("Architecture", "architecture"),
        ("Components", "components"),
        ("Relationships", "relationships"),
        ("Responsibilities", "responsibilities"),
        ("Interfaces", "interfaces"),
        ("REST APIs", "rest_apis"),
        ("Events", "events"),
        ("Future roadmap", "roadmap"),
        ("References", "references"),
        ("Related pages", "related"),
    ]
    return "\n\n".join(f"## {h}\n{kwargs[k]}" for h, k in order)


def load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text())
    return {}


def save_registry(data: dict[str, Any]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n")


class DocumentationAssistant:
    """AI Documentation Assistant — incremental Obsidian sync."""

    def __init__(self) -> None:
        self.registry = load_registry()
        self.git = GitContext()
        self.snapshot: dict[str, Any] = {}
        self.current: dict[str, Any] = {}
        self.changes = ChangeSet()
        self.written: list[str] = []

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def analyze_git(self) -> GitContext:
        self.git.branch = run_git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"
        self.git.latest_commit = run_git("rev-parse", "--short", "HEAD")
        self.git.latest_subject = run_git("log", "-1", "--pretty=%s")
        status = run_git("status", "--porcelain")
        self.git.status_lines = [l for l in status.splitlines() if l.strip()]
        self.git.diff_stat = run_git("diff", "--stat", "HEAD")
        # include staged+unstaged names
        names = run_git("diff", "--name-only", "HEAD")
        untracked = [
            line[3:]
            for line in self.git.status_lines
            if line.startswith("??")
        ]
        self.git.changed_files = sorted(
            {*(names.splitlines() if names else []), *untracked}
        )
        log = run_git("log", "-12", "--pretty=%h %ad %s", "--date=short")
        self.git.recent_log = [l for l in log.splitlines() if l.strip()]
        tags = run_git("tag", "--sort=-creatordate")
        self.git.tags = [t for t in tags.splitlines() if t.strip()][:20]
        return self.git

    def scan_modules(self) -> dict[str, Any]:
        platform = sorted(
            p.name
            for p in REPO.iterdir()
            if p.is_dir() and p.name.startswith("platform_")
        )
        apps = sorted(
            p.name
            for p in (REPO / "applications").iterdir()
            if p.is_dir() and not p.name.startswith(".")
        ) if (REPO / "applications").exists() else []
        ecosystem = []
        eco = REPO / "ecosystem"
        if eco.exists():
            ecosystem = sorted(
                p.name
                for p in eco.iterdir()
                if p.is_dir() and not p.name.startswith("_") and not p.name.startswith(".")
                and p.name not in {"__pycache__"}
            )
        drone_modules = []
        drone = REPO / "applications" / "drone_platform"
        if drone.exists():
            drone_modules = sorted(
                p.name
                for p in drone.iterdir()
                if p.is_dir() and not p.name.startswith("_") and p.name != "__pycache__"
            )
        return {
            "platform": platform,
            "applications": apps,
            "ecosystem": ecosystem,
            "drone": drone_modules,
        }

    def scan_apis(self) -> dict[str, str]:
        apis: dict[str, str] = {}
        patterns = [
            (REPO / "applications", "**/config.py"),
            (REPO / "ecosystem", "config.py"),
        ]
        # manifests
        for manifest in REPO.glob("**/manifest.json"):
            if "node_modules" in str(manifest) or ".venv" in str(manifest):
                continue
            try:
                data = json.loads(manifest.read_text())
            except Exception:
                continue
            prefix = data.get("api_prefix") or data.get("apis", {}).get("public_prefix")
            name = data.get("application") or data.get("application_name") or manifest.parent.name
            if prefix:
                apis[str(name)] = str(prefix)
        # config.py api_prefix =
        for cfg in REPO.glob("**/config.py"):
            rel = str(cfg.relative_to(REPO))
            if any(x in rel for x in (".venv", "node_modules", "venv/")):
                continue
            try:
                text = cfg.read_text(errors="ignore")
            except Exception:
                continue
            m = re.search(r'api_prefix\s*[:=]\s*["\']([^"\']+)["\']', text)
            if m:
                apis[rel] = m.group(1)
        # platform manifest
        pm = REPO / "platform_manifest.json"
        if pm.exists():
            try:
                pdata = json.loads(pm.read_text())
                core = pdata.get("platform_core", {})
                apis["platform_core"] = f"/api/{core.get('api_version', 'v1')}"
            except Exception:
                pass
        return dict(sorted(apis.items()))

    def scan_agents(self) -> dict[str, Any]:
        agents_dir = KNOWLEDGE / "agents"
        documented = sorted(p.stem for p in agents_dir.glob("*.md")) if agents_dir.exists() else []
        # read-only hints from applications (file names only)
        code_hints: list[str] = []
        for pattern in ("**/*assistant*.py", "**/*agent*.py"):
            for path in REPO.glob(pattern):
                rel = str(path.relative_to(REPO))
                if any(x in rel for x in (".venv", "venv/", "node_modules", "knowledge/tools")):
                    continue
                if rel.startswith("knowledge/"):
                    continue
                code_hints.append(rel)
        return {
            "documented": documented,
            "code_hints": sorted(set(code_hints))[:200],
        }

    def build_current_snapshot(self) -> dict[str, Any]:
        modules = self.scan_modules()
        self.current = {
            "captured_at": NOW_ISO,
            "git": asdict(self.git) if self.git.branch else asdict(self.analyze_git()),
            "modules": modules,
            "apis": self.scan_apis(),
            "agents": self.scan_agents(),
            "knowledge_files": sorted(
                str(p.relative_to(KNOWLEDGE))
                for p in KNOWLEDGE.rglob("*.md")
            ),
            "diagram_files": sorted(
                str(p.relative_to(KNOWLEDGE))
                for p in (KNOWLEDGE / "diagrams").rglob("*.md")
            ) if (KNOWLEDGE / "diagrams").exists() else [],
        }
        return self.current

    def load_snapshot(self) -> dict[str, Any]:
        if SNAPSHOT_PATH.exists():
            self.snapshot = json.loads(SNAPSHOT_PATH.read_text())
        else:
            self.snapshot = {}
        return self.snapshot

    def save_snapshot(self) -> None:
        DATA.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(self.current, indent=2) + "\n")

    def detect_changes(self) -> ChangeSet:
        prev = self.snapshot or {}
        cur = self.current
        changes = ChangeSet()

        def flat_modules(snap: dict[str, Any]) -> set[str]:
            mods = snap.get("modules") or {}
            out: set[str] = set()
            for group, items in mods.items():
                for item in items:
                    out.add(f"{group}:{item}")
            return out

        prev_m = flat_modules(prev)
        cur_m = flat_modules(cur)
        changes.added_modules = sorted(cur_m - prev_m)
        changes.removed_modules = sorted(prev_m - cur_m)

        # modified: modules appearing in git changed_files
        modified: set[str] = set()
        for path in self.git.changed_files:
            if path.startswith("platform_"):
                modified.add(f"platform:{path.split('/')[0]}")
                changes.touched_areas.add("platform")
                changes.architecture_changes.append(f"platform path touched: {path}")
            elif path.startswith("applications/"):
                parts = path.split("/")
                if len(parts) > 1:
                    modified.add(f"applications:{parts[1]}")
                    changes.touched_areas.add(parts[1])
                    changes.architecture_changes.append(f"application path touched: {path}")
            elif path.startswith("ecosystem/"):
                parts = path.split("/")
                if len(parts) > 1:
                    modified.add(f"ecosystem:{parts[1]}")
                changes.touched_areas.add("ecosystem")
                changes.architecture_changes.append(f"ecosystem path touched: {path}")
            elif path.startswith("knowledge/"):
                changes.touched_areas.add("knowledge")
            elif path.startswith("api/") or "api_prefix" in path or path.endswith("register.py"):
                changes.api_changes.append(path)
                changes.touched_areas.add("api")
            if "sprint" in path.lower() or "SPRINT" in path:
                changes.sprint_signals.append(path)
            if "agent" in path.lower() or "assistant" in path.lower():
                changes.touched_areas.add("agents")

        # rename heuristic from git status
        for line in self.git.status_lines:
            if line.startswith("R") or " -> " in line:
                changes.renamed_modules.append({"raw": line.strip()})

        changes.modified_modules = sorted(modified - set(changes.added_modules))

        prev_apis = prev.get("apis") or {}
        cur_apis = cur.get("apis") or {}
        for key in sorted(set(prev_apis) | set(cur_apis)):
            if key not in prev_apis:
                changes.api_changes.append(f"added API {key}={cur_apis[key]}")
            elif key not in cur_apis:
                changes.api_changes.append(f"removed API {key}={prev_apis[key]}")
            elif prev_apis[key] != cur_apis[key]:
                changes.api_changes.append(
                    f"changed API {key}: {prev_apis[key]} -> {cur_apis[key]}"
                )

        prev_agents = set((prev.get("agents") or {}).get("documented") or [])
        cur_agents = set((cur.get("agents") or {}).get("documented") or [])
        changes.agent_added = sorted(cur_agents - prev_agents)
        changes.agent_removed = sorted(prev_agents - cur_agents)

        # sprint completion signals from registry / knowledge
        if "Knowledge 1.2" not in json.dumps(self.registry.get("meta", {})):
            changes.sprint_signals.append("Knowledge 1.2 assistant rollout")
        for path in self.git.changed_files:
            if path.startswith("knowledge/sprints") or path.endswith("SPRINT_REGISTRY.md"):
                changes.sprint_signals.append(path)

        # first run: treat as full sync needed
        if not prev:
            changes.touched_areas.update(
                {"platform", "ecosystem", "knowledge", "api", "agents", "dashboards", "graphs"}
            )
            changes.architecture_changes.append("Initial snapshot — full documentation sync")

        if changes.has_changes():
            changes.touched_areas.add("dashboards")
        self.changes = changes
        return changes

    # ------------------------------------------------------------------
    # Incremental writers
    # ------------------------------------------------------------------
    def update_architecture_diff(self) -> Path | None:
        if not (
            self.changes.added_modules
            or self.changes.removed_modules
            or self.changes.modified_modules
            or self.changes.renamed_modules
            or self.changes.architecture_changes
            or not self.snapshot
        ):
            # still refresh a status page lightly when git dirty
            if not self.git.changed_files and self.snapshot:
                return None

        impact = []
        for area in sorted(self.changes.touched_areas):
            impact.append(f"- Area `{area}` requires doc refresh")
        deps = [
            "- Applications depend on Platform Core + Ecosystem via bridges only",
            "- Knowledge tools must not mutate runtime packages",
        ]
        body = std_sections(
            overview=f"Architecture diff generated {NOW} from Git + module scan (Knowledge 1.2).",
            architecture="Compare previous `project_snapshot.json` to current repository layout.",
            components=NL.join(
                [
                    "### Added modules",
                    *bullets(self.changes.added_modules),
                    "",
                    "### Modified modules",
                    *bullets(self.changes.modified_modules),
                    "",
                    "### Removed modules",
                    *bullets(self.changes.removed_modules),
                    "",
                    "### Renamed (git signals)",
                    *bullets(f"- `{r}`" for r in self.changes.renamed_modules),
                    "",
                    "### Detected architecture notes",
                    *bullets(self.changes.architecture_changes[:50]),
                ]
            ),
            relationships="[[ARCHITECTURE]] · [[ARCHITECTURE_DASHBOARD]] · [[diagrams/architecture/MODULE_RELATIONSHIPS]]",
            responsibilities="Explain structural delta for architects and sprint planners.",
            interfaces="Produced by `documentation_assistant.py`.",
            rest_apis="API deltas listed in release notes when `api` area touched.",
            events="snapshot_compared, architecture_diff_written",
            roadmap="[[ROADMAP]]",
            references="`knowledge/data/project_snapshot.json`",
            related="[[VALIDATION_REPORT]] · [[releases/RELEASE_NOTES]] · [[INDEX]]",
        )
        impact_block = NL.join(["### Impact analysis", *(impact or ["- No area impact"]), "", "### Dependencies", *deps])
        path = write_md(
            "ARCHITECTURE_CHANGES.md",
            frontmatter(
                "Architecture Changes",
                ["Architecture Changes", "Architecture Diff"],
                ["architecture", "diff", "knowledge-1.2"],
            )
            + "# Architecture Changes\n\n"
            + body
            + "\n\n"
            + impact_block,
        )
        self.written.append(str(path.relative_to(KNOWLEDGE)))
        return path

    def update_release_notes(self) -> list[Path]:
        paths: list[Path] = []
        features = []
        breaking = []
        new_apis = [c for c in self.changes.api_changes if c.startswith("added")]
        new_agents = list(self.changes.agent_added)
        if self.changes.removed_modules:
            breaking.append("Removed modules detected — verify dependent docs/links")
        if self.changes.api_changes:
            features.append("API surface changes detected (see Components)")
        if "knowledge" in self.changes.touched_areas:
            features.append("Knowledge 1.2 Documentation Assistant incremental sync")
        for m in self.changes.added_modules[:20]:
            features.append(f"Added module {m}")

        version_history = NL.join(
            [
                "| Version | Stream | Notes |",
                "|---------|--------|-------|",
                "| 1.2.0 | Knowledge | AI Documentation Assistant |",
                "| 1.1.0 | Knowledge | Living Obsidian documentation system |",
                "| 1.0.0-alpha | Drone | Foundation Sprint 11.1 |",
                "| 2.0.0 | Auto/Port/Agro | Commercial / enterprise releases |",
                "| 1.5.0-alpha | Ecosystem | Governance complete |",
                "| 3.0.0 | Platform Core | Certified baseline |",
            ]
        )
        components = NL.join(
            [
                "### Completed features (detected)",
                *bullets((f"- {f}" for f in features), empty="- No new feature signals in this run"),
                "",
                "### Breaking changes",
                *bullets((f"- {b}" for b in breaking), empty="- None detected"),
                "",
                "### New APIs",
                *bullets((f"- {a}" for a in new_apis), empty="- None detected"),
                "",
                "### New AI Agents",
                *bullets((f"- [[{a}]]" for a in new_agents), empty="- None detected"),
                "",
                "### Version history",
                version_history,
                "",
                "### Git context",
                f"- Branch: `{self.git.branch}`",
                f"- Latest commit: `{self.git.latest_commit}` — {self.git.latest_subject}",
                f"- Tags: {', '.join(self.git.tags[:8]) or 'none'}",
            ]
        )
        rn = write_md(
            "releases/RELEASE_NOTES.md",
            frontmatter("Release Notes", ["Release Notes"], ["releases", "knowledge-1.2"])
            + f"# Release Notes\n\n> Generated {NOW} by Documentation Assistant\n\n"
            + std_sections(
                overview="Automatically generated release notes from Git history and module/API/agent detection.",
                architecture="Knowledge-only release pipeline; runtime packages untouched.",
                components=components,
                relationships="[[CHANGELOG]] · [[ARCHITECTURE_CHANGES]] · [[registries/SPRINT_REGISTRY]]",
                responsibilities="Summarize completed features, breaking changes, APIs, and agents.",
                interfaces="`python3 knowledge/tools/release_notes.py`",
                rest_apis="See [[registries/API_REGISTRY]]",
                events="release_notes_regenerated",
                roadmap="[[ROADMAP]]",
                references="Git log + project snapshot",
                related="[[INDEX]] · [[DASHBOARD]] · [[EXECUTIVE_DASHBOARD]]",
            ),
        )
        paths.append(rn)

        changelog = write_md(
            "CHANGELOG.md",
            frontmatter("Changelog", ["Changelog"], ["changelog", "knowledge-1.2"])
            + "# Changelog\n\n"
            + std_sections(
                overview="Living changelog maintained by the Documentation Assistant.",
                architecture="Entries derived from sprint registry + latest Git signals.",
                components=NL.join(
                    [
                        f"### [1.2.0] Knowledge 1.2 — {NOW}",
                        "- AI Documentation Assistant",
                        "- Incremental documentation updates",
                        "- Git integration, architecture diff, validation report",
                        "- CLI: update_docs, build_graph, update_dashboards, check_links, release_notes, project_report, update_everything",
                        "",
                        "### Recent commits",
                        *bullets((f"- {line}" for line in self.git.recent_log[:10]), empty="- unavailable"),
                        "",
                        "### [1.1.0] Knowledge 1.1",
                        "- Living Obsidian documentation system",
                        "",
                        "### Platform / Apps (summary)",
                        "- Platform Core 3.0.0 certified",
                        "- Ecosystem 1.5.0-alpha",
                        "- Agro/Port/Auto 2.0.0",
                        "- Drone 1.0.0-alpha (11.1)",
                    ]
                ),
                relationships="[[releases/RELEASE_NOTES]] · [[PLATFORM_TIMELINE]]",
                responsibilities="Keep human-readable history current.",
                interfaces="Assistant release_notes + update_docs",
                rest_apis="N/A",
                events="changelog_updated",
                roadmap="[[ROADMAP]]",
                references="Root `CHANGELOG.md` remains Platform RC1 source of truth",
                related="[[SPRINT_PROGRESS]] · [[INDEX]]",
            ),
        )
        paths.append(changelog)
        self.written.extend(str(p.relative_to(KNOWLEDGE)) for p in paths)
        return paths

    def update_mermaid_graphs(self) -> list[Path]:
        if not (
            {"platform", "ecosystem", "knowledge", "graphs", "agents"} & self.changes.touched_areas
            or self.changes.added_modules
            or self.changes.removed_modules
            or not self.snapshot
        ):
            return []

        mods = self.current.get("modules") or {}
        apps = mods.get("applications") or []
        platform_sample = (mods.get("platform") or [])[:12]
        agents = (self.current.get("agents") or {}).get("documented") or []

        graphs = {
            "diagrams/automation/ARCHITECTURE_GRAPH.md": (
                "Architecture Graph",
                f"""flowchart TB
  CORE[Platform Core]
  ECO[Ecosystem]
  KNOW[Knowledge Vault]
  {NL.join(f'  APP_{i}[{a}]' for i, a in enumerate(apps))}
  KNOW --> CORE
  KNOW --> ECO
  {NL.join(f'  APP_{i} -->|bridges| CORE' for i in range(len(apps)))}
  {NL.join(f'  APP_{i} -->|bridges| ECO' for i in range(len(apps)))}
""",
            ),
            "diagrams/automation/DEPENDENCY_GRAPH.md": (
                "Dependency Graph",
                f"""flowchart BT
  APPS[Applications]
  ECO[Ecosystem]
  CORE[Platform Core]
  APPS --> ECO --> CORE
  APPS --> CORE
  subgraph PlatformPackages
  {NL.join(f'  {p}' for p in platform_sample)}
  end
  CORE --> PlatformPackages
""",
            ),
            "diagrams/automation/WORKFLOW_GRAPH.md": (
                "Workflow Graph",
                """stateDiagram-v2
  [*] --> Detect
  Detect --> Diff
  Diff --> IncrementalUpdate
  IncrementalUpdate --> Validate
  Validate --> Snapshot
  Snapshot --> [*]
""",
            ),
            "diagrams/automation/AGENT_GRAPH.md": (
                "Agent Graph Automated",
                f"""flowchart LR
  ORCH[Orchestrator]
  {NL.join(f'  ORCH --> A{i}[{a}]' for i, a in enumerate(agents[:12]))}
""",
            ),
            "diagrams/automation/APPLICATION_GRAPH.md": (
                "Application Graph Automated",
                f"""flowchart TB
  {NL.join(f'  {a}[{a}]' for a in apps)}
  {apps[0] if apps else 'apps'} -.-> CRM[CRM capability]
""",
            ),
            "diagrams/automation/DEPLOYMENT_GRAPH.md": (
                "Deployment Graph Automated",
                """flowchart LR
  CFG[Config] --> API[api/server.py]
  API --> HEALTH[Health]
  API --> ROUTES[Routers]
  ROUTES --> V1[/api/v1]
  ROUTES --> ECO[/api/ecosystem/v1]
  ROUTES --> APPS[/api/agro|port|auto|drone/v1]
""",
            ),
            "diagrams/automation/API_GRAPH.md": (
                "API Graph Automated",
                f"""flowchart TB
  GW[Gateway]
  {NL.join(f'  GW --> N{i}[\"{k}: {v}\"]' for i, (k, v) in enumerate(list((self.current.get('apis') or {}).items())[:12]))}
""",
            ),
            "diagrams/automation/KNOWLEDGE_GRAPH.md": (
                "Knowledge Graph Automated",
                """mindmap
  root((Knowledge))
    Assistant
      Git
      Diff
      Incremental
    Registries
    Dashboards
    Diagrams
    Validation
""",
            ),
        }

        paths: list[Path] = []
        for rel, (title, mermaid) in graphs.items():
            path = write_md(
                rel,
                frontmatter(title, [title], ["diagram", "automation", "knowledge-1.2"])
                + f"# {title}\n\n"
                + std_sections(
                    overview=f"Auto-regenerated Mermaid diagram ({title}) by Documentation Assistant.",
                    architecture=f"```mermaid\n{mermaid}\n```",
                    components="- Generated from current module/API/agent scan",
                    relationships="[[ARCHITECTURE_DASHBOARD]] · [[diagrams/PLATFORM_GRAPH]] · [[build_graph]]",
                    responsibilities="Keep graphs synchronized with repository structure.",
                    interfaces="`python3 knowledge/tools/build_graph.py`",
                    rest_apis="API graph reflects discovered prefixes only",
                    events="mermaid_regenerated",
                    roadmap="[[ROADMAP]]",
                    references="[[automation/DOCUMENTATION_ASSISTANT]]",
                    related="[[INDEX]] · [[DASHBOARD]]",
                ),
            )
            paths.append(path)
        # index for automated diagrams
        write_md(
            "diagrams/automation/README.md",
            frontmatter("Automated Diagrams", ["Automated Diagrams"], ["diagram", "knowledge-1.2"])
            + "# Automated Diagrams\n\n"
            + std_sections(
                overview="Mermaid diagrams regenerated by Knowledge 1.2 assistant.",
                architecture="Located under `knowledge/diagrams/automation/`.",
                components=NL.join(f"- [[{p.relative_to(KNOWLEDGE).with_suffix('')}]]" for p in paths),
                relationships="[[ARCHITECTURE_DASHBOARD]]",
                responsibilities="Incremental graph refresh",
                interfaces="build_graph.py",
                rest_apis="N/A",
                events="graphs_built",
                roadmap="[[ROADMAP]]",
                references="[[automation/DOCUMENTATION_ASSISTANT]]",
                related="[[INDEX]]",
            ),
        )
        self.written.extend(str(p.relative_to(KNOWLEDGE)) for p in paths)
        return paths

    def update_sprint_tracker(self) -> Path:
        reg = self.registry
        sprints = reg.get("sprints") or []
        completed = [s for s in sprints if s.get("status") == "completed"]
        planned = [s for s in sprints if s.get("status") == "planned"]
        pct = round(100 * len(completed) / max(len(sprints), 1), 1)
        modules = self.current.get("modules") or {}
        module_count = sum(len(v) for v in modules.values())
        md_count = len(self.current.get("knowledge_files") or [])
        diagram_count = len(self.current.get("diagram_files") or [])
        coverage = round(100 * min(md_count, 120) / 120, 1)

        # ensure Knowledge 1.2 in registry
        ids = {s.get("id") for s in sprints}
        if "K1.2" not in ids:
            sprints.append(
                {
                    "id": "K1.2",
                    "stream": "Knowledge",
                    "purpose": "AI Documentation Assistant incremental sync",
                    "version": "1.2.0",
                    "status": "completed",
                    "deps": ["K1.1"],
                }
            )
            reg["sprints"] = sprints
            reg.setdefault("meta", {})
            reg["meta"].update(
                {
                    "sprint": "Knowledge 1.2",
                    "title": "AI Documentation Assistant",
                    "status": "completed",
                    "version": "1.2.0",
                }
            )
            self.registry = reg
            save_registry(reg)
            completed = [s for s in sprints if s.get("status") == "completed"]
            planned = [s for s in sprints if s.get("status") == "planned"]
            pct = round(100 * len(completed) / max(len(sprints), 1), 1)

        path = write_md(
            "reports/SPRINT_TRACKER.md",
            frontmatter("Sprint Tracker", ["Sprint Tracker"], ["sprints", "knowledge-1.2"])
            + "# Sprint Tracker\n\n"
            + std_sections(
                overview="Automated sprint tracker maintained by Documentation Assistant.",
                architecture="Source: `ecosystem_registry.json` + live module coverage.",
                components=NL.join(
                    [
                        f"- **Current sprint focus:** Knowledge 1.2 (assistant)",
                        f"- **Completed sprints:** {len(completed)}",
                        f"- **Planned sprints:** {len(planned)}",
                        f"- **Completion %:** {pct}%",
                        f"- **Module coverage (scanned):** {module_count}",
                        f"- **Documentation files:** {md_count}",
                        f"- **Diagram files:** {diagram_count}",
                        f"- **Documentation coverage (heuristic):** {coverage}%",
                        "- **Pending work:** Drone 11.2+, Ecosystem 1.6, Legal L1.0",
                        "- **Roadmap progress:** [[ROADMAP]] · [[SPRINT_PROGRESS]]",
                        "",
                        "### Signals this run",
                        *bullets(self.changes.sprint_signals[:20]),
                    ]
                ),
                relationships="[[registries/SPRINT_REGISTRY]] · [[PROJECT_STATUS]]",
                responsibilities="Track completion and coverage metrics.",
                interfaces="update_docs / update_everything",
                rest_apis="N/A",
                events="sprint_tracker_updated",
                roadmap="[[ROADMAP]]",
                references="registry JSON",
                related="[[DASHBOARD]] · [[INDEX]]",
            ),
        )
        self.written.append(str(path.relative_to(KNOWLEDGE)))
        return path

    def update_agent_registry_page(self) -> Path | None:
        if not (
            self.changes.agent_added
            or self.changes.agent_removed
            or self.changes.agent_updated
            or "agents" in self.changes.touched_areas
            or not self.snapshot
        ):
            return None
        agents = (self.current.get("agents") or {}).get("documented") or []
        hints = (self.current.get("agents") or {}).get("code_hints") or []
        path = write_md(
            "registries/AGENT_REGISTRY.md",
            frontmatter(
                "AI Agents Registry",
                ["AI Agents Registry", "Agent Registry"],
                ["registry", "agents", "knowledge-1.2"],
            )
            + "# AI Agents Registry\n\n"
            + std_sections(
                overview="Agent registry refreshed by Documentation Assistant detection.",
                architecture="Documented agents live in `knowledge/agents/`; code hints are read-only paths.",
                components=NL.join(
                    [
                        "### Documented agents",
                        *bullets(f"- [[{a}]]" for a in agents),
                        "",
                        "### Added this run",
                        *bullets(self.changes.agent_added),
                        "",
                        "### Removed this run",
                        *bullets(self.changes.agent_removed),
                        "",
                        "### Code hints (read-only)",
                        *bullets(f"- `{h}`" for h in hints[:40]),
                        "",
                        "### Relationships / workflows",
                        "- [[diagrams/flows/AGENT_COMMUNICATION]]",
                        "- [[diagrams/automation/AGENT_GRAPH]]",
                        "- Permissions: bridge-only; engineering agents remain safe-use scoped",
                    ]
                ),
                relationships="[[AI Agents]] · [[diagrams/AGENT_GRAPH]]",
                responsibilities="Detect new/updated/removed agents and keep wiki roster current.",
                interfaces="documentation_assistant.scan_agents",
                rest_apis="App assistant endpoints documented in API registry",
                events="agent_registry_updated",
                roadmap="Shared skill catalog",
                references="`docs/AGENT_REGISTRY.md`",
                related="[[Owner AI]] · [[Drone Engineer AI]] · [[INDEX]]",
            ),
        )
        self.written.append(str(path.relative_to(KNOWLEDGE)))
        return path

    def update_dashboards(self) -> list[Path]:
        if "dashboards" not in self.changes.touched_areas and self.snapshot:
            # still allow forced updates via CLI
            pass
        mods = self.current.get("modules") or {}
        module_count = sum(len(v) for v in mods.values())
        agents = len((self.current.get("agents") or {}).get("documented") or [])
        apis = len(self.current.get("apis") or {})
        sprints = self.registry.get("sprints") or []
        completed = sum(1 for s in sprints if s.get("status") == "completed")
        pct = round(100 * completed / max(len(sprints), 1), 1)
        dirty = len(self.git.changed_files)

        pages = {
            "INDEX.md": (
                "INDEX",
                ["Home", "Knowledge Home"],
                NL.join(
                    [
                        "**Main entry point** — Knowledge 1.2 AI Documentation Assistant enabled.",
                        "",
                        f"- Branch `{self.git.branch}` @ `{self.git.latest_commit}`",
                        f"- Modules scanned: **{module_count}** · Agents: **{agents}** · APIs: **{apis}**",
                        f"- Sprint completion: **{pct}%** · Dirty files: **{dirty}**",
                        "",
                        "### Quick links",
                        "[[DASHBOARD]] · [[EXECUTIVE_DASHBOARD]] · [[ARCHITECTURE_DASHBOARD]] · [[PROJECT_STATUS]] · [[SPRINT_PROGRESS]]",
                        "[[VALIDATION_REPORT]] · [[ARCHITECTURE_CHANGES]] · [[releases/RELEASE_NOTES]] · [[reports/PROJECT_REPORT]]",
                        "[[Platform Core]] · [[Auto Marketplace]] · [[Port ERP]] · [[Agro Marketplace]] · [[Drone Platform]] · [[AI Agents]]",
                        "[[automation/DOCUMENTATION_ASSISTANT]] · [[diagrams/automation/README]]",
                    ]
                ),
            ),
            "DASHBOARD.md": (
                "Dashboard",
                ["Dashboard"],
                NL.join(
                    [
                        "| Panel | Status |",
                        "|-------|--------|",
                        f"| Git branch | `{self.git.branch}` |",
                        f"| Latest commit | `{self.git.latest_commit}` |",
                        f"| Changed files | {dirty} |",
                        f"| Modules | {module_count} |",
                        f"| Agents | {agents} |",
                        f"| API prefixes | {apis} |",
                        f"| Sprint completion | {pct}% |",
                        "| Assistant | Knowledge 1.2 Ready |",
                        "",
                        "[[EXECUTIVE_DASHBOARD]] · [[ARCHITECTURE_DASHBOARD]] · [[reports/SPRINT_TRACKER]] · [[statistics/STATISTICS]]",
                    ]
                ),
            ),
            "EXECUTIVE_DASHBOARD.md": (
                "Executive Dashboard",
                ["Executive Dashboard"],
                NL.join(
                    [
                        "### Portfolio posture",
                        "- Platform Core 3.0.0 — Production Ready",
                        "- Ecosystem 1.5.0-alpha — complete",
                        "- Agro / Port / Auto — 2.0.0 commercial",
                        "- Drone — 1.0.0-alpha foundation",
                        "- Knowledge — **1.2 Documentation Assistant**",
                        "",
                        f"### Delivery signals",
                        f"- Sprint completion **{pct}%**",
                        f"- Pending roadmap items tracked in [[ROADMAP]]",
                        f"- Architecture diff: [[ARCHITECTURE_CHANGES]]",
                    ]
                ),
            ),
            "PROJECT_STATUS.md": (
                "Project Status",
                ["Project Status"],
                NL.join(
                    [
                        "| Stream | Status |",
                        "|--------|--------|",
                        "| Platform Core | ✅ 3.0.0 |",
                        "| Ecosystem | ✅ 1.5.0-alpha |",
                        "| Agro / Port / Auto | ✅ 2.0.0 |",
                        "| Drone | ✅ 11.1 foundation |",
                        "| Knowledge 1.1 | ✅ Living docs |",
                        "| Knowledge 1.2 | ✅ Assistant |",
                        "| Legal | 🔜 planned |",
                        "",
                        f"Git: `{self.git.branch}` / `{self.git.latest_commit}` — {self.git.latest_subject}",
                    ]
                ),
            ),
            "SPRINT_PROGRESS.md": (
                "Sprint Progress",
                ["Sprint Progress"],
                NL.join(
                    [
                        f"**Completion:** {pct}% ({completed}/{len(sprints)})",
                        "",
                        "### Current",
                        "- Knowledge 1.2 — AI Documentation Assistant",
                        "",
                        "### Completed (summary)",
                        "- Platform 1.5–5.5 · Eco 7.x · Agro 8.x · Port 9.x · Auto 6.x/10.x · Drone 11.1 · Knowledge 1.1–1.2",
                        "",
                        "### Planned",
                        "- Drone 11.2+ · Ecosystem 1.6 · Legal L1.0",
                        "",
                        "[[registries/SPRINT_REGISTRY]] · [[reports/SPRINT_TRACKER]]",
                    ]
                ),
            ),
            "ARCHITECTURE_DASHBOARD.md": (
                "Architecture Dashboard",
                ["Architecture Dashboard"],
                NL.join(
                    [
                        "### Automated graphs",
                        "[[diagrams/automation/ARCHITECTURE_GRAPH]] · [[diagrams/automation/DEPENDENCY_GRAPH]] · [[diagrams/automation/WORKFLOW_GRAPH]]",
                        "[[diagrams/automation/AGENT_GRAPH]] · [[diagrams/automation/APPLICATION_GRAPH]] · [[diagrams/automation/DEPLOYMENT_GRAPH]]",
                        "[[diagrams/automation/API_GRAPH]] · [[diagrams/automation/KNOWLEDGE_GRAPH]]",
                        "",
                        "### Diff",
                        "[[ARCHITECTURE_CHANGES]]",
                        "",
                        "### Classic diagrams",
                        "[[diagrams/PLATFORM_GRAPH]] · [[diagrams/APPLICATION_GRAPH]] · [[diagrams/AGENT_GRAPH]] · [[diagrams/DATA_FLOW]]",
                    ]
                ),
            ),
        }

        paths: list[Path] = []
        for rel, (title, aliases, components) in pages.items():
            path = write_md(
                rel,
                frontmatter(title, aliases, ["dashboard", "knowledge-1.2"])
                + f"# {title}\n\n"
                + std_sections(
                    overview=f"Automatically updated dashboard ({title}) — Knowledge 1.2.",
                    architecture="Driven by Documentation Assistant incremental sync.",
                    components=components,
                    relationships="[[INDEX]] · [[DASHBOARD]] · [[automation/DOCUMENTATION_ASSISTANT]]",
                    responsibilities="Keep stakeholders synchronized with project state.",
                    interfaces="`python3 knowledge/tools/update_dashboards.py`",
                    rest_apis="[[registries/API_REGISTRY]]",
                    events="dashboard_updated",
                    roadmap="[[ROADMAP]]",
                    references="Git + snapshot",
                    related="[[VALIDATION_REPORT]] · [[reports/PROJECT_REPORT]]",
                ),
            )
            paths.append(path)
        self.written.extend(str(p.relative_to(KNOWLEDGE)) for p in paths)
        return paths

    def validate_knowledge(self) -> Path:
        md_files = list(KNOWLEDGE.rglob("*.md"))
        # map note names for link resolution
        notes: dict[str, Path] = {}
        for path in md_files:
            rel = path.relative_to(KNOWLEDGE)
            notes[path.stem] = path
            notes[str(rel.with_suffix(""))] = path
            notes[str(rel.with_suffix("")).replace("\\", "/")] = path

        broken: list[str] = []
        missing_sections: list[str] = []
        missing_refs: list[str] = []
        duplicates: dict[str, list[str]] = defaultdict(list)
        for path in md_files:
            duplicates[path.stem].append(str(path.relative_to(KNOWLEDGE)))
            text = path.read_text(errors="ignore")
            rel = str(path.relative_to(KNOWLEDGE))
            if "templates/" in rel:
                continue
            for section in REQUIRED_SECTIONS:
                if section not in text:
                    missing_sections.append(f"{rel}: missing {section}")
            for match in WIKI_LINK_RE.findall(text):
                target = match.strip()
                if not target or target.startswith("http"):
                    continue
                # skip mustache templates
                if "{{" in target:
                    continue
                ok = (
                    target in notes
                    or target.replace(" ", "%20") in notes
                    or (KNOWLEDGE / f"{target}.md").exists()
                    or (KNOWLEDGE / f"{target}").exists()
                    or (KNOWLEDGE / f"{target}.md".replace(" ", " ")).exists()
                )
                # also allow path without .md
                if not ok and "/" in target:
                    ok = (KNOWLEDGE / f"{target}.md").exists() or (KNOWLEDGE / target).exists()
                if not ok:
                    broken.append(f"{rel} -> [[{target}]]")
            if "[[INDEX]]" not in text and rel not in {"INDEX.md", "README.md"} and "templates/" not in rel:
                # not mandatory for every page; track lightly
                pass
            if rel.startswith("applications/") and "[[ARCHITECTURE]]" not in text and "Architecture" not in text:
                missing_refs.append(f"{rel}: weak architecture references")

        dup_pages = {k: v for k, v in duplicates.items() if len(v) > 1}
        diagram_expected = [
            "diagrams/automation/ARCHITECTURE_GRAPH.md",
            "diagrams/automation/DEPENDENCY_GRAPH.md",
            "diagrams/automation/AGENT_GRAPH.md",
            "diagrams/automation/APPLICATION_GRAPH.md",
            "diagrams/automation/API_GRAPH.md",
            "diagrams/automation/DEPLOYMENT_GRAPH.md",
            "diagrams/automation/WORKFLOW_GRAPH.md",
            "diagrams/automation/KNOWLEDGE_GRAPH.md",
        ]
        missing_diagrams = [d for d in diagram_expected if not (KNOWLEDGE / d).exists()]
        missing_apis = []
        if not (KNOWLEDGE / "registries/API_REGISTRY.md").exists():
            missing_apis.append("registries/API_REGISTRY.md")

        report = write_md(
            "VALIDATION_REPORT.md",
            frontmatter("Validation Report", ["Validation Report"], ["validation", "knowledge-1.2"])
            + "# Validation Report\n\n"
            + std_sections(
                overview=f"Knowledge validation run {NOW}.",
                architecture="Static checks over Markdown wiki links, sections, diagrams, and API registry presence.",
                components=NL.join(
                    [
                        f"- Markdown files scanned: **{len(md_files)}**",
                        f"- Broken wiki links: **{len(broken)}**",
                        f"- Missing required sections: **{len(missing_sections)}**",
                        f"- Duplicate stems: **{len(dup_pages)}**",
                        f"- Missing diagrams: **{len(missing_diagrams)}**",
                        f"- Missing API registry files: **{len(missing_apis)}**",
                        "",
                        "### Broken wiki links (sample)",
                        *bullets(f"- `{b}`" for b in broken[:80]),
                        "",
                        "### Missing sections (sample)",
                        *bullets(f"- `{m}`" for m in missing_sections[:40]),
                        "",
                        "### Duplicate page stems",
                        *bullets(
                            f"`{k}`: {', '.join(v)}"
                            for k, v in list(dup_pages.items())[:30]
                        ),
                        "",
                        "### Missing diagrams",
                        *bullets(f"- `{d}`" for d in missing_diagrams),
                        "",
                        "### Missing APIs docs",
                        *bullets(f"- `{a}`" for a in missing_apis),
                        "",
                        "### Missing architecture references (soft)",
                        *bullets(f"- `{m}`" for m in missing_refs[:30]),
                    ]
                ),
                relationships="[[INDEX]] · [[standards/DOCUMENTATION_STANDARDS]]",
                responsibilities="Detect documentation defects before they spread.",
                interfaces="`python3 knowledge/tools/check_links.py`",
                rest_apis="Validates presence of API registry documentation only",
                events="validation_completed",
                roadmap="Auto-fix stubs for broken links in Knowledge 1.3",
                references="Wiki link regex scan",
                related="[[DASHBOARD]] · [[automation/DOCUMENTATION_ASSISTANT]]",
            ),
        )
        self.written.append(str(report.relative_to(KNOWLEDGE)))
        return report

    def maintain_obsidian(self) -> list[Path]:
        """Maintain tags/bookmarks/graph/canvas/daily indexes inside knowledge + .obsidian."""
        written: list[Path] = []
        # canvas index
        canvas_idx = write_md(
            "canvas/INDEX.md",
            frontmatter("Canvas Index", ["Canvas Index"], ["canvas", "knowledge-1.2"])
            + "# Canvas Index\n\n"
            + std_sections(
                overview="Index of Obsidian Canvas workspace for architecture workshops.",
                architecture="Files live under `knowledge/canvas/`.",
                components="- [[canvas/README]]\n- Add `.canvas` boards as needed",
                relationships="[[ARCHITECTURE_DASHBOARD]] · [[excalidraw/README]]",
                responsibilities="Keep canvas discovery current.",
                interfaces="Obsidian Canvas plugin",
                rest_apis="N/A",
                events="canvas_index_updated",
                roadmap="Starter boards in later knowledge sprints",
                references="[[automation/DOCUMENTATION_ASSISTANT]]",
                related="[[INDEX]]",
            ),
        )
        written.append(canvas_idx)

        daily_idx = write_md(
            "reports/DAILY_NOTES_INDEX.md",
            frontmatter("Daily Notes Index", ["Daily Notes Index"], ["daily", "knowledge-1.2"])
            + "# Daily Notes Index\n\n"
            + std_sections(
                overview="Index for Daily Notes created via Obsidian template.",
                architecture="Template: `knowledge/templates/Daily Note.md` · folder configured in `.obsidian/daily-notes.json`.",
                components="- Template [[templates/Daily Note]]\n- Landing [[INDEX]]",
                relationships="[[DASHBOARD]] · [[SPRINT_PROGRESS]]",
                responsibilities="Help navigate daily engineering notes.",
                interfaces="Obsidian Daily Notes core plugin",
                rest_apis="N/A",
                events="daily_index_updated",
                roadmap="Auto-list dated notes when present",
                references=".obsidian/daily-notes.json",
                related="[[INDEX]]",
            ),
        )
        written.append(daily_idx)

        # bookmarks refresh
        bookmarks = {
            "items": [
                {"type": "file", "ctime": 1721651000000, "path": "knowledge/INDEX.md", "title": "INDEX"},
                {"type": "file", "ctime": 1721651000001, "path": "knowledge/DASHBOARD.md", "title": "Dashboard"},
                {"type": "file", "ctime": 1721651000002, "path": "knowledge/VALIDATION_REPORT.md", "title": "Validation"},
                {"type": "file", "ctime": 1721651000003, "path": "knowledge/ARCHITECTURE_CHANGES.md", "title": "Architecture Diff"},
                {"type": "file", "ctime": 1721651000004, "path": "knowledge/automation/DOCUMENTATION_ASSISTANT.md", "title": "Doc Assistant"},
                {"type": "file", "ctime": 1721651000005, "path": "knowledge/reports/PROJECT_REPORT.md", "title": "Project Report"},
                {"type": "file", "ctime": 1721651000006, "path": "knowledge/SPRINT_PROGRESS.md", "title": "Sprint Progress"},
                {"type": "file", "ctime": 1721651000007, "path": "knowledge/diagrams/automation/README.md", "title": "Automated Graphs"},
            ]
        }
        OBSIDIAN.mkdir(parents=True, exist_ok=True)
        bp = OBSIDIAN / "bookmarks.json"
        bp.write_text(json.dumps(bookmarks, indent=2) + "\n")

        # graph color groups remain; ensure knowledge-1.2 tag color
        graph_path = OBSIDIAN / "graph.json"
        if graph_path.exists():
            try:
                graph = json.loads(graph_path.read_text())
            except Exception:
                graph = {}
        else:
            graph = {}
        groups = graph.get("colorGroups") or []
        if not any("knowledge-1.2" in json.dumps(g) for g in groups):
            groups.append(
                {"query": "tag:#knowledge-1.2", "color": {"a": 1, "rgb": 300}}
            )
            graph["colorGroups"] = groups
            graph_path.write_text(json.dumps(graph, indent=2) + "\n")

        self.written.extend(str(p.relative_to(KNOWLEDGE)) for p in written)
        return written

    def project_report(self) -> Path:
        path = write_md(
            "reports/PROJECT_REPORT.md",
            frontmatter("Project Report", ["Project Report"], ["report", "knowledge-1.2"])
            + "# Project Report\n\n"
            + std_sections(
                overview=f"Consolidated project report generated {NOW}.",
                architecture="Combines Git context, module scan, change set, and documentation outputs.",
                components=NL.join(
                    [
                        f"- Branch: `{self.git.branch}`",
                        f"- Commit: `{self.git.latest_commit}` — {self.git.latest_subject}",
                        f"- Changed files: {len(self.git.changed_files)}",
                        f"- Added modules: {len(self.changes.added_modules)}",
                        f"- Removed modules: {len(self.changes.removed_modules)}",
                        f"- Modified modules: {len(self.changes.modified_modules)}",
                        f"- API change signals: {len(self.changes.api_changes)}",
                        f"- Files written this run: {len(self.written)}",
                        "",
                        "### Recent log",
                        *bullets((f"- {l}" for l in self.git.recent_log[:8]), empty="- n/a"),
                        "",
                        "### Written outputs",
                        *bullets((f"- `{w}`" for w in self.written[:60]), empty="- none"),
                    ]
                ),
                relationships="[[DASHBOARD]] · [[VALIDATION_REPORT]] · [[ARCHITECTURE_CHANGES]]",
                responsibilities="Single printable status artifact for the vault.",
                interfaces="`python3 knowledge/tools/project_report.py`",
                rest_apis="[[registries/API_REGISTRY]]",
                events="project_report_generated",
                roadmap="[[ROADMAP]]",
                references="Git + snapshot",
                related="[[INDEX]] · [[releases/RELEASE_NOTES]]",
            ),
        )
        self.written.append(str(path.relative_to(KNOWLEDGE)))
        return path

    def update_api_docs_incremental(self) -> Path | None:
        if "api" not in self.changes.touched_areas and self.snapshot:
            return None
        apis = self.current.get("apis") or {}
        rows = [f"| `{k}` | `{v}` |" for k, v in apis.items()]
        path = write_md(
            "registries/API_REGISTRY.md",
            frontmatter("API Registry", ["API Registry"], ["registry", "api", "knowledge-1.2"])
            + "# API Registry\n\n"
            + std_sections(
                overview="API registry regenerated from read-only manifest/config scan.",
                architecture="Detection only — no API code modified.",
                components=NL.join(
                    ["| Source | Prefix |", "|--------|--------|", *rows]
                    or ["| — | — |"]
                ),
                relationships="[[API_REFERENCE]] · [[diagrams/automation/API_GRAPH]]",
                responsibilities="Keep API documentation synchronized with discovered prefixes.",
                interfaces="scan_apis()",
                rest_apis="This page lists discovered prefixes.",
                events="api_registry_updated",
                roadmap="OpenAPI embeds later",
                references="manifest.json / config.py (read-only)",
                related="[[INDEX]] · [[ARCHITECTURE_CHANGES]]",
            ),
        )
        self.written.append(str(path.relative_to(KNOWLEDGE)))
        return path

    def update_sprint_registry_from_data(self) -> Path:
        # reuse generate_docs if available, else write slim registry
        try:
            from knowledge.tools import generate_docs as gd  # type: ignore
        except Exception:
            gd = None
        if gd is not None:
            try:
                # generate_docs uses knowledge/ as ROOT via parents[1]
                gd.generate_registries(self.registry)
                path = KNOWLEDGE / "registries" / "SPRINT_REGISTRY.md"
                self.written.append("registries/SPRINT_REGISTRY.md")
                return path
            except Exception:
                pass
        sprints = self.registry.get("sprints") or []
        rows = [
            f"| {s.get('id')} | {s.get('stream')} | {s.get('purpose')} | {s.get('version')} | {s.get('status')} |"
            for s in sprints
        ]
        path = write_md(
            "registries/SPRINT_REGISTRY.md",
            frontmatter("Sprint Registry", ["Sprint Registry"], ["registry", "sprints", "knowledge-1.2"])
            + "# Sprint Registry\n\n"
            + std_sections(
                overview="Sprint registry maintained with Knowledge 1.2 assistant.",
                architecture="From ecosystem_registry.json",
                components=NL.join(
                    [
                        "| Sprint | Stream | Purpose | Version | Status |",
                        "|--------|--------|---------|---------|--------|",
                        *rows,
                    ]
                ),
                relationships="[[reports/SPRINT_TRACKER]] · [[SPRINT_PROGRESS]]",
                responsibilities="Track sprints",
                interfaces="update_docs.py",
                rest_apis="N/A",
                events="sprint_registry_updated",
                roadmap="[[ROADMAP]]",
                references="registry JSON",
                related="[[INDEX]]",
            ),
        )
        self.written.append("registries/SPRINT_REGISTRY.md")
        return path

    # ------------------------------------------------------------------
    # Pipelines
    # ------------------------------------------------------------------
    def prepare(self) -> None:
        self.analyze_git()
        self.load_snapshot()
        self.build_current_snapshot()
        self.detect_changes()

    def update_docs(self, *, force: bool = False) -> dict[str, Any]:
        self.prepare()
        if force:
            self.changes.touched_areas.update(
                {"platform", "ecosystem", "knowledge", "api", "agents", "dashboards", "graphs"}
            )
        self.update_architecture_diff()
        self.update_sprint_tracker()
        self.update_sprint_registry_from_data()
        self.update_api_docs_incremental()
        self.update_agent_registry_page()
        self.update_release_notes()
        self.update_dashboards()
        self.save_snapshot()
        return self.summary()

    def build_graph(self, *, force: bool = False) -> dict[str, Any]:
        self.prepare()
        if force:
            self.changes.touched_areas.add("graphs")
        self.update_mermaid_graphs()
        self.save_snapshot()
        return self.summary()

    def update_dashboards_only(self, *, force: bool = True) -> dict[str, Any]:
        self.prepare()
        if force:
            self.changes.touched_areas.add("dashboards")
        self.update_dashboards()
        self.update_sprint_tracker()
        return self.summary()

    def check_links(self) -> dict[str, Any]:
        self.prepare()
        self.validate_knowledge()
        return self.summary()

    def release_notes_only(self) -> dict[str, Any]:
        self.prepare()
        self.changes.touched_areas.add("knowledge")
        self.update_release_notes()
        return self.summary()

    def project_report_only(self) -> dict[str, Any]:
        self.prepare()
        self.project_report()
        return self.summary()

    def update_everything(self) -> dict[str, Any]:
        self.prepare()
        self.changes.touched_areas.update(
            {"platform", "ecosystem", "knowledge", "api", "agents", "dashboards", "graphs"}
        )
        self.update_architecture_diff()
        self.update_sprint_tracker()
        self.update_sprint_registry_from_data()
        self.update_api_docs_incremental()
        self.update_agent_registry_page()
        self.update_release_notes()
        self.update_mermaid_graphs()
        self.update_dashboards()
        self.validate_knowledge()
        self.maintain_obsidian()
        self.project_report()
        # also refresh 1.1 generator outputs when possible
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "generate_docs", TOOLS / "generate_docs.py"
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.main()
                self.written.append("(generate_docs.main)")
        except Exception as exc:
            self.written.append(f"(generate_docs skipped: {exc})")
        self.save_snapshot()
        return self.summary()

    def summary(self) -> dict[str, Any]:
        changes = asdict(self.changes)
        areas = changes.get("touched_areas")
        if isinstance(areas, set):
            changes["touched_areas"] = sorted(areas)
        elif areas is not None and not isinstance(areas, list):
            changes["touched_areas"] = list(areas)
        return {
            "sprint": "Knowledge 1.2",
            "generated": NOW_ISO,
            "branch": self.git.branch,
            "commit": self.git.latest_commit,
            "changes": changes,
            "written": self.written,
        }


def main() -> None:
    assistant = DocumentationAssistant()
    result = assistant.update_everything()
    print(json.dumps({"status": "ok", **{k: result[k] for k in ("sprint", "branch", "commit", "written")}}, indent=2))


if __name__ == "__main__":
    main()
