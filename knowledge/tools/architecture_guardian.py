#!/usr/bin/env python3
"""Knowledge Sprint 1.3 — AI Project Architect & Architecture Guardian.

Read-only repository analysis that validates AI Ecosystem architecture rules
and generates Obsidian reports under knowledge/. Does not modify Platform Core,
applications, APIs, or business logic.
"""

from __future__ import annotations

import ast
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[2]
KNOWLEDGE = REPO / "knowledge"
OBSIDIAN = REPO / ".obsidian"
DATA = KNOWLEDGE / "data"
REGISTRY_PATH = DATA / "ecosystem_registry.json"
HISTORY_PATH = DATA / "architecture_history.json"
SCORES_PATH = DATA / "architecture_scores.json"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")
NOW_ISO = datetime.now(timezone.utc).isoformat()
NL = "\n"
WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
    re.MULTILINE,
)

SKIP_DIR_PARTS = {
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
}


def bullets(items: Iterable[Any], empty: str = "- None") -> list[str]:
    items = list(items)
    if not items:
        return [empty]
    out = []
    for i in items:
        s = str(i)
        out.append(s if s.lstrip().startswith("- ") else f"- {s}")
    return out


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
        f"generated: {NOW}\nsprint: Knowledge 1.3\n---\n"
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


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return default if default is not None else {}


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_PARTS for part in path.parts)


def module_layer(name: str) -> str:
    if name.startswith("platform_") or name in {"platform_manifest", "api", "services", "database"}:
        if name.startswith("platform_"):
            return "platform"
        return "shared"
    if name.startswith("applications.") or name.startswith("applications/"):
        return "application"
    if name == "ecosystem" or name.startswith("ecosystem."):
        return "ecosystem"
    if name.startswith("knowledge"):
        return "knowledge"
    return "other"


@dataclass
class Violation:
    severity: str  # high | medium | low
    category: str
    message: str
    path: str = ""


@dataclass
class ArchitectureFindings:
    violations: list[Violation] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    circular: list[str] = field(default_factory=list)
    missing_abstractions: list[str] = field(default_factory=list)
    misplaced: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    unused_apis: list[str] = field(default_factory=list)
    dead_docs: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    gates: dict[str, Any] = field(default_factory=dict)
    inventory: dict[str, Any] = field(default_factory=dict)


class ArchitectureGuardian:
    """AI Project Architect — continuous architecture validation (docs only)."""

    def __init__(self) -> None:
        self.registry = load_json(REGISTRY_PATH, {})
        self.findings = ArchitectureFindings()
        self.written: list[str] = []
        self.import_graph: dict[str, set[str]] = defaultdict(set)
        self.package_files: dict[str, list[str]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Inventory & import graph (read-only)
    # ------------------------------------------------------------------
    def inventory(self) -> dict[str, Any]:
        platform = sorted(
            p.name
            for p in REPO.iterdir()
            if p.is_dir() and p.name.startswith("platform_") and not should_skip(p)
        )
        apps = []
        apps_root = REPO / "applications"
        if apps_root.exists():
            apps = sorted(
                p.name
                for p in apps_root.iterdir()
                if p.is_dir() and not p.name.startswith(".") and not should_skip(p)
            )
        eco = []
        eco_root = REPO / "ecosystem"
        if eco_root.exists():
            eco = sorted(
                p.name
                for p in eco_root.iterdir()
                if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__"
            )
        py_count = 0
        test_count = 0
        for path in REPO.rglob("*.py"):
            if should_skip(path):
                continue
            py_count += 1
            rel = str(path.relative_to(REPO))
            if rel.startswith("tests/") or "/tests/" in rel or path.name.startswith("test_"):
                test_count += 1
        md_count = len(list(KNOWLEDGE.rglob("*.md"))) if KNOWLEDGE.exists() else 0
        agents = len(list((KNOWLEDGE / "agents").glob("*.md"))) if (KNOWLEDGE / "agents").exists() else 0
        inv = {
            "platform_packages": platform,
            "applications": apps,
            "ecosystem_modules": eco,
            "python_files": py_count,
            "test_files": test_count,
            "knowledge_md": md_count,
            "agents_documented": agents,
        }
        self.findings.inventory = inv
        return inv

    def _top_package(self, rel: str) -> str:
        parts = rel.split("/")
        if parts[0] == "applications" and len(parts) > 1:
            return f"applications.{parts[1]}"
        if parts[0] == "ecosystem":
            return "ecosystem"
        if parts[0].startswith("platform_"):
            return parts[0]
        if parts[0] in {"api", "services", "database", "plugins", "repositories", "src"}:
            return parts[0]
        return parts[0]

    def build_import_graph(self, *, limit_files: int = 8000) -> dict[str, set[str]]:
        count = 0
        for path in REPO.rglob("*.py"):
            if should_skip(path):
                continue
            if path.is_relative_to(KNOWLEDGE):
                continue
            rel = str(path.relative_to(REPO))
            pkg = self._top_package(rel)
            self.package_files[pkg].append(rel)
            try:
                text = path.read_text(errors="ignore")
            except Exception:
                continue
            # Prefer AST; fall back to regex
            imports: set[str] = set()
            try:
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split(".")[0])
                            # keep applications.X
                            if node.module.startswith("applications."):
                                bits = node.module.split(".")
                                if len(bits) >= 2:
                                    imports.add(f"applications.{bits[1]}")
                            if node.module.startswith("platform_"):
                                imports.add(node.module.split(".")[0])
                            if node.module.startswith("ecosystem"):
                                imports.add("ecosystem")
            except SyntaxError:
                for match in IMPORT_RE.finditer(text):
                    mod = match.group(1) or match.group(2)
                    if mod:
                        imports.add(mod.split(".")[0])
            for imp in imports:
                if imp in {"typing", "json", "re", "os", "sys", "pathlib", "dataclasses", "collections", "asyncio", "logging", "uuid", "datetime", "unittest", "pytest"}:
                    continue
                self.import_graph[pkg].add(imp)
            count += 1
            if count >= limit_files:
                break
        return self.import_graph

    # ------------------------------------------------------------------
    # Detectors
    # ------------------------------------------------------------------
    def detect_violations(self) -> None:
        apps = set(self.findings.inventory.get("applications") or [])
        # Bridge rule: applications should not import other applications' packages
        for pkg, deps in self.import_graph.items():
            if not pkg.startswith("applications."):
                continue
            app_name = pkg.split(".", 1)[1]
            for dep in deps:
                if dep.startswith("applications."):
                    other = dep.split(".", 1)[1]
                    if other != app_name:
                        self.findings.violations.append(
                            Violation(
                                "high",
                                "cross_app_import",
                                f"`{pkg}` imports `{dep}` — prefer bridges only",
                                pkg,
                            )
                        )
                # apps importing platform internals deeply is OK via bridges; flag direct mutation patterns later

        # Misplaced: platform_* inside applications
        for app in apps:
            app_path = REPO / "applications" / app
            for p in app_path.rglob("*"):
                if should_skip(p):
                    continue
                if p.is_dir() and p.name.startswith("platform_"):
                    self.findings.misplaced.append(
                        f"applications/{app}/{p.name} looks like Platform Core package inside an app"
                    )
                    self.findings.violations.append(
                        Violation("high", "misplaced_code", self.findings.misplaced[-1], str(p))
                    )

        # Naming gates
        for app in apps:
            if not re.match(r"^[a-z][a-z0-9_]*$", app):
                self.findings.violations.append(
                    Violation("medium", "naming", f"Application folder naming unusual: {app}", app)
                )
        for plat in self.findings.inventory.get("platform_packages") or []:
            if not plat.startswith("platform_"):
                self.findings.violations.append(
                    Violation("medium", "naming", f"Platform package naming: {plat}", plat)
                )

        # Missing abstractions: apps without integrations/ bridge folder
        for app in apps:
            bridge = REPO / "applications" / app / "integrations"
            if not bridge.exists():
                msg = f"Application `{app}` missing `integrations/` bridge folder"
                self.findings.missing_abstractions.append(msg)
                self.findings.violations.append(Violation("medium", "missing_abstraction", msg, app))

        # ecosystem should not import applications (layering)
        for dep in self.import_graph.get("ecosystem", set()):
            if dep.startswith("applications") or dep in {f"applications.{a}" for a in apps}:
                self.findings.violations.append(
                    Violation(
                        "high",
                        "layering",
                        f"ecosystem imports application `{dep}` — invert dependency via bridges",
                        "ecosystem",
                    )
                )

    def detect_duplicates(self) -> None:
        # duplicate top-level module stems across layers
        stems: dict[str, list[str]] = defaultdict(list)
        for plat in self.findings.inventory.get("platform_packages") or []:
            stems[plat.replace("platform_", "")].append(f"platform:{plat}")
        for app in self.findings.inventory.get("applications") or []:
            # inner module name collisions e.g. inventory in multiple apps is expected; track package-level only
            stems[app].append(f"app:{app}")
        # knowledge hub duplicates (stem collisions)
        md_stems: dict[str, list[str]] = defaultdict(list)
        for path in KNOWLEDGE.rglob("*.md"):
            md_stems[path.stem].append(str(path.relative_to(KNOWLEDGE)))
        for stem, paths in md_stems.items():
            if len(paths) > 1:
                self.findings.duplicates.append(f"doc stem `{stem}` → {', '.join(paths[:5])}")

    def detect_circular(self) -> None:
        """Detect short cycles among application/ecosystem nodes (coarse, high-signal)."""
        apps = {
            f"applications.{a}" for a in (self.findings.inventory.get("applications") or [])
        }
        focus_nodes = set(apps) | {"ecosystem"}
        graph: dict[str, set[str]] = {n: set() for n in focus_nodes}
        for pkg, deps in self.import_graph.items():
            if pkg not in focus_nodes:
                continue
            for dep in deps:
                if dep in focus_nodes and dep != pkg:
                    graph[pkg].add(dep)

        cycles: set[str] = set()
        for start in sorted(focus_nodes):
            stack: list[str] = [start]
            visiting = {start}

            def dfs(node: str, depth: int) -> None:
                if depth > 6:
                    return
                for dep in graph.get(node, set()):
                    if dep == start and depth >= 1:
                        cycles.add(" → ".join(stack + [start]))
                        return
                    if dep in visiting:
                        continue
                    visiting.add(dep)
                    stack.append(dep)
                    dfs(dep, depth + 1)
                    stack.pop()
                    visiting.discard(dep)

            dfs(start, 0)

        self.findings.circular = sorted(cycles)[:30]

    def detect_orphans(self) -> None:
        # packages never imported by anyone else
        importers: dict[str, int] = defaultdict(int)
        for pkg, deps in self.import_graph.items():
            for d in deps:
                importers[d] += 1
        for plat in self.findings.inventory.get("platform_packages") or []:
            # some packages may only be entrypoints
            if importers.get(plat, 0) == 0 and plat not in {
                "platform_api",
                "platform_management",
                "platform_console",
                "platform_certification",
                "platform_legacy",
            }:
                self.findings.orphans.append(f"platform package rarely referenced: `{plat}`")
        # knowledge markdown with zero inbound wiki links
        inbound: dict[str, int] = defaultdict(int)
        notes = list(KNOWLEDGE.rglob("*.md"))
        for path in notes:
            text = path.read_text(errors="ignore")
            for target in WIKI_LINK_RE.findall(text):
                inbound[target.strip()] += 1
                inbound[Path(target.strip()).stem] += 1
        for path in notes:
            rel = str(path.relative_to(KNOWLEDGE))
            if rel.startswith("templates/"):
                continue
            stem = path.stem
            if inbound.get(stem, 0) == 0 and inbound.get(rel.replace(".md", ""), 0) == 0:
                # hubs and INDEX exempt-ish
                if stem in {"INDEX", "README", "Daily Note", "Documentation Page", "Sprint Page", "Agent Page"}:
                    continue
                if rel.count("/") >= 3 and "automation" in rel:
                    continue
                self.findings.dead_docs.append(rel)

    def detect_unused_apis(self) -> None:
        # Compare documented API prefixes vs references in knowledge
        api_registry = KNOWLEDGE / "registries" / "API_REGISTRY.md"
        documented: list[str] = []
        if api_registry.exists():
            documented = re.findall(r"`(/api/[^`]+)`", api_registry.read_text())
        corpus = ""
        for path in KNOWLEDGE.rglob("*.md"):
            if path.name == "API_REGISTRY.md":
                continue
            corpus += path.read_text(errors="ignore")
        for prefix in sorted(set(documented)):
            # count mentions outside registry
            if corpus.count(prefix) < 1:
                self.findings.unused_apis.append(f"Documented API rarely referenced elsewhere: `{prefix}`")

    def build_dependency_map(self) -> dict[str, list[str]]:
        deps: dict[str, list[str]] = {
            "platform_core": sorted(self.findings.inventory.get("platform_packages") or []),
            "applications": {},
            "shared_libraries": [],
            "plugins": [],
            "ai_agents": [],
        }  # type: ignore
        app_deps: dict[str, list[str]] = {}
        for app in self.findings.inventory.get("applications") or []:
            pkg = f"applications.{app}"
            raw = sorted(self.import_graph.get(pkg, set()))
            app_deps[app] = [
                d
                for d in raw
                if d.startswith("platform_")
                or d == "ecosystem"
                or d.startswith("applications.")
                or d in {"api", "services", "database"}
            ]
        deps["applications"] = app_deps  # type: ignore
        # shared
        for name in ("api", "services", "database", "plugins", "repositories"):
            if (REPO / name).exists():
                deps["shared_libraries"].append(name)
        plugins_dir = REPO / "plugins"
        if plugins_dir.exists():
            deps["plugins"] = sorted(
                p.name for p in plugins_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
            )
        agents_dir = KNOWLEDGE / "agents"
        if agents_dir.exists():
            deps["ai_agents"] = sorted(p.stem for p in agents_dir.glob("*.md"))
        # also map who depends on agents conceptually via imports of assistant modules
        self.findings.dependencies = deps  # type: ignore
        return deps  # type: ignore

    def quality_gates(self) -> dict[str, Any]:
        gates = {
            "folder_naming": {"pass": True, "issues": []},
            "module_naming": {"pass": True, "issues": []},
            "api_naming": {"pass": True, "issues": []},
            "documentation": {"pass": True, "issues": []},
            "wiki_links": {"pass": True, "issues": []},
            "mermaid_diagrams": {"pass": True, "issues": []},
            "dependency_rules": {"pass": True, "issues": []},
        }
        for v in self.findings.violations:
            if v.category in {"naming"}:
                gates["folder_naming"]["pass"] = False
                gates["folder_naming"]["issues"].append(v.message)
                gates["module_naming"]["pass"] = False
                gates["module_naming"]["issues"].append(v.message)
            if v.category in {"cross_app_import", "layering"}:
                gates["dependency_rules"]["pass"] = False
                gates["dependency_rules"]["issues"].append(v.message)
            if v.category == "missing_abstraction":
                gates["documentation"]["issues"].append(v.message)

        # API naming: prefixes should start with /api/
        api_file = KNOWLEDGE / "registries" / "API_REGISTRY.md"
        if api_file.exists():
            for prefix in re.findall(r"`(/[^`]+)`", api_file.read_text()):
                if prefix.startswith("/api/") or prefix.startswith("/management/") or prefix.startswith("/internal/"):
                    continue
                if prefix.startswith("/"):
                    gates["api_naming"]["issues"].append(f"Unusual prefix `{prefix}`")
        if gates["api_naming"]["issues"]:
            gates["api_naming"]["pass"] = False

        # mermaid presence
        mermaid_files = list((KNOWLEDGE / "diagrams").rglob("*.md")) if (KNOWLEDGE / "diagrams").exists() else []
        with_mermaid = 0
        for p in mermaid_files:
            if "```mermaid" in p.read_text(errors="ignore"):
                with_mermaid += 1
        if with_mermaid < 5:
            gates["mermaid_diagrams"]["pass"] = False
            gates["mermaid_diagrams"]["issues"].append(f"Only {with_mermaid} mermaid diagrams found")

        # wiki link health from validation report if present
        val = KNOWLEDGE / "VALIDATION_REPORT.md"
        if val.exists():
            text = val.read_text(errors="ignore")
            m = re.search(r"Broken wiki links:\s*\*\*(\d+)\*\*", text)
            if m and int(m.group(1)) > 50:
                gates["wiki_links"]["pass"] = False
                gates["wiki_links"]["issues"].append(f"High broken link count: {m.group(1)}")

        # documentation coverage gate
        inv = self.findings.inventory
        if inv.get("knowledge_md", 0) < 30:
            gates["documentation"]["pass"] = False
            gates["documentation"]["issues"].append("Knowledge markdown count below threshold")

        self.findings.gates = gates
        return gates

    def calculate_scores(self) -> dict[str, float]:
        inv = self.findings.inventory
        high = sum(1 for v in self.findings.violations if v.severity == "high")
        medium = sum(1 for v in self.findings.violations if v.severity == "medium")
        low = sum(1 for v in self.findings.violations if v.severity == "low")

        # Architecture quality: start 100, subtract
        arch = 100.0 - high * 8 - medium * 3 - low * 1
        arch -= min(15, len(self.findings.circular) * 5)
        arch -= min(10, len(self.findings.misplaced) * 4)
        arch = max(0.0, min(100.0, arch))

        # Documentation coverage heuristic
        md = inv.get("knowledge_md", 0)
        doc = min(100.0, md / 1.2)  # ~120 pages => 100
        # boost if dashboards exist
        for name in ("INDEX.md", "DASHBOARD.md", "ARCHITECTURE_CHANGES.md"):
            if (KNOWLEDGE / name).exists():
                doc = min(100.0, doc + 2)

        # Cohesion: apps with bridges / total apps
        apps = inv.get("applications") or []
        with_bridge = 0
        for app in apps:
            if (REPO / "applications" / app / "integrations").exists():
                with_bridge += 1
        cohesion = 100.0 * with_bridge / max(len(apps), 1)

        # Coupling: average external deps per app (lower better) mapped to score
        app_deps = (self.findings.dependencies or {}).get("applications") or {}
        if isinstance(app_deps, dict) and app_deps:
            avg = sum(len(v) for v in app_deps.values()) / len(app_deps)
            coupling = max(0.0, 100.0 - avg * 8)
        else:
            coupling = 70.0

        # Maintainability: tests ratio
        py_files = max(inv.get("python_files", 1), 1)
        test_files = inv.get("test_files", 0)
        maintainability = min(100.0, (test_files / py_files) * 100 * 3)  # scale

        # Complexity: package count pressure (platform packages are expected to be many)
        plat_n = len(inv.get("platform_packages") or [])
        complexity = max(35.0, 100.0 - max(0, plat_n - 35) * 1.5 - len(self.findings.circular) * 4)

        # Scalability: apps commercial + layered architecture present
        scalability = 60.0
        if (REPO / "ecosystem").exists():
            scalability += 15
        if len(apps) >= 3:
            scalability += 15
        if (KNOWLEDGE / "tools" / "architecture_guardian.py").exists():
            scalability += 10
        scalability = min(100.0, scalability)

        # Risk index: driven by high violations + focused cycles (lower better)
        risk = min(100.0, high * 12 + medium * 3 + len(self.findings.circular) * 8 + len(self.findings.misplaced) * 5)
        risk = round(max(5.0, risk), 1)

        scores = {
            "architecture_quality": round(arch, 1),
            "documentation_coverage": round(min(100.0, doc), 1),
            "module_cohesion": round(cohesion, 1),
            "coupling": round(coupling, 1),
            "maintainability": round(maintainability, 1),
            "complexity": round(complexity, 1),
            "scalability": round(scalability, 1),
            "risk_index": round(risk, 1),
        }
        # composite
        scores["overall"] = round(
            (
                scores["architecture_quality"] * 0.25
                + scores["documentation_coverage"] * 0.15
                + scores["module_cohesion"] * 0.1
                + scores["coupling"] * 0.1
                + scores["maintainability"] * 0.15
                + scores["complexity"] * 0.1
                + scores["scalability"] * 0.15
            ),
            1,
        )
        self.findings.scores = scores
        return scores

    # ------------------------------------------------------------------
    # Writers
    # ------------------------------------------------------------------
    def write_dependency_report(self) -> Path:
        deps = self.findings.dependencies
        app_deps = deps.get("applications") or {}
        app_blocks = []
        if isinstance(app_deps, dict):
            for app, items in sorted(app_deps.items()):
                app_blocks.append(f"#### {app}")
                app_blocks.extend(bullets(items, empty="- (no project deps detected)"))
                app_blocks.append("")
        path = write_md(
            "DEPENDENCY_REPORT.md",
            frontmatter("Dependency Report", ["Dependency Report"], ["architecture", "knowledge-1.3"])
            + "# Dependency Report\n\n"
            + std_sections(
                overview=f"Dependency analysis generated {NOW} by Architecture Guardian (read-only).",
                architecture="Coarse package import graph across Platform Core, Ecosystem, and applications.",
                components=NL.join(
                    [
                        "### Platform Core dependencies (packages)",
                        *bullets(deps.get("platform_core") or []),
                        "",
                        "### Application dependencies",
                        *(app_blocks if app_blocks else ["- None"]),
                        "",
                        "### Shared libraries",
                        *bullets(deps.get("shared_libraries") or []),
                        "",
                        "### Plugin dependencies",
                        *bullets(deps.get("plugins") or []),
                        "",
                        "### AI Agent dependencies (documented)",
                        *bullets(deps.get("ai_agents") or []),
                    ]
                ),
                relationships="[[ARCHITECTURE]] · [[diagrams/automation/DEPENDENCY_GRAPH]] · [[ARCHITECT_RECOMMENDATIONS]]",
                responsibilities="Expose layer coupling for architecture reviews.",
                interfaces="`python3 knowledge/tools/architecture_check.py`",
                rest_apis="API surfaces tracked separately in [[registries/API_REGISTRY]]",
                events="dependency_report_generated",
                roadmap="[[ROADMAP]]",
                references="AST import scan (bounded)",
                related="[[PROJECT_HEALTH]] · [[TECHNICAL_DEBT]] · [[INDEX]]",
            ),
        )
        self.written.append("DEPENDENCY_REPORT.md")
        return path

    def write_recommendations(self) -> Path:
        recs = []
        if self.findings.circular:
            recs.append("**Refactoring:** break circular package dependencies listed in Components.")
        if self.findings.missing_abstractions:
            recs.append("**Abstractions:** add `integrations/` bridges for apps missing them.")
        if any(v.category == "cross_app_import" for v in self.findings.violations):
            recs.append("**Module split / boundaries:** replace cross-app imports with explicit bridge facades.")
        if self.findings.orphans:
            recs.append("**Optimization:** review orphan platform packages for consolidation or clearer entrypoints.")
        if self.findings.dead_docs:
            recs.append("**Documentation:** link or archive dead knowledge pages to reduce vault noise.")
        if self.findings.scores.get("maintainability", 0) < 50:
            recs.append("**Tests:** increase automated test coverage near domain facades.")
        if self.findings.scores.get("coupling", 100) < 60:
            recs.append("**Coupling:** reduce wide imports; prefer narrow bridge interfaces.")
        recs.append("**Future:** federate app knowledge graphs into Ecosystem global knowledge (see [[ROADMAP]]).")
        recs.append("**Future:** keep Architecture Guardian in CI via `full_architecture_review.py`.")

        path = write_md(
            "ARCHITECT_RECOMMENDATIONS.md",
            frontmatter(
                "Architect Recommendations",
                ["Architect Recommendations", "AI Recommendations"],
                ["architecture", "recommendations", "knowledge-1.3"],
            )
            + "# Architect Recommendations\n\n"
            + std_sections(
                overview="AI Project Architect recommendations based on guardian findings.",
                architecture="Prioritize dependency rules (bridges only) and documentation graph hygiene.",
                components=NL.join(
                    [
                        "### Suggested actions",
                        *bullets(recs),
                        "",
                        "### Suggested refactoring targets",
                        *bullets(self.findings.circular[:20], empty="- No circular deps detected"),
                        "",
                        "### Suggested module / abstraction work",
                        *bullets(self.findings.missing_abstractions[:20]),
                        "",
                        "### Misplaced code",
                        *bullets(self.findings.misplaced[:20]),
                    ]
                ),
                relationships="[[TECHNICAL_DEBT]] · [[DEPENDENCY_REPORT]] · [[PROJECT_HEALTH]]",
                responsibilities="Guide safe architectural evolution without runtime code edits from knowledge tools.",
                interfaces="`python3 knowledge/tools/recommendations.py`",
                rest_apis="N/A",
                events="recommendations_generated",
                roadmap="[[ROADMAP]]",
                references="Architecture Guardian findings",
                related="[[ARCHITECTURE_HISTORY]] · [[EXECUTIVE_DASHBOARD]] · [[INDEX]]",
            ),
        )
        self.written.append("ARCHITECT_RECOMMENDATIONS.md")
        return path

    def write_technical_debt(self) -> Path:
        high, medium, low = [], [], []
        for v in self.findings.violations:
            item = f"{v.category}: {v.message}" + (f" (`{v.path}`)" if v.path else "")
            if v.severity == "high":
                high.append(item)
            elif v.severity == "medium":
                medium.append(item)
            else:
                low.append(item)
        for c in self.findings.circular:
            high.append(f"circular_dependency: {c}")
        for d in self.findings.dead_docs[:30]:
            low.append(f"dead_documentation: {d}")
        for o in self.findings.orphans[:20]:
            medium.append(o)

        effort = {
            "high": f"{max(1, len(high)) * 2}–{max(2, len(high) * 4)} engineering-hours (est.)",
            "medium": f"{max(1, len(medium))}–{max(2, len(medium) * 2)} engineering-hours (est.)",
            "low": f"{max(1, len(low) // 2)}–{max(1, len(low))} engineering-hours (est.)",
        }
        path = write_md(
            "TECHNICAL_DEBT.md",
            frontmatter("Technical Debt", ["Technical Debt"], ["debt", "architecture", "knowledge-1.3"])
            + "# Technical Debt\n\n"
            + std_sections(
                overview=f"Technical debt register generated {NOW} from Architecture Guardian.",
                architecture="Debt is classified by severity; knowledge tools only document — they do not auto-refactor runtime code.",
                components=NL.join(
                    [
                        "### High priority",
                        *bullets(high[:40]),
                        f"**Estimated effort:** {effort['high']}",
                        "",
                        "### Medium priority",
                        *bullets(medium[:40]),
                        f"**Estimated effort:** {effort['medium']}",
                        "",
                        "### Low priority",
                        *bullets(low[:40]),
                        f"**Estimated effort:** {effort['low']}",
                    ]
                ),
                relationships="[[ARCHITECT_RECOMMENDATIONS]] · [[PROJECT_HEALTH]] · [[DEPENDENCY_REPORT]]",
                responsibilities="Make debt visible for sprint planning.",
                interfaces="`python3 knowledge/tools/technical_debt.py`",
                rest_apis="N/A",
                events="technical_debt_updated",
                roadmap="[[ROADMAP]]",
                references="Guardian violations + circular/orphan/dead-doc detectors",
                related="[[EXECUTIVE_DASHBOARD]] · [[INDEX]]",
            ),
        )
        self.written.append("TECHNICAL_DEBT.md")
        return path

    def write_project_health(self) -> Path:
        s = self.findings.scores
        inv = self.findings.inventory
        gates = self.findings.gates
        gate_rows = [
            f"| {name} | {'✅ PASS' if g.get('pass') else '❌ FAIL'} | {len(g.get('issues') or [])} |"
            for name, g in gates.items()
        ]
        path = write_md(
            "PROJECT_HEALTH.md",
            frontmatter("Project Health", ["Project Health"], ["health", "architecture", "knowledge-1.3"])
            + "# Project Health\n\n"
            + std_sections(
                overview=f"Project health dashboard snapshot {NOW}.",
                architecture="Composite of architecture scores, inventory, and quality gates.",
                components=NL.join(
                    [
                        "### Scores",
                        "| Metric | Score |",
                        "|--------|------:|",
                        f"| Overall | **{s.get('overall', 0)}** |",
                        f"| Architecture quality | {s.get('architecture_quality', 0)} |",
                        f"| Documentation coverage | {s.get('documentation_coverage', 0)}% |",
                        f"| Module cohesion | {s.get('module_cohesion', 0)} |",
                        f"| Coupling (higher=better isolation) | {s.get('coupling', 0)} |",
                        f"| Maintainability | {s.get('maintainability', 0)} |",
                        f"| Complexity | {s.get('complexity', 0)} |",
                        f"| Scalability | {s.get('scalability', 0)} |",
                        f"| Risk index (lower better) | {s.get('risk_index', 0)} |",
                        "",
                        "### Inventory",
                        f"- Platform packages: {len(inv.get('platform_packages') or [])}",
                        f"- Applications: {len(inv.get('applications') or [])}",
                        f"- Ecosystem modules: {len(inv.get('ecosystem_modules') or [])}",
                        f"- Python files: {inv.get('python_files', 0)}",
                        f"- Test files: {inv.get('test_files', 0)}",
                        f"- Knowledge markdown: {inv.get('knowledge_md', 0)}",
                        f"- Documented agents: {inv.get('agents_documented', 0)}",
                        "",
                        "### Quality gates",
                        "| Gate | Status | Issues |",
                        "|------|--------|-------:|",
                        *gate_rows,
                    ]
                ),
                relationships="[[EXECUTIVE_DASHBOARD]] · [[TECHNICAL_DEBT]] · [[ARCHITECT_RECOMMENDATIONS]]",
                responsibilities="Provide a single health artifact for executives and architects.",
                interfaces="`python3 knowledge/tools/project_health.py`",
                rest_apis="[[registries/API_REGISTRY]]",
                events="project_health_updated",
                roadmap="[[ROADMAP]]",
                references="Architecture Guardian",
                related="[[DASHBOARD]] · [[INDEX]] · [[VALIDATION_REPORT]]",
            ),
        )
        self.written.append("PROJECT_HEALTH.md")
        return path

    def write_architecture_history(self) -> Path:
        history = load_json(HISTORY_PATH, {"entries": []})
        entry = {
            "at": NOW_ISO,
            "sprint": "Knowledge 1.3",
            "scores": self.findings.scores,
            "applications": self.findings.inventory.get("applications"),
            "platform_count": len(self.findings.inventory.get("platform_packages") or []),
            "violations": len(self.findings.violations),
            "circular": len(self.findings.circular),
            "knowledge_md": self.findings.inventory.get("knowledge_md"),
            "registry_version": (self.registry.get("meta") or {}).get("version"),
        }
        history.setdefault("entries", []).append(entry)
        # keep last 50
        history["entries"] = history["entries"][-50:]
        save_json(HISTORY_PATH, history)

        rows = []
        for e in history["entries"][-15:]:
            sc = e.get("scores") or {}
            rows.append(
                f"| {e.get('at', '')[:10]} | {e.get('sprint')} | {sc.get('overall', '—')} | "
                f"{sc.get('architecture_quality', '—')} | {e.get('violations')} | {e.get('platform_count')} | "
                f"{len(e.get('applications') or [])} | {e.get('knowledge_md')} |"
            )

        path = write_md(
            "ARCHITECTURE_HISTORY.md",
            frontmatter(
                "Architecture History",
                ["Architecture History", "Evolution Tracker"],
                ["history", "architecture", "knowledge-1.3"],
            )
            + "# Architecture History\n\n"
            + std_sections(
                overview="Evolution tracker for modules, sprints, versions, and architecture scores.",
                architecture="Append-only history stored in `knowledge/data/architecture_history.json`.",
                components=NL.join(
                    [
                        "### Recent evolution",
                        "| Date | Sprint | Overall | Arch | Violations | Platform pkgs | Apps | Docs |",
                        "|------|--------|--------:|-----:|-----------:|--------------:|-----:|-----:|",
                        * (rows if rows else ["| — | — | — | — | — | — | — | — |"]),
                        "",
                        "### Sprint evolution (registry)",
                        *bullets(
                            f"{s.get('id')}: {s.get('stream')} — {s.get('status')}"
                            for s in (self.registry.get("sprints") or [])[-12:]
                        ),
                        "",
                        "### Version evolution",
                        f"- Registry meta version: `{(self.registry.get('meta') or {}).get('version')}`",
                        f"- Platform Core: `{(self.registry.get('meta') or {}).get('platform_core')}`",
                        f"- Ecosystem: `{(self.registry.get('meta') or {}).get('ecosystem')}`",
                    ]
                ),
                relationships="[[PLATFORM_TIMELINE]] · [[registries/SPRINT_REGISTRY]] · [[PROJECT_HEALTH]]",
                responsibilities="Track architecture change over time.",
                interfaces="Guardian persists history on each full review.",
                rest_apis="N/A",
                events="architecture_history_appended",
                roadmap="[[ROADMAP]]",
                references="`architecture_history.json`",
                related="[[ARCHITECTURE_CHANGES]] · [[INDEX]]",
            ),
        )
        self.written.append("ARCHITECTURE_HISTORY.md")
        return path

    def write_guardian_summary(self) -> Path:
        path = write_md(
            "reports/ARCHITECTURE_GUARDIAN.md",
            frontmatter("Architecture Guardian Report", ["Architecture Guardian"], ["guardian", "knowledge-1.3"])
            + "# Architecture Guardian Report\n\n"
            + std_sections(
                overview="Summary of architectural violations and detector results.",
                architecture="Detectors: violations, duplicates, circular deps, abstractions, misplaced code, orphans, unused APIs, dead docs.",
                components=NL.join(
                    [
                        f"- Violations: **{len(self.findings.violations)}**",
                        f"- Circular dependency chains: **{len(self.findings.circular)}**",
                        f"- Duplicate doc stems: **{len(self.findings.duplicates)}**",
                        f"- Missing abstractions: **{len(self.findings.missing_abstractions)}**",
                        f"- Misplaced code signals: **{len(self.findings.misplaced)}**",
                        f"- Orphan signals: **{len(self.findings.orphans)}**",
                        f"- Unused API doc signals: **{len(self.findings.unused_apis)}**",
                        f"- Dead documentation candidates: **{len(self.findings.dead_docs)}**",
                        "",
                        "### Violations (sample)",
                        *bullets(
                            f"[{v.severity}] {v.category}: {v.message}"
                            for v in self.findings.violations[:40]
                        ),
                        "",
                        "### Circular",
                        *bullets(self.findings.circular[:20]),
                    ]
                ),
                relationships="[[DEPENDENCY_REPORT]] · [[TECHNICAL_DEBT]] · [[ARCHITECT_RECOMMENDATIONS]]",
                responsibilities="Continuously validate AI Ecosystem architecture rules.",
                interfaces="`python3 knowledge/tools/architecture_check.py`",
                rest_apis="N/A (analysis only)",
                events="architecture_check_completed",
                roadmap="[[ROADMAP]]",
                references="[[automation/ARCHITECTURE_GUARDIAN]]",
                related="[[PROJECT_HEALTH]] · [[INDEX]]",
            ),
        )
        self.written.append("reports/ARCHITECTURE_GUARDIAN.md")
        return path

    def update_dashboards(self) -> list[Path]:
        s = self.findings.scores
        risk = s.get("risk_index", 0)
        risk_level = "Low" if risk < 30 else "Medium" if risk < 60 else "High"
        sprints = self.registry.get("sprints") or []
        completed = [x for x in sprints if x.get("status") == "completed"]
        planned = [x for x in sprints if x.get("status") == "planned"]
        pct = round(100 * len(completed) / max(len(sprints), 1), 1)

        updates = {
            "EXECUTIVE_DASHBOARD.md": (
                "Executive Dashboard",
                ["Executive Dashboard"],
                NL.join(
                    [
                        "### Architecture & health (Knowledge 1.3)",
                        f"- **Architecture score:** {s.get('architecture_quality')} / 100",
                        f"- **Overall project score:** {s.get('overall')}",
                        f"- **Documentation coverage:** {s.get('documentation_coverage')}%",
                        f"- **Risk level:** {risk_level} (index {risk})",
                        f"- **Technical debt:** [[TECHNICAL_DEBT]]",
                        f"- **Project health:** [[PROJECT_HEALTH]]",
                        f"- **Roadmap completed:** {pct}% of tracked sprints",
                        "",
                        "### Upcoming milestones",
                        *bullets(
                            f"{p.get('id')} — {p.get('purpose')}" for p in planned[:6]
                        ),
                        "",
                        "### Completed roadmap (recent)",
                        *bullets(
                            f"{c.get('id')} — {c.get('stream')}" for c in completed[-8:]
                        ),
                        "",
                        "[[ARCHITECT_RECOMMENDATIONS]] · [[DEPENDENCY_REPORT]] · [[ARCHITECTURE_HISTORY]]",
                    ]
                ),
            ),
            "DASHBOARD.md": (
                "Dashboard",
                ["Dashboard"],
                NL.join(
                    [
                        "| Metric | Value |",
                        "|--------|------:|",
                        f"| Architecture quality | {s.get('architecture_quality')} |",
                        f"| Documentation % | {s.get('documentation_coverage')} |",
                        f"| Risk index | {risk} |",
                        f"| Overall score | {s.get('overall')} |",
                        f"| Sprint completion | {pct}% |",
                        "",
                        "[[PROJECT_HEALTH]] · [[TECHNICAL_DEBT]] · [[reports/ARCHITECTURE_GUARDIAN]] · [[ARCHITECT_RECOMMENDATIONS]]",
                    ]
                ),
            ),
            "ARCHITECTURE_DASHBOARD.md": (
                "Architecture Dashboard",
                ["Architecture Dashboard"],
                NL.join(
                    [
                        f"**Architecture Quality Score:** {s.get('architecture_quality')}",
                        f"**Coupling / Cohesion:** {s.get('coupling')} / {s.get('module_cohesion')}",
                        f"**Risk:** {risk_level}",
                        "",
                        "### Guardian outputs",
                        "[[DEPENDENCY_REPORT]] · [[ARCHITECT_RECOMMENDATIONS]] · [[TECHNICAL_DEBT]] · [[PROJECT_HEALTH]] · [[ARCHITECTURE_HISTORY]]",
                        "[[reports/ARCHITECTURE_GUARDIAN]] · [[automation/ARCHITECTURE_GUARDIAN]]",
                        "",
                        "### Graphs",
                        "[[diagrams/automation/DEPENDENCY_GRAPH]] · [[diagrams/automation/ARCHITECTURE_GRAPH]]",
                    ]
                ),
            ),
            "PROJECT_STATUS.md": (
                "Project Status",
                ["Project Status"],
                NL.join(
                    [
                        f"| Architecture score | {s.get('architecture_quality')} |",
                        f"| Documentation % | {s.get('documentation_coverage')} |",
                        f"| Risk | {risk_level} |",
                        f"| Knowledge sprint | 1.3 Architecture Guardian |",
                        "",
                        "See [[PROJECT_HEALTH]] for full metrics.",
                    ]
                ),
            ),
            "INDEX.md": (
                "INDEX",
                ["Home", "Knowledge Home"],
                NL.join(
                    [
                        "**Knowledge 1.3** — AI Project Architect & Architecture Guardian enabled.",
                        "",
                        f"- Architecture score: **{s.get('architecture_quality')}** · Overall: **{s.get('overall')}** · Risk: **{risk_level}**",
                        f"- Documentation coverage: **{s.get('documentation_coverage')}%** · Sprint completion: **{pct}%**",
                        "",
                        "### Architect suite",
                        "[[PROJECT_HEALTH]] · [[DEPENDENCY_REPORT]] · [[ARCHITECT_RECOMMENDATIONS]] · [[TECHNICAL_DEBT]] · [[ARCHITECTURE_HISTORY]]",
                        "[[reports/ARCHITECTURE_GUARDIAN]] · [[automation/ARCHITECTURE_GUARDIAN]]",
                        "",
                        "### Dashboards",
                        "[[DASHBOARD]] · [[EXECUTIVE_DASHBOARD]] · [[ARCHITECTURE_DASHBOARD]] · [[PROJECT_STATUS]] · [[SPRINT_PROGRESS]]",
                    ]
                ),
            ),
        }
        paths = []
        for rel, (title, aliases, components) in updates.items():
            p = write_md(
                rel,
                frontmatter(title, aliases, ["dashboard", "knowledge-1.3"])
                + f"# {title}\n\n"
                + std_sections(
                    overview=f"Auto-updated for Knowledge 1.3 Architecture Guardian — {title}.",
                    architecture="Scores and health derived from read-only repository analysis.",
                    components=components,
                    relationships="[[automation/ARCHITECTURE_GUARDIAN]] · [[PROJECT_HEALTH]]",
                    responsibilities="Surface architecture quality to the vault.",
                    interfaces="`full_architecture_review.py`",
                    rest_apis="[[registries/API_REGISTRY]]",
                    events="dashboard_updated_from_guardian",
                    roadmap="[[ROADMAP]]",
                    references="Architecture scores JSON",
                    related="[[INDEX]] · [[TECHNICAL_DEBT]]",
                ),
            )
            paths.append(p)
            self.written.append(rel)
        return paths

    def update_registry_meta(self) -> None:
        reg = self.registry or {}
        reg.setdefault("meta", {})
        reg["meta"].update(
            {
                "sprint": "Knowledge 1.3",
                "title": "AI Project Architect & Architecture Guardian",
                "status": "completed",
                "version": "1.3.0",
            }
        )
        sprints = reg.setdefault("sprints", [])
        if not any(s.get("id") == "K1.3" for s in sprints):
            sprints.append(
                {
                    "id": "K1.3",
                    "stream": "Knowledge",
                    "purpose": "AI Project Architect & Architecture Guardian",
                    "version": "1.3.0",
                    "status": "completed",
                    "deps": ["K1.2"],
                }
            )
        self.registry = reg
        save_json(REGISTRY_PATH, reg)

    def maintain_obsidian(self) -> None:
        bookmarks = load_json(OBSIDIAN / "bookmarks.json", {"items": []})
        items = bookmarks.get("items") or []
        wanted = [
            ("knowledge/PROJECT_HEALTH.md", "Project Health"),
            ("knowledge/DEPENDENCY_REPORT.md", "Dependency Report"),
            ("knowledge/ARCHITECT_RECOMMENDATIONS.md", "Architect Recommendations"),
            ("knowledge/TECHNICAL_DEBT.md", "Technical Debt"),
            ("knowledge/ARCHITECTURE_HISTORY.md", "Architecture History"),
            ("knowledge/automation/ARCHITECTURE_GUARDIAN.md", "Architecture Guardian"),
        ]
        existing = {i.get("path") for i in items}
        ctime = 1721652000000
        for path, title in wanted:
            if path not in existing:
                items.append({"type": "file", "ctime": ctime, "path": path, "title": title})
                ctime += 1
        bookmarks["items"] = items
        OBSIDIAN.mkdir(parents=True, exist_ok=True)
        save_json(OBSIDIAN / "bookmarks.json", bookmarks)
        graph = load_json(OBSIDIAN / "graph.json", {})
        groups = graph.get("colorGroups") or []
        if not any("knowledge-1.3" in json.dumps(g) for g in groups):
            groups.append({"query": "tag:#knowledge-1.3", "color": {"a": 1, "rgb": 20}})
            graph["colorGroups"] = groups
            save_json(OBSIDIAN / "graph.json", graph)

    # ------------------------------------------------------------------
    # Pipelines
    # ------------------------------------------------------------------
    def analyze(self) -> ArchitectureFindings:
        self.inventory()
        self.build_import_graph()
        self.build_dependency_map()
        self.detect_violations()
        self.detect_duplicates()
        self.detect_circular()
        self.detect_orphans()
        self.detect_unused_apis()
        self.quality_gates()
        self.calculate_scores()
        return self.findings

    def architecture_check(self) -> dict[str, Any]:
        self.analyze()
        self.write_guardian_summary()
        self.write_dependency_report()
        save_json(SCORES_PATH, {"at": NOW_ISO, "scores": self.findings.scores, "gates": self.findings.gates})
        return self.summary()

    def project_health(self) -> dict[str, Any]:
        self.analyze()
        self.write_project_health()
        self.update_dashboards()
        return self.summary()

    def technical_debt(self) -> dict[str, Any]:
        self.analyze()
        self.write_technical_debt()
        return self.summary()

    def recommendations(self) -> dict[str, Any]:
        self.analyze()
        self.write_recommendations()
        return self.summary()

    def full_review(self) -> dict[str, Any]:
        self.analyze()
        self.update_registry_meta()
        self.write_guardian_summary()
        self.write_dependency_report()
        self.write_recommendations()
        self.write_technical_debt()
        self.write_project_health()
        self.write_architecture_history()
        self.update_dashboards()
        self.maintain_obsidian()
        save_json(SCORES_PATH, {"at": NOW_ISO, "scores": self.findings.scores, "gates": self.findings.gates})
        return self.summary()

    def summary(self) -> dict[str, Any]:
        return {
            "sprint": "Knowledge 1.3",
            "generated": NOW_ISO,
            "scores": self.findings.scores,
            "violations": len(self.findings.violations),
            "circular": len(self.findings.circular),
            "written": self.written,
        }


def main() -> None:
    result = ArchitectureGuardian().full_review()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
