#!/usr/bin/env python3
"""Knowledge Sprint 2.0 — Enterprise Development Infrastructure.

Generates GitHub automation docs, architecture visualizations, analytics
dashboards, developer portal, and release pipeline artifacts under
knowledge/. Also syncs non-runtime GitHub templates into .github/.

Does NOT modify Platform Core, applications, APIs, or business logic.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
KNOWLEDGE = REPO / "knowledge"
GITHUB_DIR = REPO / ".github"
OBSIDIAN = REPO / ".obsidian"
DATA = KNOWLEDGE / "data"
REGISTRY = DATA / "ecosystem_registry.json"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")
NOW_ISO = datetime.now(timezone.utc).isoformat()
NL = "\n"
VERSION = "2.0.0"


def run_git(*args: str) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text())
    except Exception:
        return {} if default is None else default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def write(rel: str | Path, content: str, *, root: Path = KNOWLEDGE) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n")
    return path


def fm(title: str, aliases: list[str], tags: list[str]) -> str:
    al = NL.join(f"  - {a}" for a in aliases)
    tg = NL.join(f"  - {t}" for t in tags)
    return (
        f"---\ntitle: {title}\naliases:\n{al}\ntags:\n{tg}\n"
        f"generated: {NOW}\nsprint: Knowledge 2.0\nversion: {VERSION}\n---\n"
    )


def page(title: str, aliases: list[str], tags: list[str], overview: str, components: str, **extra: str) -> str:
    return (
        fm(title, aliases, tags)
        + f"# {title}\n\n"
        + f"## Overview\n{overview}\n\n"
        + f"## Architecture\n{extra.get('architecture', 'Part of Enterprise Development Infrastructure (Knowledge 2.0).')}\n\n"
        + f"## Components\n{components}\n\n"
        + f"## Relationships\n{extra.get('relationships', '[[INDEX]] · [[dashboard/README]] · [[pipeline/README]]')}\n\n"
        + f"## Responsibilities\n{extra.get('responsibilities', 'Provide enterprise development infrastructure without changing runtime logic.')}\n\n"
        + f"## Interfaces\n{extra.get('interfaces', 'Markdown + generators under `knowledge/tools/`.')}\n\n"
        + f"## REST APIs\n{extra.get('rest_apis', 'N/A — documentation/infrastructure only.')}\n\n"
        + f"## Events\n{extra.get('events', 'generated_by_enterprise_infra')}\n\n"
        + f"## Future roadmap\n{extra.get('roadmap', '[[ROADMAP]]')}\n\n"
        + f"## References\n{extra.get('references', '[[automation/ENTERPRISE_INFRASTRUCTURE]]')}\n\n"
        + f"## Related pages\n{extra.get('related', '[[INDEX]] · [[PROJECT_STATUS]] · [[EXECUTIVE_DASHBOARD]]')}\n"
    )


def bullets(items: list[str], empty: str = "- None") -> str:
    return NL.join(f"- {i}" if not str(i).startswith("- ") else str(i) for i in items) if items else empty


class EnterpriseInfrastructure:
    def __init__(self) -> None:
        self.registry = load_json(REGISTRY, {})
        self.scores = load_json(DATA / "architecture_scores.json", {})
        self.written: list[str] = []
        self.stats = self._collect_stats()

    def _collect_stats(self) -> dict[str, Any]:
        def count_glob(pattern: str) -> int:
            return sum(1 for p in REPO.glob(pattern) if ".venv" not in str(p) and "node_modules" not in str(p))

        apps = sorted(
            p.name for p in (REPO / "applications").iterdir()
            if p.is_dir() and not p.name.startswith(".")
        ) if (REPO / "applications").exists() else []
        platform = sorted(
            p.name for p in REPO.iterdir() if p.is_dir() and p.name.startswith("platform_")
        )
        py_files = [p for p in REPO.rglob("*.py") if ".venv" not in p.parts and "venv" not in p.parts]
        test_files = [p for p in py_files if "test" in p.name or "tests" in p.parts]
        loc = 0
        for p in py_files[:5000]:
            try:
                loc += sum(1 for _ in p.open(errors="ignore"))
            except Exception:
                pass
        md = list(KNOWLEDGE.rglob("*.md")) if KNOWLEDGE.exists() else []
        agents = list((KNOWLEDGE / "agents").glob("*.md")) if (KNOWLEDGE / "agents").exists() else []
        commits = run_git("rev-list", "--count", "HEAD") or "0"
        branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
        latest = run_git("log", "-1", "--pretty=%h %s")
        tags = [t for t in run_git("tag", "--sort=-creatordate").splitlines() if t][:15]
        log = [l for l in run_git("log", "-20", "--pretty=%h %ad %s", "--date=short").splitlines() if l]
        return {
            "applications": apps,
            "platform_packages": platform,
            "python_files": len(py_files),
            "test_files": len(test_files),
            "loc_sample": loc,
            "knowledge_md": len(md),
            "agents": len(agents),
            "commits": int(commits) if commits.isdigit() else 0,
            "branch": branch,
            "latest": latest,
            "tags": tags,
            "recent_log": log,
            "sprints": self.registry.get("sprints") or [],
        }

    def _track(self, path: Path) -> None:
        try:
            self.written.append(str(path.relative_to(REPO)))
        except ValueError:
            self.written.append(str(path))

    # ------------------------------------------------------------------
    # 2.1 GitHub Enterprise
    # ------------------------------------------------------------------
    def generate_github(self) -> None:
        root = "github"
        stats = self.stats
        scores = (self.scores.get("scores") or self.scores)

        pages = {
            f"{root}/README.md": page(
                "GitHub Enterprise Automation",
                ["GitHub Enterprise", "GitHub Automation"],
                ["github", "knowledge-2.0"],
                "Knowledge 2.1 — GitHub enterprise automation pack for releases, tags, milestones, templates, and repository health.",
                bullets([
                    "[[github/RELEASE_GENERATOR]]",
                    "[[github/CHANGELOG_AUTOMATION]]",
                    "[[github/SEMANTIC_VERSIONING]]",
                    "[[github/TAG_GENERATOR]]",
                    "[[github/RELEASE_NOTES_GENERATOR]]",
                    "[[github/MILESTONE_GENERATOR]]",
                    "[[github/REPOSITORY_HEALTH]]",
                    "[[github/CONTRIBUTION_STATS]]",
                    "[[github/REPOSITORY_DASHBOARD]]",
                    "[[github/README_UPDATER]]",
                    "[[github/BADGES]]",
                    "Templates synced to `.github/`",
                ]),
                architecture="Source-of-truth docs live in `knowledge/github/`; GitHub-native files under `.github/`.",
                interfaces="`python3 knowledge/tools/generate_github.py`",
            ),
            f"{root}/RELEASE_GENERATOR.md": page(
                "GitHub Release Generator",
                ["Release Generator"],
                ["github", "release", "knowledge-2.0"],
                "Documents how to cut GitHub Releases from Knowledge version metadata.",
                bullets([
                    f"Current knowledge version: `{VERSION}`",
                    f"Latest commit: `{stats['latest']}`",
                    "Uses [[github/RELEASE_NOTES_GENERATOR]] + [[releases/RELEASE_NOTES]]",
                    "Suggested tag: `knowledge-v2.0.0`",
                    "Command sketch: `gh release create knowledge-v2.0.0 -F knowledge/releases/RELEASE_NOTES.md`",
                ]),
            ),
            f"{root}/CHANGELOG_AUTOMATION.md": page(
                "Automatic CHANGELOG Generation",
                ["CHANGELOG Automation"],
                ["github", "changelog", "knowledge-2.0"],
                "CHANGELOG is regenerated by Knowledge tools from registry + git log.",
                bullets([
                    "Primary: [[CHANGELOG]]",
                    "Engine: Documentation Assistant + Enterprise Infra",
                    "Git history sample:",
                    *stats["recent_log"][:8],
                ]),
            ),
            f"{root}/SEMANTIC_VERSIONING.md": page(
                "Semantic Version Manager",
                ["Semantic Versioning", "SemVer"],
                ["github", "versioning", "knowledge-2.0"],
                "Semantic version policy for Knowledge infrastructure and guidance for apps.",
                bullets([
                    "Knowledge MAJOR.MINOR.PATCH — current **2.0.0**",
                    "MAJOR: enterprise infra / incompatible doc contracts",
                    "MINOR: additive generators/dashboards",
                    "PATCH: fixes to docs/automation",
                    f"Platform Core remains `{self.registry.get('meta', {}).get('platform_core', '3.0.0')}`",
                    "Version file: `knowledge/data/ecosystem_registry.json` meta.version",
                ]),
            ),
            f"{root}/TAG_GENERATOR.md": page(
                "Git Tag Generator",
                ["Tag Generator"],
                ["github", "tags", "knowledge-2.0"],
                "Tag naming conventions and existing tags.",
                bullets([
                    "Convention: `knowledge-vX.Y.Z`, `platform-vX.Y.Z`, app tags as needed",
                    "Existing tags:",
                    *(stats["tags"] or ["(none)"]),
                    "Suggested next: `knowledge-v2.0.0`",
                ]),
            ),
            f"{root}/RELEASE_NOTES_GENERATOR.md": page(
                "Release Notes Generator",
                ["GH Release Notes Generator"],
                ["github", "release-notes", "knowledge-2.0"],
                "Release notes pipeline for GitHub Releases.",
                bullets([
                    "Canonical notes: [[releases/RELEASE_NOTES]]",
                    "CLI: `python3 knowledge/tools/release_notes.py`",
                    "Enterprise refresh: `python3 knowledge/tools/knowledge20_update.py`",
                ]),
            ),
            f"{root}/MILESTONE_GENERATOR.md": page(
                "Milestone Generator",
                ["Milestone Generator"],
                ["github", "milestones", "knowledge-2.0"],
                "Milestone mapping from sprint registry.",
                bullets([
                    f"{s.get('id')} — {s.get('stream')}: {s.get('purpose')} [{s.get('status')}]"
                    for s in stats["sprints"][-12:]
                ] or ["- No sprints"]),
            ),
            f"{root}/REPOSITORY_HEALTH.md": page(
                "Repository Health Report",
                ["Repository Health"],
                ["github", "health", "knowledge-2.0"],
                "Repository health snapshot for GitHub enterprise view.",
                bullets([
                    f"Branch: `{stats['branch']}`",
                    f"Commits: **{stats['commits']}**",
                    f"Python files: **{stats['python_files']}**",
                    f"Test files: **{stats['test_files']}**",
                    f"Knowledge pages: **{stats['knowledge_md']}**",
                    f"Architecture score: **{(scores or {}).get('architecture_quality', 'n/a')}**",
                    "Related: [[PROJECT_HEALTH]] · [[VALIDATION_REPORT]]",
                ]),
            ),
            f"{root}/CONTRIBUTION_STATS.md": page(
                "Contribution Statistics",
                ["Contribution Stats"],
                ["github", "stats", "knowledge-2.0"],
                "Contribution / commit analytics summary.",
                bullets([
                    f"Total commits (approx): {stats['commits']}",
                    "Recent activity:",
                    *stats["recent_log"][:10],
                ]),
            ),
            f"{root}/REPOSITORY_DASHBOARD.md": page(
                "Repository Dashboard",
                ["Repository Dashboard"],
                ["github", "dashboard", "knowledge-2.0"],
                "GitHub-oriented repository dashboard.",
                NL.join([
                    "| Metric | Value |",
                    "|--------|------:|",
                    f"| Apps | {len(stats['applications'])} |",
                    f"| Platform packages | {len(stats['platform_packages'])} |",
                    f"| LOC (sampled py) | {stats['loc_sample']} |",
                    f"| Knowledge MD | {stats['knowledge_md']} |",
                    f"| Agents documented | {stats['agents']} |",
                    f"| Commits | {stats['commits']} |",
                    "",
                    "[[github/BADGES]] · [[dashboard/README]]",
                ]),
            ),
            f"{root}/README_UPDATER.md": page(
                "README Updater",
                ["README Updater"],
                ["github", "readme", "knowledge-2.0"],
                "Guidance for refreshing repository README badges and knowledge pointers (does not overwrite root README automatically without explicit run flags).",
                bullets([
                    "Knowledge entry: [[INDEX]]",
                    "Badges: [[github/BADGES]]",
                    "Developer portal: [[developer/README]]",
                    "Generated stub: `knowledge/github/README_SNIPPET.md`",
                ]),
            ),
            f"{root}/BADGES.md": page(
                "Badge Generator",
                ["Badges"],
                ["github", "badges", "knowledge-2.0"],
                "Markdown badges for README / docs.",
                NL.join([
                    "```markdown",
                    f"![Knowledge](https://img.shields.io/badge/Knowledge-{VERSION}-blue)",
                    "![Platform Core](https://img.shields.io/badge/Platform_Core-3.0.0-green)",
                    "![Ecosystem](https://img.shields.io/badge/Ecosystem-1.5.0--alpha-lightgrey)",
                    "![Docs](https://img.shields.io/badge/Docs-Obsidian-purple)",
                    "```",
                    "",
                    "Rendered references live in [[github/README_SNIPPET]].",
                ]),
            ),
            f"{root}/README_SNIPPET.md": page(
                "README Snippet",
                ["README Snippet"],
                ["github", "knowledge-2.0"],
                "Copy-paste snippet for repository README knowledge section.",
                NL.join([
                    "```markdown",
                    f"## Knowledge System `{VERSION}`",
                    "- Obsidian vault: `knowledge/INDEX.md`",
                    "- Enterprise infra: Knowledge 2.0",
                    "- Developer portal: `knowledge/developer/`",
                    "- Architecture viz: `knowledge/architecture/`",
                    "```",
                ]),
            ),
            f"{root}/ISSUE_TEMPLATES.md": page(
                "Issue Templates",
                ["Issue Templates Docs"],
                ["github", "templates", "knowledge-2.0"],
                "Issue templates are maintained under `.github/ISSUE_TEMPLATE/` and documented here.",
                bullets(["Bug report", "Feature request", "Architecture review", "Documentation task"]),
            ),
            f"{root}/PR_TEMPLATES.md": page(
                "Pull Request Templates",
                ["PR Templates Docs"],
                ["github", "templates", "knowledge-2.0"],
                "PR template lives at `.github/PULL_REQUEST_TEMPLATE.md`.",
                bullets(["Summary", "Test plan", "Architecture impact", "Docs updated?"]),
            ),
            f"{root}/CODEOWNERS.md": page(
                "CODEOWNERS",
                ["CODEOWNERS Docs"],
                ["github", "owners", "knowledge-2.0"],
                "CODEOWNERS file at `.github/CODEOWNERS` maps ownership without changing runtime code.",
                bullets([
                    "`/knowledge/` — documentation maintainers",
                    "`/applications/` — application maintainers",
                    "`/platform_*/` — platform maintainers",
                    "`/ecosystem/` — ecosystem maintainers",
                ]),
            ),
            f"{root}/ACTIONS.md": page(
                "GitHub Actions Improvements",
                ["GitHub Actions Docs"],
                ["github", "actions", "knowledge-2.0"],
                "Knowledge validation workflow additions for enterprise CI.",
                bullets([
                    "`.github/workflows/knowledge-validation.yml`",
                    "Existing: `.github/workflows/architecture.yml`",
                    "Runs doc generators in check mode / link validation",
                ]),
            ),
        }
        for rel, content in pages.items():
            self._track(write(rel, content))

        # sync .github templates (infra only)
        self._sync_github_native()

    def _sync_github_native(self) -> None:
        write(
            "ISSUE_TEMPLATE/bug_report.md",
            """---
name: Bug report
about: Report a defect
title: "[bug] "
labels: bug
---

## Summary
## Steps to reproduce
## Expected
## Actual
## Environment
## Architecture impact
- [ ] Platform Core
- [ ] Ecosystem
- [ ] Application
- [ ] Knowledge only
""",
            root=GITHUB_DIR,
        )
        write(
            "ISSUE_TEMPLATE/feature_request.md",
            """---
name: Feature request
about: Propose an enhancement
title: "[feat] "
labels: enhancement
---

## Problem
## Proposal
## Alternatives
## Documentation / Knowledge updates required
""",
            root=GITHUB_DIR,
        )
        write(
            "ISSUE_TEMPLATE/architecture_review.md",
            """---
name: Architecture review
about: Request architecture guardian review
title: "[arch] "
labels: architecture
---

## Scope
## Dependency concerns
## Bridge compliance
## Links
- knowledge/PROJECT_HEALTH.md
- knowledge/DEPENDENCY_REPORT.md
""",
            root=GITHUB_DIR,
        )
        write(
            "ISSUE_TEMPLATE/documentation.md",
            """---
name: Documentation task
about: Knowledge / docs work
title: "[docs] "
labels: documentation
---

## Pages to update
## Generators to run
- [ ] knowledge/tools/knowledge20_update.py
- [ ] knowledge/tools/update_docs.py
- [ ] knowledge/tools/full_architecture_review.py
""",
            root=GITHUB_DIR,
        )
        write(
            "PULL_REQUEST_TEMPLATE.md",
            """## Summary
## Changes
## Test plan
- [ ] Unit / regression tests
- [ ] Docs updated (`knowledge/`)
- [ ] No unintended runtime logic changes
## Architecture impact
- [ ] Bridges only (no Core/Ecosystem mutations from apps)
## Knowledge checklist
- [ ] INDEX / dashboards refreshed if sprint completed
- [ ] CHANGELOG / RELEASE_NOTES updated
""",
            root=GITHUB_DIR,
        )
        write(
            "CODEOWNERS",
            """# Enterprise ownership map (Knowledge 2.0)
/knowledge/ @macbook
/docs/ @macbook
/.github/ @macbook
/applications/ @macbook
/ecosystem/ @macbook
/platform_*/ @macbook
""",
            root=GITHUB_DIR,
        )
        write(
            "workflows/knowledge-validation.yml",
            """name: Knowledge Validation

on:
  push:
    paths:
      - 'knowledge/**'
      - '.github/workflows/knowledge-validation.yml'
  pull_request:
    paths:
      - 'knowledge/**'
  workflow_dispatch:

jobs:
  validate-knowledge:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Validate wiki links
        run: python3 knowledge/tools/check_links.py
      - name: Architecture check (read-only)
        run: python3 knowledge/tools/architecture_check.py
      - name: Pipeline validation
        run: python3 knowledge/tools/validate_release_pipeline.py
""",
            root=GITHUB_DIR,
        )
        write(
            "RELEASE_TEMPLATE.md",
            f"""# Release Template (Knowledge / Platform)

## Version
`knowledge-v{VERSION}`

## Highlights
-

## Documentation
- knowledge/INDEX.md
- knowledge/releases/RELEASE_NOTES.md

## Validation
- [ ] knowledge validation workflow green
- [ ] architecture guardian reviewed
""",
            root=GITHUB_DIR,
        )
        for p in GITHUB_DIR.rglob("*"):
            if p.is_file():
                self._track(p)

    # ------------------------------------------------------------------
    # 2.2 Architecture Visualization
    # ------------------------------------------------------------------
    def generate_architecture_viz(self) -> None:
        root = "architecture"
        apps = self.stats["applications"]
        plats = self.stats["platform_packages"][:18]

        def mermaid_page(name: str, title: str, diagram: str, overview: str) -> None:
            content = page(
                title,
                [title],
                ["architecture", "diagram", "knowledge-2.0"],
                overview,
                f"```mermaid\n{diagram}\n```\n\nAlso see PlantUML twin when present.",
                architecture="Auto-generated architecture visualization (Knowledge 2.2).",
                relationships="[[architecture/README]] · [[ARCHITECTURE_DASHBOARD]] · [[diagrams/automation/README]]",
            )
            self._track(write(f"{root}/{name}.md", content))

        self._track(write(
            f"{root}/README.md",
            page(
                "Architecture Visualization",
                ["Architecture Visualization"],
                ["architecture", "knowledge-2.0"],
                "Knowledge 2.2 — enterprise architecture visualization pack (Mermaid + PlantUML + snapshots).",
                bullets([
                    "[[architecture/PLATFORM_DIAGRAM]]",
                    "[[architecture/C4_MODEL]]",
                    "[[architecture/CONTAINER_DIAGRAM]]",
                    "[[architecture/COMPONENT_DIAGRAM]]",
                    "[[architecture/DEPLOYMENT_DIAGRAM]]",
                    "[[architecture/DEPENDENCY_GRAPH]]",
                    "[[architecture/MODULE_GRAPH]]",
                    "[[architecture/APPLICATION_GRAPH]]",
                    "[[architecture/PLUGIN_GRAPH]]",
                    "[[architecture/AI_AGENT_GRAPH]]",
                    "[[architecture/WORKFLOW_GRAPH]]",
                    "[[architecture/DATABASE_ER]]",
                    "[[architecture/API_RELATIONSHIPS]]",
                    "[[architecture/KNOWLEDGE_GRAPH]]",
                    "[[architecture/snapshots/README]]",
                ]),
                interfaces="`python3 knowledge/tools/generate_architecture_viz.py`",
            ),
        ))

        mermaid_page(
            "PLATFORM_DIAGRAM",
            "Platform Diagram",
            f"""flowchart TB
  subgraph Core[Platform Core]
  {NL.join(f'  {p}' for p in plats)}
  end
  ECO[Ecosystem]
  KNOW[Knowledge 2.0]
  {NL.join(f'  {a}[{a}]' for a in apps)}
  KNOW --> ECO --> Core
  {NL.join(f'  {a} -->|bridges| ECO' for a in apps)}
  {NL.join(f'  {a} -->|bridges| Core' for a in apps)}
""",
            "High-level platform diagram of Core, Ecosystem, apps, and Knowledge.",
        )
        mermaid_page(
            "C4_MODEL",
            "C4 Model",
            """C4Context
  title AI Ecosystem Context
  Person(dev, Developer)
  Person(ops, Operator)
  System(core, Platform Core)
  System(eco, AI Ecosystem)
  System_Ext(gh, GitHub)
  Rel(dev, core, uses SDKs)
  Rel(dev, eco, workspace)
  Rel(ops, gh, releases)
  Rel(eco, core, depends)
""",
            "C4 context-style diagram for the AI Ecosystem (Mermaid C4).",
        )
        mermaid_page(
            "CONTAINER_DIAGRAM",
            "Container Diagram",
            """flowchart LR
  WEB[API Gateway aiohttp]
  CORE[Platform Services]
  ECO[Ecosystem Services]
  APPS[Application Containers]
  DB[(Database)]
  KNOW[Knowledge Vault]
  WEB --> CORE
  WEB --> ECO
  WEB --> APPS
  CORE --> DB
  APPS --> DB
  KNOW -.-> WEB
""",
            "Container-level view of runtime vs knowledge infrastructure.",
        )
        mermaid_page(
            "COMPONENT_DIAGRAM",
            "Component Diagram",
            """flowchart TB
  API[api/server.py] --> REG[App Routers]
  REG --> BR[Bridges]
  BR --> MEM[Memory]
  BR --> ORCH[Orchestrator]
  BR --> WF[Workflow]
  KNOW[Knowledge Tools] --> MD[Markdown Reports]
""",
            "Component interactions for API routing and knowledge tooling.",
        )
        mermaid_page(
            "DEPLOYMENT_DIAGRAM",
            "Deployment Diagram",
            """flowchart TB
  CI[GitHub Actions] --> ART[Artifacts/Docs]
  NODE[App Process] --> HEALTH[/health]
  NODE --> METRICS[/metrics]
  KNOW[Obsidian Vault] --> CI
""",
            "Deployment / CI relationship diagram.",
        )
        mermaid_page(
            "DEPENDENCY_GRAPH",
            "Dependency Graph",
            """flowchart BT
  Apps --> Ecosystem --> PlatformCore
  KnowledgeTools --> Apps
  KnowledgeTools --> Ecosystem
  KnowledgeTools --> PlatformCore
""",
            "Layer dependency graph (bridges downward).",
        )
        mermaid_page(
            "MODULE_GRAPH",
            "Module Graph",
            f"""mindmap
  root((Modules))
    Platform
      {plats[0] if plats else 'platform_memory'}
      {plats[1] if len(plats)>1 else 'platform_orchestrator'}
    Ecosystem
      identity
      assistant
    Knowledge
      tools
      dashboards
""",
            "Module mind map for major layers.",
        )
        mermaid_page(
            "APPLICATION_GRAPH",
            "Application Graph",
            f"""flowchart LR
  {NL.join(f'  {a}' for a in apps) if apps else '  none'}
  CRM[CRM capability]
  LEGAL[Legal scaffold]
""",
            "Application portfolio graph.",
        )
        mermaid_page(
            "PLUGIN_GRAPH",
            "Plugin Graph",
            """flowchart TB
  SDK[Plugin SDK] --> PM[Plugin Manager]
  PM --> T1[Tools]
  AG[Agents] --> PM
  WF[Workflows] --> PM
""",
            "Plugin / tool framework graph.",
        )
        agents = [p.stem for p in (KNOWLEDGE / "agents").glob("*.md")][:12] if (KNOWLEDGE / "agents").exists() else []
        mermaid_page(
            "AI_AGENT_GRAPH",
            "AI Agent Graph",
            f"""flowchart LR
  ORCH[Orchestrator]
  {NL.join(f'  ORCH --> A{i}[{a}]' for i, a in enumerate(agents))}
""",
            "Documented AI agent topology.",
        )
        mermaid_page(
            "WORKFLOW_GRAPH",
            "Workflow Graph",
            """stateDiagram-v2
  [*] --> Plan
  Plan --> Implement
  Implement --> ValidateKnowledge
  ValidateKnowledge --> Release
  Release --> [*]
""",
            "Enterprise delivery workflow graph.",
        )
        mermaid_page(
            "DATABASE_ER",
            "Database ER Diagram",
            """erDiagram
  PLATFORM ||--o{ APPLICATION : hosts
  APPLICATION ||--o{ MODULE : contains
  APPLICATION ||--o{ AGENT : documents
  SPRINT ||--o{ RELEASE : produces
""",
            "Logical ER-style diagram for platform entities (documentation model).",
        )
        mermaid_page(
            "API_RELATIONSHIPS",
            "API Relationship Diagram",
            """flowchart TB
  GW[Gateway] --> V1[/api/v1]
  GW --> ECO[/api/ecosystem/v1]
  GW --> AGRO[/api/agro/v1]
  GW --> PORT[/api/port/v1]
  GW --> AUTO[/api/auto/v1]
  GW --> DRONE[/api/drone/v1]
""",
            "API relationship diagram across surfaces.",
        )
        mermaid_page(
            "KNOWLEDGE_GRAPH",
            "Knowledge Graph Diagram",
            """mindmap
  root((Knowledge 2.0))
    GitHub
    Architecture
    Dashboards
    Developer
    Pipeline
    Agents
    Registries
""",
            "Obsidian knowledge graph overview.",
        )

        # PlantUML twins (text)
        plantuml = {
            "PLATFORM_DIAGRAM.puml": "@startuml\nrectangle PlatformCore\nrectangle Ecosystem\nrectangle Knowledge\nKnowledge --> Ecosystem\nEcosystem --> PlatformCore\n@enduml\n",
            "DEPLOYMENT_DIAGRAM.puml": "@startuml\nnode GitHubActions\nnode AppProcess\ncloud ObsidianVault\nGitHubActions --> ObsidianVault\nAppProcess --> GitHubActions\n@enduml\n",
            "APPLICATION_GRAPH.puml": "@startuml\n" + NL.join(f'component {a}' for a in apps) + "\n@enduml\n",
        }
        for name, body in plantuml.items():
            self._track(write(f"{root}/plantuml/{name}", body))

        # snapshots
        snap_dir = KNOWLEDGE / root / "snapshots"
        snap_name = f"architecture_{NOW.replace('-', '')}_{VERSION.replace('.', '_')}.md"
        self._track(write(
            f"{root}/snapshots/{snap_name}",
            page(
                f"Architecture Snapshot {VERSION}",
                [f"Architecture Snapshot {VERSION}"],
                ["snapshot", "architecture", "knowledge-2.0"],
                f"Historical architecture snapshot for Knowledge `{VERSION}` on {NOW}.",
                bullets([
                    f"Apps: {', '.join(apps)}",
                    f"Platform packages: {len(self.stats['platform_packages'])}",
                    f"Scores: {json.dumps(self.scores.get('scores') or {}, sort_keys=True)}",
                    "Links: [[architecture/PLATFORM_DIAGRAM]] · [[PROJECT_HEALTH]]",
                ]),
            ),
        ))
        self._track(write(
            f"{root}/snapshots/README.md",
            page(
                "Architecture Snapshots",
                ["Architecture Snapshots"],
                ["snapshot", "knowledge-2.0"],
                "Historical architecture versions generated by Enterprise Infra.",
                bullets([snap_name, "Regenerate via generate_architecture_viz.py"]),
            ),
        ))
        # canvas stub index
        self._track(write(
            "canvas/ENTERPRISE_ARCHITECTURE.canvas",
            json.dumps({
                "nodes": [
                    {"id": "1", "type": "file", "file": "knowledge/architecture/README.md", "x": 0, "y": 0, "width": 400, "height": 200},
                    {"id": "2", "type": "file", "file": "knowledge/INDEX.md", "x": 500, "y": 0, "width": 400, "height": 200},
                ],
                "edges": [{"id": "e1", "fromNode": "1", "toNode": "2"}],
            }, indent=2),
        ))

    # ------------------------------------------------------------------
    # 2.3 Analytics dashboards
    # ------------------------------------------------------------------
    def generate_analytics(self) -> None:
        root = "dashboard"
        s = self.stats
        scores = self.scores.get("scores") or {}
        sprints = s["sprints"]
        completed = [x for x in sprints if x.get("status") == "completed"]
        planned = [x for x in sprints if x.get("status") == "planned"]
        pct = round(100 * len(completed) / max(len(sprints), 1), 1)
        test_cov = round(100 * s["test_files"] / max(s["python_files"], 1), 1)

        dashboards = {
            "README.md": ("Analytics Dashboards", bullets([
                "Knowledge 2.3 analytics pack",
                "[[dashboard/PLATFORM_PROGRESS]]",
                "[[dashboard/SPRINT_PROGRESS]]",
                "[[dashboard/PROJECT_TIMELINE]]",
                "[[dashboard/DEVELOPMENT_VELOCITY]]",
                "[[dashboard/COMPONENT_STATISTICS]]",
                "[[dashboard/APPLICATION_STATISTICS]]",
                "[[dashboard/MODULE_STATISTICS]]",
                "[[dashboard/AGENT_STATISTICS]]",
                "[[dashboard/API_STATISTICS]]",
                "[[dashboard/DATABASE_STATISTICS]]",
                "[[dashboard/DOCUMENTATION_COVERAGE]]",
                "[[dashboard/TEST_COVERAGE]]",
                "[[dashboard/ARCHITECTURE_HEALTH]]",
                "[[dashboard/TECHNICAL_DEBT]]",
                "[[dashboard/COMPLEXITY_METRICS]]",
                "[[dashboard/REPOSITORY_GROWTH]]",
                "[[dashboard/LINES_OF_CODE]]",
                "[[dashboard/COMMIT_ANALYTICS]]",
                "[[dashboard/RELEASE_ANALYTICS]]",
                "[[dashboard/MILESTONE_PROGRESS]]",
            ])),
            "PLATFORM_PROGRESS.md": ("Platform Progress", NL.join([
                f"- Platform packages: **{len(s['platform_packages'])}**",
                f"- Architecture quality: **{scores.get('architecture_quality', 'n/a')}**",
                f"- Scalability score: **{scores.get('scalability', 'n/a')}**",
                "- Detail: [[PLATFORM_CORE]] · [[PROJECT_HEALTH]]",
            ])),
            "SPRINT_PROGRESS.md": ("Sprint Progress (Analytics)", NL.join([
                f"- Completion: **{pct}%** ({len(completed)}/{len(sprints)})",
                f"- Planned remaining: **{len(planned)}**",
                "- Canonical: [[SPRINT_PROGRESS]] · [[registries/SPRINT_REGISTRY]]",
            ])),
            "PROJECT_TIMELINE.md": ("Project Timeline", bullets([
                f"{x.get('id')}: {x.get('stream')} — {x.get('status')}" for x in sprints[-15:]
            ])),
            "DEVELOPMENT_VELOCITY.md": ("Development Velocity", bullets([
                f"Commits total≈ {s['commits']}",
                "Recent:",
                *s["recent_log"][:8],
            ])),
            "COMPONENT_STATISTICS.md": ("Component Statistics", bullets([
                f"Platform components: {len(s['platform_packages'])}",
                f"Applications: {len(s['applications'])}",
                f"Knowledge pages: {s['knowledge_md']}",
            ])),
            "APPLICATION_STATISTICS.md": ("Application Statistics", bullets([
                f"`{a}`" for a in s["applications"]
            ])),
            "MODULE_STATISTICS.md": ("Module Statistics", bullets([
                f"Python modules/files: {s['python_files']}",
                f"Platform packages: {len(s['platform_packages'])}",
            ])),
            "AGENT_STATISTICS.md": ("Agent Statistics", bullets([
                f"Documented agents: {s['agents']}",
                "Registry: [[registries/AGENT_REGISTRY]]",
            ])),
            "API_STATISTICS.md": ("API Statistics", bullets([
                "Prefixes documented in [[registries/API_REGISTRY]]",
                "/api/v1, /api/ecosystem/v1, /api/agro/v1, /api/port/v1, /api/auto/v1, /api/drone/v1",
            ])),
            "DATABASE_STATISTICS.md": ("Database Statistics", bullets([
                "Logical model: [[architecture/DATABASE_ER]]",
                "Runtime schema docs remain under `docs/database.md` (reference only)",
            ])),
            "DOCUMENTATION_COVERAGE.md": ("Documentation Coverage", bullets([
                f"Knowledge markdown files: **{s['knowledge_md']}**",
                f"Documentation score: **{scores.get('documentation_coverage', 'n/a')}**",
            ])),
            "TEST_COVERAGE.md": ("Test Coverage", bullets([
                f"Test-related files: **{s['test_files']}**",
                f"Heuristic coverage ratio: **{test_cov}%** (file count based)",
            ])),
            "ARCHITECTURE_HEALTH.md": ("Architecture Health", bullets([
                f"Overall: {scores.get('overall')}",
                f"Risk index: {scores.get('risk_index')}",
                "[[PROJECT_HEALTH]] · [[DEPENDENCY_REPORT]]",
            ])),
            "TECHNICAL_DEBT.md": ("Technical Debt Dashboard", bullets([
                "Canonical register: [[TECHNICAL_DEBT]]",
                "Recommendations: [[ARCHITECT_RECOMMENDATIONS]]",
            ])),
            "COMPLEXITY_METRICS.md": ("Complexity Metrics", bullets([
                f"Complexity score: {scores.get('complexity')}",
                f"Coupling score: {scores.get('coupling')}",
                f"Cohesion score: {scores.get('module_cohesion')}",
            ])),
            "REPOSITORY_GROWTH.md": ("Repository Growth", bullets([
                f"Commits: {s['commits']}",
                f"Python files: {s['python_files']}",
                f"Knowledge pages: {s['knowledge_md']}",
            ])),
            "LINES_OF_CODE.md": ("Lines of Code", bullets([
                f"Sampled Python LOC: **{s['loc_sample']}**",
                "(Bounded scan for generator performance)",
            ])),
            "COMMIT_ANALYTICS.md": ("Commit Analytics", bullets(s["recent_log"][:15])),
            "RELEASE_ANALYTICS.md": ("Release Analytics", bullets([
                f"Knowledge version: {VERSION}",
                f"Tags: {', '.join(s['tags'][:8]) or 'none'}",
                "[[releases/RELEASE_NOTES]] · [[github/RELEASE_GENERATOR]]",
            ])),
            "MILESTONE_PROGRESS.md": ("Milestone Progress", bullets([
                f"Completed milestones/sprints: {len(completed)}",
                f"Planned: {len(planned)}",
                f"Progress: {pct}%",
            ])),
        }
        for rel, (title, components) in dashboards.items():
            self._track(write(
                f"{root}/{rel}",
                page(title, [title], ["dashboard", "analytics", "knowledge-2.0"], f"Analytics dashboard — {title}.", components,
                     relationships="[[dashboard/README]] · [[EXECUTIVE_DASHBOARD]] · [[INDEX]]"),
            ))

    # ------------------------------------------------------------------
    # 2.4 Developer portal
    # ------------------------------------------------------------------
    def generate_developer_portal(self) -> None:
        root = "developer"
        guides = {
            "README.md": ("Developer Portal", bullets([
                "Knowledge 2.4 developer experience hub",
                "[[developer/DEVELOPER_GUIDE]]",
                "[[developer/PLATFORM_SDK]]",
                "[[developer/PLUGIN_SDK]]",
                "[[developer/APPLICATION_SDK]]",
                "[[developer/AGENT_SDK]]",
                "[[developer/REST_API_GUIDE]]",
                "[[developer/ARCHITECTURE_GUIDE]]",
                "[[developer/CONTRIBUTION_GUIDE]]",
                "[[developer/CODING_STANDARDS]]",
                "[[developer/PROJECT_TEMPLATES]]",
                "[[developer/CHECKLIST]]",
                "Wizards: [[developer/wizards/README]]",
            ])),
            "DEVELOPER_GUIDE.md": ("Developer Guide", bullets([
                "Start at [[INDEX]] and [[developer/ARCHITECTURE_GUIDE]]",
                "Run apps via existing repo tooling; do not mutate Core from apps",
                "After sprints: `python3 knowledge/tools/knowledge20_update.py`",
            ])),
            "PLATFORM_SDK.md": ("Platform SDK", bullets([
                "Package: `platform_sdk/`",
                "Docs: repository `docs/` + [[PLATFORM_CORE]]",
                "Consume via imports/bridges — do not fork Core inside apps",
            ])),
            "PLUGIN_SDK.md": ("Plugin SDK Guide", bullets([
                "[[Plugin SDK]] · `platform_plugin_sdk`",
                "Register tools through plugin manager",
            ])),
            "APPLICATION_SDK.md": ("Application SDK", bullets([
                "Pattern: `applications/<name>/` with facade + bridges",
                "Examples: auto_marketplace, port_erp, agro_marketplace, drone_platform",
                "Wizard: [[developer/wizards/NEW_APPLICATION]]",
            ])),
            "AGENT_SDK.md": ("Agent SDK", bullets([
                "Register agents via platform agent registry patterns",
                "Document agents under `knowledge/agents/`",
                "Wizard: [[developer/wizards/NEW_AI_AGENT]]",
            ])),
            "REST_API_GUIDE.md": ("REST API Guide", bullets([
                "[[API_REFERENCE]] · [[registries/API_REGISTRY]]",
                "Versioned prefixes under `/api/<domain>/v1`",
            ])),
            "ARCHITECTURE_GUIDE.md": ("Architecture Guide", bullets([
                "Layers: Apps → bridges → Ecosystem → Platform Core",
                "[[ARCHITECTURE]] · [[architecture/README]] · [[DEPENDENCY_REPORT]]",
                "Guardian: [[automation/ARCHITECTURE_GUARDIAN]]",
            ])),
            "CONTRIBUTION_GUIDE.md": ("Contribution Guide", bullets([
                "Use `.github` issue/PR templates",
                "Keep knowledge updated on sprint completion",
                "Prefer bridges; never modify Core/Ecosystem from app PRs unless intentional platform work",
            ])),
            "CODING_STANDARDS.md": ("Coding Standards", bullets([
                "Match existing module style",
                "Typed Python where surrounding code is typed",
                "No drive-by refactors",
                "Docs standards: [[standards/DOCUMENTATION_STANDARDS]]",
            ])),
            "PROJECT_TEMPLATES.md": ("Project Templates", bullets([
                "Application template checklist → wizards",
                "Plugin / Agent / ERP / Marketplace wizards under `developer/wizards/`",
            ])),
            "CHECKLIST.md": ("Development Checklist", bullets([
                "Design against architecture guide",
                "Add/adjust tests",
                "Update knowledge registries if public surface changes",
                "Run `check_links.py` and `architecture_check.py` for doc-heavy PRs",
                "Fill PR template architecture impact section",
            ])),
        }
        for rel, (title, components) in guides.items():
            self._track(write(
                f"{root}/{rel}",
                page(title, [title], ["developer", "knowledge-2.0"], f"Developer portal — {title}.", components,
                     relationships="[[developer/README]] · [[INDEX]]"),
            ))

        wizards = {
            "README.md": ("Wizards", bullets([
                "[[developer/wizards/NEW_APPLICATION]]",
                "[[developer/wizards/NEW_PLUGIN]]",
                "[[developer/wizards/NEW_AI_AGENT]]",
                "[[developer/wizards/NEW_ERP]]",
                "[[developer/wizards/NEW_MARKETPLACE]]",
            ])),
            "NEW_APPLICATION.md": ("New Application Wizard", bullets([
                "1. Create `applications/<app_name>/`",
                "2. Add config, manifest, application facade, shared store",
                "3. Add `integrations/platform_bridge.py` + `ecosystem_bridge.py`",
                "4. Register routes via app `api/register.py` (mount in api/server only as glue)",
                "5. Add `knowledge/applications/<APP>.md` + registry entry",
                "6. Run Knowledge update tools",
            ])),
            "NEW_PLUGIN.md": ("New Plugin Wizard", bullets([
                "1. Follow Plugin SDK",
                "2. Register with plugin manager",
                "3. Document under knowledge + tests",
            ])),
            "NEW_AI_AGENT.md": ("New AI Agent Wizard", bullets([
                "1. Implement agent capability in appropriate layer",
                "2. Add `knowledge/agents/<Agent Name>.md`",
                "3. Refresh [[registries/AGENT_REGISTRY]]",
            ])),
            "NEW_ERP.md": ("New ERP Wizard", bullets([
                "Follow Port ERP package layout patterns",
                "Domains + facade + bridges + `/api/<erp>/v1`",
                "Document sprint registry + architecture diagrams",
            ])),
            "NEW_MARKETPLACE.md": ("New Marketplace Wizard", bullets([
                "Follow Agro/Auto marketplace patterns",
                "Catalog, CRM, trading/transactions, portals as needed",
                "Bridge-only integration with Core/Ecosystem",
            ])),
        }
        for rel, (title, components) in wizards.items():
            self._track(write(
                f"{root}/wizards/{rel}",
                page(title, [title], ["wizard", "developer", "knowledge-2.0"], f"Wizard — {title}.", components),
            ))

    # ------------------------------------------------------------------
    # 2.5 Release pipeline
    # ------------------------------------------------------------------
    def generate_pipeline(self) -> None:
        root = "pipeline"
        pages = {
            "README.md": ("Enterprise Release Pipeline", bullets([
                "Knowledge 2.5 pipeline pack",
                "[[pipeline/DOCUMENTATION_VALIDATION]]",
                "[[pipeline/ARCHITECTURE_VALIDATION]]",
                "[[pipeline/LINK_VALIDATION]]",
                "[[pipeline/WIKI_VALIDATION]]",
                "[[pipeline/DASHBOARD_VALIDATION]]",
                "[[pipeline/DIAGRAM_VALIDATION]]",
                "[[pipeline/RELEASE_VALIDATION]]",
                "[[pipeline/REGRESSION_VALIDATION]]",
                "[[pipeline/SNAPSHOT_GENERATOR]]",
                "[[pipeline/VERSION_SNAPSHOT]]",
                "[[pipeline/PROJECT_ARCHIVE]]",
                "[[pipeline/RELEASE_PACKAGE]]",
                "[[pipeline/GITHUB_RELEASE_PACKAGE]]",
                "[[pipeline/PRODUCTION_REPORT]]",
                "[[pipeline/EXECUTIVE_SUMMARY]]",
            ])),
            "DOCUMENTATION_VALIDATION.md": ("Documentation Validation", bullets([
                "`python3 knowledge/tools/check_links.py`",
                "Required sections standard: [[standards/DOCUMENTATION_STANDARDS]]",
            ])),
            "ARCHITECTURE_VALIDATION.md": ("Architecture Validation", bullets([
                "`python3 knowledge/tools/architecture_check.py`",
                "[[DEPENDENCY_REPORT]] · [[PROJECT_HEALTH]]",
            ])),
            "LINK_VALIDATION.md": ("Broken Link Detection", bullets([
                "[[VALIDATION_REPORT]]",
                "Wiki link scanner in Documentation Assistant",
            ])),
            "WIKI_VALIDATION.md": ("Wiki Validation", bullets([
                "Obsidian hubs + aliases",
                "INDEX connectivity",
            ])),
            "DASHBOARD_VALIDATION.md": ("Dashboard Validation", bullets([
                "Ensure [[DASHBOARD]] [[EXECUTIVE_DASHBOARD]] [[dashboard/README]] exist",
                "Enterprise update refreshes metrics",
            ])),
            "DIAGRAM_VALIDATION.md": ("Diagram Validation", bullets([
                "Mermaid fences present under knowledge/architecture and diagrams/",
                "[[architecture/README]]",
            ])),
            "RELEASE_VALIDATION.md": ("Release Validation", bullets([
                "Version bump in registry meta",
                "CHANGELOG + RELEASE_NOTES updated",
                "GitHub release template filled",
            ])),
            "REGRESSION_VALIDATION.md": ("Regression Validation", bullets([
                "Run existing pytest suites for touched apps (manual/CI)",
                "Knowledge generators must remain non-mutating to runtime",
            ])),
            "SNAPSHOT_GENERATOR.md": ("Snapshot Generator", bullets([
                "Architecture snapshots: [[architecture/snapshots/README]]",
                "Project snapshot JSON: knowledge/data/project_snapshot.json",
            ])),
            "VERSION_SNAPSHOT.md": ("Version Snapshot", bullets([
                f"Knowledge version **{VERSION}** @ {NOW}",
                f"Git: {self.stats['latest']}",
            ])),
            "PROJECT_ARCHIVE.md": ("Project Archive", bullets([
                "Archive pointer documents under knowledge/pipeline/archives/",
                "Does not delete historical markdown",
            ])),
            "RELEASE_PACKAGE.md": ("Release Package", bullets([
                "Bundle: RELEASE_NOTES + CHANGELOG + PROJECT_HEALTH + EXECUTIVE_SUMMARY",
                "Generated listing in [[pipeline/GITHUB_RELEASE_PACKAGE]]",
            ])),
            "GITHUB_RELEASE_PACKAGE.md": ("GitHub Release Package", bullets([
                "Tag `knowledge-v2.0.0`",
                "Notes from [[releases/RELEASE_NOTES]]",
                "Assets: optional zip of knowledge/ (manual)",
            ])),
            "PRODUCTION_REPORT.md": ("Production Report", bullets([
                "Runtime production posture unchanged by Knowledge 2.0",
                "Apps remain at their commercial versions",
                "See [[PROJECT_STATUS]]",
            ])),
            "EXECUTIVE_SUMMARY.md": ("Executive Summary", NL.join([
                f"# Knowledge 2.0 Enterprise Infrastructure — {NOW}",
                "",
                f"- Version: **{VERSION}**",
                f"- Architecture score: **{(self.scores.get('scores') or {}).get('architecture_quality', 'n/a')}**",
                f"- Documentation pages: **{self.stats['knowledge_md']}+** (growing with this sprint)",
                f"- Applications: {', '.join(self.stats['applications'])}",
                "- Delivered: GitHub automation, architecture viz, analytics dashboards, developer portal, release pipeline",
                "",
                "Related: [[EXECUTIVE_DASHBOARD]] · [[ROADMAP]]",
            ])),
        }
        for rel, (title, components) in pages.items():
            body = components if rel == "EXECUTIVE_SUMMARY.md" else page(
                title, [title], ["pipeline", "knowledge-2.0"], f"Pipeline — {title}.", components,
                relationships="[[pipeline/README]] · [[github/README]] · [[INDEX]]",
            )
            if rel == "EXECUTIVE_SUMMARY.md":
                body = fm(title, [title], ["pipeline", "executive", "knowledge-2.0"]) + components
            self._track(write(f"{root}/{rel}", body))

        self._track(write(
            f"{root}/archives/README.md",
            page(
                "Pipeline Archives",
                ["Pipeline Archives"],
                ["pipeline", "archive", "knowledge-2.0"],
                "Archive index for release packages and snapshots.",
                bullets([f"knowledge-{VERSION}-{NOW}", "See architecture/snapshots"]),
            ),
        ))

    # ------------------------------------------------------------------
    # Auto updates of core dashboards / registries
    # ------------------------------------------------------------------
    def update_core_docs(self) -> None:
        reg = self.registry
        meta = reg.setdefault("meta", {})
        meta.update({
            "sprint": "Knowledge 2.0",
            "title": "Enterprise Development Infrastructure",
            "status": "completed",
            "version": VERSION,
        })
        sprints = reg.setdefault("sprints", [])
        for sid, purpose in [
            ("K2.0", "Enterprise Development Infrastructure umbrella"),
            ("K2.1", "GitHub Enterprise Automation"),
            ("K2.2", "Architecture Visualization"),
            ("K2.3", "Project Analytics Dashboards"),
            ("K2.4", "Developer Portal"),
            ("K2.5", "Enterprise Release Pipeline"),
        ]:
            if not any(s.get("id") == sid for s in sprints):
                sprints.append({
                    "id": sid,
                    "stream": "Knowledge",
                    "purpose": purpose,
                    "version": VERSION,
                    "status": "completed",
                    "deps": ["K1.3"] if sid == "K2.0" else ["K2.0"],
                })
        save_json(REGISTRY, reg)
        self.registry = reg

        scores = self.scores.get("scores") or {}
        completed = [s for s in sprints if s.get("status") == "completed"]
        planned = [s for s in sprints if s.get("status") == "planned"]
        pct = round(100 * len(completed) / max(len(sprints), 1), 1)

        # Application registry
        self._track(write(
            "registries/APPLICATION_REGISTRY.md",
            page(
                "Application Registry",
                ["Application Registry", "AI Application Registry"],
                ["registry", "knowledge-2.0"],
                "Registry of applications in the AI Ecosystem.",
                NL.join([
                    "| Application | Package | Version | API |",
                    "|-------------|---------|---------|-----|",
                    *[
                        f"| {a.get('name')} | `{a.get('package')}` | {a.get('version')} | `{a.get('api')}` |"
                        for a in (reg.get("applications") or [])
                    ],
                ]),
                relationships="[[registries/MODULE_REGISTRY]] · [[registries/API_REGISTRY]] · [[INDEX]]",
            ),
        ))
        # Agent registry alias page
        self._track(write(
            "registries/AI_AGENT_REGISTRY.md",
            page(
                "AI Agent Registry",
                ["AI Agent Registry"],
                ["registry", "agents", "knowledge-2.0"],
                "Alias/canonical enterprise registry page for AI agents.",
                bullets([
                    "Canonical detailed registry: [[registries/AGENT_REGISTRY]]",
                    f"Documented agents: {self.stats['agents']}",
                    "Portal: [[developer/AGENT_SDK]]",
                ]),
            ),
        ))

        core_pages = {
            "INDEX.md": page(
                "INDEX",
                ["Home", "Knowledge Home"],
                ["index", "knowledge-2.0"],
                f"**Knowledge {VERSION}** — Enterprise Development Infrastructure is live.",
                bullets([
                    f"Architecture score: **{scores.get('architecture_quality', 'n/a')}** · Sprint completion: **{pct}%**",
                    "### Enterprise packs",
                    "[[github/README]] · [[architecture/README]] · [[dashboard/README]] · [[developer/README]] · [[pipeline/README]]",
                    "### Core dashboards",
                    "[[DASHBOARD]] · [[EXECUTIVE_DASHBOARD]] · [[ARCHITECTURE_DASHBOARD]] · [[PROJECT_STATUS]] · [[SPRINT_PROGRESS]]",
                    "### Registries",
                    "[[registries/SPRINT_REGISTRY]] · [[registries/APPLICATION_REGISTRY]] · [[registries/API_REGISTRY]] · [[registries/MODULE_REGISTRY]] · [[registries/AI_AGENT_REGISTRY]]",
                    "### Automation",
                    "[[automation/ENTERPRISE_INFRASTRUCTURE]] · [[automation/DOCUMENTATION_ASSISTANT]] · [[automation/ARCHITECTURE_GUARDIAN]]",
                ]),
            ),
            "PROJECT_STATUS.md": page(
                "Project Status",
                ["Project Status"],
                ["status", "knowledge-2.0"],
                "Enterprise project status including Knowledge 2.0 delivery.",
                NL.join([
                    "| Stream | Status |",
                    "|--------|--------|",
                    "| Platform Core | ✅ 3.0.0 |",
                    "| Ecosystem | ✅ 1.5.0-alpha |",
                    "| Agro/Port/Auto | ✅ 2.0.0 |",
                    "| Drone | ✅ 1.0.0-alpha |",
                    f"| Knowledge | ✅ **{VERSION}** Enterprise Infra |",
                ]),
            ),
            "SPRINT_PROGRESS.md": page(
                "Sprint Progress",
                ["Sprint Progress"],
                ["sprints", "knowledge-2.0"],
                f"Sprint completion **{pct}%** ({len(completed)}/{len(sprints)}).",
                bullets([
                    "### Current",
                    "Knowledge 2.0 enterprise infrastructure adopted",
                    "### Completed recently",
                    *[f"{s.get('id')} — {s.get('purpose')}" for s in completed[-10:]],
                    "### Planned",
                    *([f"{s.get('id')} — {s.get('purpose')}" for s in planned[:8]] or ["None"]),
                ]),
            ),
            "EXECUTIVE_DASHBOARD.md": page(
                "Executive Dashboard",
                ["Executive Dashboard"],
                ["dashboard", "executive", "knowledge-2.0"],
                "Executive view with Knowledge 2.0 enterprise metrics.",
                bullets([
                    f"Knowledge version **{VERSION}**",
                    f"Architecture score **{scores.get('architecture_quality', 'n/a')}** · Risk **{scores.get('risk_index', 'n/a')}**",
                    f"Documentation pages ≈ **{self.stats['knowledge_md']}** (+ enterprise packs)",
                    f"Roadmap completed **{pct}%**",
                    "Packs ready: GitHub · Architecture Viz · Analytics · Developer Portal · Release Pipeline",
                    "[[pipeline/EXECUTIVE_SUMMARY]] · [[PROJECT_HEALTH]] · [[ROADMAP]]",
                ]),
            ),
            "ARCHITECTURE_DASHBOARD.md": page(
                "Architecture Dashboard",
                ["Architecture Dashboard"],
                ["dashboard", "architecture", "knowledge-2.0"],
                "Architecture dashboard linking enterprise visualization pack.",
                bullets([
                    "[[architecture/README]] · [[architecture/C4_MODEL]] · [[architecture/PLATFORM_DIAGRAM]]",
                    "[[DEPENDENCY_REPORT]] · [[PROJECT_HEALTH]] · [[diagrams/automation/README]]",
                ]),
            ),
            "DASHBOARD.md": page(
                "Dashboard",
                ["Dashboard"],
                ["dashboard", "knowledge-2.0"],
                "Operational dashboard for Knowledge 2.0.",
                NL.join([
                    "| Area | Link |",
                    "|------|------|",
                    "| Executive | [[EXECUTIVE_DASHBOARD]] |",
                    "| Analytics | [[dashboard/README]] |",
                    "| GitHub | [[github/README]] |",
                    "| Developer | [[developer/README]] |",
                    "| Pipeline | [[pipeline/README]] |",
                    "| Architecture | [[architecture/README]] |",
                ]),
            ),
            "ROADMAP.md": page(
                "Roadmap",
                ["Roadmap"],
                ["roadmap", "knowledge-2.0"],
                "Roadmap including completed Knowledge 2.0 enterprise infrastructure.",
                NL.join([
                    "### Completed",
                    "| Milestone | Version |",
                    "|-----------|---------|",
                    "| Knowledge 1.1–1.3 | 1.x |",
                    f"| Knowledge 2.0 Enterprise Infra | **{VERSION}** |",
                    "| Platform / Apps commercial stack | Core 3.0 / Apps 2.0 |",
                    "",
                    "### Planned",
                    "| Milestone | Notes |",
                    "|-----------|-------|",
                    "| Knowledge 2.6+ | CI auto-publish releases, deeper coverage badges |",
                    "| Drone 11.2+ | App runtime (separate from knowledge) |",
                    "| Ecosystem 1.6 | App registry federation |",
                ]),
            ),
        }
        for rel, content in core_pages.items():
            self._track(write(rel, content))

        # CHANGELOG + RELEASE NOTES
        self._track(write(
            "CHANGELOG.md",
            page(
                "Changelog",
                ["Changelog"],
                ["changelog", "knowledge-2.0"],
                "Living changelog for Knowledge enterprise releases.",
                NL.join([
                    f"### [{VERSION}] Knowledge 2.0 — {NOW}",
                    "- Enterprise Development Infrastructure",
                    "- GitHub automation pack (2.1)",
                    "- Architecture visualization pack (2.2)",
                    "- Project analytics dashboards (2.3)",
                    "- Developer portal + wizards (2.4)",
                    "- Enterprise release pipeline (2.5)",
                    "",
                    "### [1.3.0] Knowledge 1.3",
                    "- Architecture Guardian",
                    "",
                    "### [1.2.0] Knowledge 1.2",
                    "- Documentation Assistant",
                    "",
                    "### [1.1.0] Knowledge 1.1",
                    "- Living Obsidian documentation system",
                ]),
            ),
        ))
        self._track(write(
            "releases/RELEASE_NOTES.md",
            page(
                "Release Notes",
                ["Release Notes"],
                ["releases", "knowledge-2.0"],
                f"Release notes for Knowledge **{VERSION}**.",
                bullets([
                    "Enterprise Development Infrastructure Ready",
                    "GitHub Enterprise Ready",
                    "Architecture Visualization Ready",
                    "Developer Portal Ready",
                    "Enterprise Release Pipeline Ready",
                    "Automatic Documentation / Dashboards / Knowledge Updates Ready",
                    f"Git: {self.stats['latest']}",
                    "See [[pipeline/EXECUTIVE_SUMMARY]]",
                ]),
            ),
        ))
        self._track(write(
            "reports/PROJECT_REPORT.md",
            page(
                "Project Report",
                ["Project Report"],
                ["report", "knowledge-2.0"],
                f"Enterprise project report {NOW}.",
                bullets([
                    f"Knowledge version {VERSION}",
                    f"Files written this generation: {len(self.written)}",
                    f"Apps: {', '.join(self.stats['applications'])}",
                    "Packs: github, architecture, dashboard, developer, pipeline",
                ]),
            ),
        ))

        # daily + project snapshot notes
        self._track(write(
            f"reports/daily/DAILY_SNAPSHOT_{NOW}.md",
            page(
                f"Daily Snapshot {NOW}",
                [f"Daily Snapshot {NOW}"],
                ["daily", "snapshot", "knowledge-2.0"],
                f"Automatic daily snapshot for {NOW}.",
                bullets([
                    f"Version {VERSION}",
                    f"Commit {self.stats['latest']}",
                    f"Knowledge pages {self.stats['knowledge_md']}",
                ]),
            ),
        ))
        save_json(DATA / "enterprise_snapshot.json", {
            "at": NOW_ISO,
            "version": VERSION,
            "stats": {k: v for k, v in self.stats.items() if k != "recent_log"},
            "written_count": len(self.written),
        })

    def write_automation_doc(self) -> None:
        self._track(write(
            "automation/ENTERPRISE_INFRASTRUCTURE.md",
            page(
                "Enterprise Infrastructure",
                ["Enterprise Infrastructure", "Knowledge 2.0"],
                ["automation", "knowledge-2.0"],
                "Umbrella documentation for Knowledge 2.0 enterprise development infrastructure.",
                bullets([
                    "[[github/README]] (2.1)",
                    "[[architecture/README]] (2.2)",
                    "[[dashboard/README]] (2.3)",
                    "[[developer/README]] (2.4)",
                    "[[pipeline/README]] (2.5)",
                    "Engine: `knowledge/tools/enterprise_infra.py`",
                    "Update: `python3 knowledge/tools/knowledge20_update.py`",
                ]),
                interfaces=NL.join([
                    "```bash",
                    "python3 knowledge/tools/generate_github.py",
                    "python3 knowledge/tools/generate_architecture_viz.py",
                    "python3 knowledge/tools/generate_analytics_dashboards.py",
                    "python3 knowledge/tools/generate_developer_portal.py",
                    "python3 knowledge/tools/generate_release_pipeline.py",
                    "python3 knowledge/tools/knowledge20_update.py",
                    "python3 knowledge/tools/validate_release_pipeline.py",
                    "```",
                ]),
            ),
        ))

    def update_obsidian(self) -> None:
        bookmarks = load_json(OBSIDIAN / "bookmarks.json", {"items": []})
        items = bookmarks.get("items") or []
        existing = {i.get("path") for i in items}
        for path, title in [
            ("knowledge/github/README.md", "GitHub Enterprise"),
            ("knowledge/architecture/README.md", "Architecture Viz"),
            ("knowledge/dashboard/README.md", "Analytics Dashboards"),
            ("knowledge/developer/README.md", "Developer Portal"),
            ("knowledge/pipeline/README.md", "Release Pipeline"),
            ("knowledge/automation/ENTERPRISE_INFRASTRUCTURE.md", "Enterprise Infra"),
        ]:
            if path not in existing:
                items.append({"type": "file", "ctime": 1721653000000, "path": path, "title": title})
        bookmarks["items"] = items
        OBSIDIAN.mkdir(parents=True, exist_ok=True)
        save_json(OBSIDIAN / "bookmarks.json", bookmarks)
        graph = load_json(OBSIDIAN / "graph.json", {})
        groups = graph.get("colorGroups") or []
        if not any("knowledge-2.0" in json.dumps(g) for g in groups):
            groups.append({"query": "tag:#knowledge-2.0", "color": {"a": 1, "rgb": 250}})
            graph["colorGroups"] = groups
            save_json(OBSIDIAN / "graph.json", graph)

    def run_all(self) -> dict[str, Any]:
        self.generate_github()
        self.generate_architecture_viz()
        self.generate_analytics()
        self.generate_developer_portal()
        self.generate_pipeline()
        self.write_automation_doc()
        self.update_core_docs()
        self.update_obsidian()
        # refresh tools readme lightly via written flag
        return {
            "sprint": "Knowledge 2.0",
            "version": VERSION,
            "generated": NOW_ISO,
            "written": len(self.written),
            "sample": self.written[:30],
        }


def main() -> None:
    result = EnterpriseInfrastructure().run_all()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
