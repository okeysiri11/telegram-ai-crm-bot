#!/usr/bin/env python3
"""Knowledge Sprint 1.1 — documentation generator.

Updates living Markdown registries from knowledge/data/ecosystem_registry.json.
Run after every completed sprint:

    python3 knowledge/tools/generate_docs.py

Does not modify Platform Core, Ecosystem, or application source code.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ecosystem_registry.json"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")
NL = "\n"


def load() -> dict:
    return json.loads(DATA.read_text())


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n")


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
    parts = []
    for heading, key in order:
        parts.append(f"## {heading}\n{kwargs[key]}")
    return "\n\n".join(parts)


def frontmatter(*, title: str, aliases: list[str], tags: list[str]) -> str:
    alias_lines = NL.join(f"  - {a}" for a in aliases)
    tag_lines = NL.join(f"  - {t}" for t in tags)
    return (
        f"---\ntitle: {title}\naliases:\n{alias_lines}\ntags:\n{tag_lines}\n"
        f"generated: {NOW}\nsprint: Knowledge 1.1\n---\n"
    )


def generate_registries(data: dict) -> None:
    sprints = data["sprints"]
    completed = [s for s in sprints if s["status"] == "completed"]
    planned = [s for s in sprints if s["status"] == "planned"]
    pct = round(100 * len(completed) / max(len(sprints), 1), 1)

    rows = []
    for s in sprints:
        deps = ", ".join(s.get("deps") or []) or "—"
        rows.append(
            f"| {s['id']} | {s['stream']} | {s['purpose']} | {s['version']} | {s['status']} | {deps} |"
        )

    sprint_table = NL.join(
        [
            "| Sprint | Stream | Purpose | Version | Status | Dependencies |",
            "|--------|--------|---------|---------|--------|--------------|",
            *rows,
            "",
            f"**Completed:** {len(completed)} · **Planned:** {len(planned)} · **Completion:** {pct}%",
        ]
    )

    write(
        "registries/SPRINT_REGISTRY.md",
        frontmatter(
            title="Sprint Registry",
            aliases=["Sprint Registry", "Sprints"],
            tags=["registry", "sprints", "knowledge-1.1"],
        )
        + f"""# Sprint Registry

> Auto-generated {NOW} by `knowledge/tools/generate_docs.py` · [[INDEX]]

"""
        + std_sections(
            overview="Complete sprint registry for Platform Core, Ecosystem, Port ERP, Auto Marketplace, Drone Platform, Knowledge, and future platforms.",
            architecture="Sprints are grouped by stream. Completed work forms the living baseline; planned sprints feed [[ROADMAP]].",
            components=sprint_table,
            relationships="Detail pages: [[sprints/PLATFORM]] · [[sprints/PORT_ERP]] · [[sprints/AUTO_MARKETPLACE]] · [[sprints/DRONE_PLATFORM]] · [[SPRINT_PROGRESS]]",
            responsibilities="Track purpose, features, components, APIs, architecture changes, version, status, and dependencies per sprint.",
            interfaces="Machine source: `knowledge/data/ecosystem_registry.json`. Generator: `knowledge/tools/generate_docs.py`.",
            rest_apis="Sprints that introduce APIs are reflected in [[registries/API_REGISTRY]] and [[API_REFERENCE]].",
            events="Documentation update event after each sprint completion (run generator).",
            roadmap="Next: Drone 11.2+, Ecosystem 1.6, Legal L1.0 — [[ROADMAP]].",
            references="Repository `docs/`, `platform_manifest.json`, app manifests.",
            related="[[INDEX]] · [[PLATFORM_TIMELINE]] · [[CHANGELOG]] · [[releases/RELEASE_NOTES]] · [[statistics/STATISTICS]]",
        ),
    )

    api_rows = [
        f"| {a['name']} | `{a['prefix']}` | [[{a['owner']}]] |" for a in data["apis"]
    ]
    api_table = NL.join(
        ["| API | Prefix | Owner |", "|-----|--------|-------|", *api_rows]
    )
    write(
        "registries/API_REGISTRY.md",
        frontmatter(
            title="API Registry",
            aliases=["API Registry"],
            tags=["registry", "api", "knowledge-1.1"],
        )
        + f"""# API Registry

> Auto-generated {NOW} · [[INDEX]] · [[API_REFERENCE]]

"""
        + std_sections(
            overview="Canonical HTTP API prefixes for Platform Core, Ecosystem, and applications.",
            architecture="Gateway `api/server.py` mounts versioned routers. Apps stay behind bridges.",
            components=api_table,
            relationships="Deep reference: [[API_REFERENCE]]. Flows: [[diagrams/DATA_FLOW]] · [[diagrams/flows/API_COMMUNICATION]].",
            responsibilities="Keep prefixes stable; document new routes after each sprint.",
            interfaces="JSON registry field `apis` in `ecosystem_registry.json`.",
            rest_apis="This page **is** the REST API registry summary.",
            events="Route registration at process startup; webhook prefixes per app.",
            roadmap="OpenAPI export per application.",
            references="`docs/api.md`, app `api/register.py` modules.",
            related="[[Platform Core]] · [[Auto Marketplace]] · [[Port ERP]] · [[Agro Marketplace]] · [[Drone Platform]]",
        ),
    )

    mods = data["modules"]
    module_body = NL.join(
        [
            "### Platform Core",
            ", ".join(f"`{m}`" for m in mods["platform"]),
            "",
            "### Ecosystem",
            ", ".join(f"`{m}`" for m in mods["ecosystem"]),
            "",
            "### Drone Platform",
            ", ".join(f"`{m}`" for m in mods["drone"]),
            "",
            f"**Counts:** platform={len(mods['platform'])}, ecosystem={len(mods['ecosystem'])}, drone={len(mods['drone'])}",
        ]
    )
    write(
        "registries/MODULE_REGISTRY.md",
        frontmatter(
            title="Module Registry",
            aliases=["Module Registry"],
            tags=["registry", "modules", "knowledge-1.1"],
        )
        + f"""# Module Registry

> Auto-generated {NOW} · [[INDEX]]

"""
        + std_sections(
            overview="Inventory of Platform Core packages, Ecosystem modules, and Drone Platform modules.",
            architecture="Modules are package-level units. Applications compose modules behind facades.",
            components=module_body,
            relationships="[[Platform Core]] · [[registries/COMPONENT_REGISTRY]] · [[glossary/COMPONENTS]]",
            responsibilities="Name and track modules; do not duplicate business logic in knowledge tooling.",
            interfaces="Registry JSON `modules` map.",
            rest_apis="Modules expose APIs via their owning layer — [[registries/API_REGISTRY]].",
            events="Module load / plugin init on API startup.",
            roadmap="Add Legal modules when productized.",
            references="`platform_manifest.json`, `ecosystem/manifest.json`, drone `manifest.json`.",
            related="[[Plugin SDK]] · [[Memory Engine]] · [[Workflow Engine]] · [[AI Agents]]",
        ),
    )

    component_table = NL.join(
        [
            "| Component | Layer | Page |",
            "|-----------|-------|------|",
            "| Memory Engine | Platform | [[Memory Engine]] |",
            "| Workflow Engine | Platform | [[Workflow Engine]] |",
            "| Plugin SDK | Platform | [[Plugin SDK]] |",
            "| AI Agents | Platform/Eco | [[AI Agents]] |",
            "| Knowledge Graph | Ecosystem | [[Knowledge Graph]] |",
            "| Auto Marketplace | App | [[Auto Marketplace]] |",
            "| Port ERP | App | [[Port ERP]] |",
            "| Agro Marketplace | App | [[Agro Marketplace]] |",
            "| Drone Platform | App | [[Drone Platform]] |",
            "| Legal Platform | Scaffold | [[Legal Platform]] |",
            "| CRM | Capability | [[CRM]] |",
            "| Sprint Registry | Knowledge | [[registries/SPRINT_REGISTRY]] |",
            "| Documentation Generator | Knowledge | [[automation/DOCUMENTATION_AUTOMATION]] |",
        ]
    )
    write(
        "registries/COMPONENT_REGISTRY.md",
        frontmatter(
            title="Component Registry",
            aliases=["Component Registry"],
            tags=["registry", "components", "knowledge-1.1"],
        )
        + f"""# Component Registry

> Auto-generated {NOW} · [[INDEX]]

"""
        + std_sections(
            overview="Cross-cutting component catalog spanning engines, apps, and documentation system.",
            architecture="Components are logical capabilities (engines, facades, registries, dashboards).",
            components=component_table,
            relationships="See [[diagrams/PLATFORM_GRAPH]] and [[diagrams/APPLICATION_GRAPH]].",
            responsibilities="Provide stable names for Obsidian graph nodes and backlinks.",
            interfaces="Human pages + JSON registry.",
            rest_apis="N/A for documentation components; app components listed in API registry.",
            events="Documentation regeneration.",
            roadmap="Expand drone manufacturing components in 11.2+.",
            references="[[glossary/COMPONENTS]]",
            related="[[ARCHITECTURE]] · [[statistics/STATISTICS]]",
        ),
    )

    agent_rows = [
        f"| [[{a['name']}]] | {a['role']} | {a['layer']} | {a['status']} |"
        for a in data["agents"]
    ]
    agent_table = NL.join(
        [
            "| Agent | Role | Layer | Status |",
            "|-------|------|-------|--------|",
            *agent_rows,
        ]
    )
    write(
        "registries/AGENT_REGISTRY.md",
        frontmatter(
            title="AI Agents Registry",
            aliases=["AI Agents Registry", "Agent Registry"],
            tags=["registry", "agents", "knowledge-1.1"],
        )
        + f"""# AI Agents Registry

> Auto-generated {NOW} · [[AI Agents]] · [[diagrams/AGENT_GRAPH]]

"""
        + std_sections(
            overview="Registry of platform, ecosystem, and application AI agents documented in the knowledge vault.",
            architecture="Agents register with Platform Core registry/orchestrator; domain agents live in apps; workforce/executive agents in Ecosystem.",
            components=agent_table,
            relationships="Communication flows: [[diagrams/flows/AGENT_COMMUNICATION]]. Hub: [[AI Agents]].",
            responsibilities="Document owner, purpose, interfaces, and safe operating policy per agent.",
            interfaces="Agent pages under `knowledge/agents/`; orchestrator TaskRequest patterns in Core.",
            rest_apis="Assist endpoints under Ecosystem and app `/ai` or `/assistant` routes.",
            events="Task requests, workflow steps, assistant sessions.",
            roadmap="Shared skill catalog across agents.",
            references="`docs/AGENT_REGISTRY.md`, `docs/AI_WORKFORCE.md`.",
            related="[[Owner AI]] · [[Drone Engineer AI]] · [[Port AI]] · [[Agro AI]] · [[CRM AI]] · [[Marketplace AI]]",
        ),
    )


def generate_statistics(data: dict) -> None:
    sprints = data["sprints"]
    completed = sum(1 for s in sprints if s["status"] == "completed")
    planned = sum(1 for s in sprints if s["status"] == "planned")
    apps = data["applications"]
    mods = data["modules"]
    module_count = sum(len(v) for v in mods.values())
    agents = len(data["agents"])
    apis = len(data["apis"])
    sprint_pct = round(100 * completed / max(len(sprints), 1), 1)
    app_prod = sum(1 for a in apps if a["status"] == "completed")
    maturity = "Production Core + Commercial Verticals + Drone Alpha + Living Docs"

    stats_table = NL.join(
        [
            "| Metric | Value |",
            "|--------|-------|",
            f"| Platform Core version | {data['meta']['platform_core']} |",
            f"| Ecosystem version | {data['meta']['ecosystem']} |",
            f"| Modules (tracked) | {module_count} |",
            f"| Applications (tracked) | {len(apps)} |",
            f"| Commercial/completed apps | {app_prod} |",
            f"| AI Agents documented | {agents} |",
            f"| API surfaces | {apis} |",
            f"| Sprints total | {len(sprints)} |",
            f"| Sprints completed | {completed} |",
            f"| Sprints planned | {planned} |",
            f"| Sprint completion % | {sprint_pct}% |",
            "| Documentation coverage | Living vault (Knowledge 1.1) |",
            f"| Platform maturity | {maturity} |",
        ]
    )
    write(
        "statistics/STATISTICS.md",
        frontmatter(
            title="Statistics",
            aliases=["Statistics", "Platform Statistics"],
            tags=["statistics", "knowledge-1.1"],
        )
        + f"""# Statistics

> Auto-generated {NOW} · [[INDEX]] · [[DASHBOARD]]

"""
        + std_sections(
            overview="Quantitative view of the AI Ecosystem documentation and delivery state.",
            architecture="Metrics derived from `ecosystem_registry.json` (documentation system source of truth).",
            components=stats_table,
            relationships="Dashboards: [[DASHBOARD]] · [[EXECUTIVE_DASHBOARD]] · [[ARCHITECTURE_DASHBOARD]] · [[PROJECT_STATUS]] · [[SPRINT_PROGRESS]]",
            responsibilities="Provide executive-ready counts without querying production databases.",
            interfaces="Generator output only.",
            rest_apis="API count reflects versioned prefixes, not individual routes.",
            events="Regenerate after sprint completion.",
            roadmap="Add automated route-count scraping (read-only) in a future Knowledge sprint.",
            references="[[registries/SPRINT_REGISTRY]] · [[registries/MODULE_REGISTRY]]",
            related="[[ROADMAP]] · [[CHANGELOG]] · [[releases/RELEASE_NOTES]]",
        ),
    )


def generate_release_notes(data: dict) -> None:
    release_components = NL.join(
        [
            "### Platform Core 3.0.0",
            "- Certified PASS (100.0); frozen baseline",
            "",
            "### Ecosystem 1.5.0-alpha",
            "- Sprints 7.1–7.6 complete",
            "",
            "### Agro / Port / Auto 2.0.0",
            "- Commercial / enterprise releases complete",
            "",
            "### Drone Platform 1.0.0-alpha",
            "- Sprint 11.1 foundation complete",
            "",
            "### Knowledge 1.1.0",
            "- Obsidian living documentation system",
            "- Registries, dashboards, agent graph, Mermaid diagrams, generator",
        ]
    )
    write(
        "releases/RELEASE_NOTES.md",
        frontmatter(
            title="Release Notes",
            aliases=["Release Notes"],
            tags=["releases", "knowledge-1.1"],
        )
        + f"""# Release Notes

> Living release notes · generated {NOW}

"""
        + std_sections(
            overview="Release notes spanning Platform Core certification, commercial verticals, Drone foundation, and Knowledge 1.1.",
            architecture="Releases align to sprint streams; Knowledge releases only touch `knowledge/` and `.obsidian/`.",
            components=release_components,
            relationships="[[CHANGELOG]] · [[PLATFORM_TIMELINE]] · [[registries/SPRINT_REGISTRY]]",
            responsibilities="Communicate version status to stakeholders.",
            interfaces="Markdown + registry JSON.",
            rest_apis="No runtime API; documentation only.",
            events="Release publication events recorded in changelog.",
            roadmap="Knowledge 1.2 — deeper OpenAPI embeds and canvas packs.",
            references="Root `CHANGELOG.md`, app `*_RELEASE.md` docs.",
            related="[[INDEX]] · [[DASHBOARD]] · [[EXECUTIVE_DASHBOARD]]",
        ),
    )

    changelog_components = NL.join(
        [
            f"### [{data['meta']['version']}] Knowledge 1.1 — {NOW}",
            "- Living Obsidian documentation system",
            "- Documentation generator + registries",
            "- Dashboards, statistics, agent pages, Mermaid packs",
            "- `.obsidian` templates, bookmarks, graph config",
            "",
            "### [1.0.0-alpha] Drone Platform — Sprint 11.1",
            "- Foundation: registry, engineering, firmware, missions, inventory, AI assistant",
            "",
            "### [2.0.0] Auto Marketplace — Sprint 10.8",
            "- Enterprise / commercial release",
            "",
            "### [2.0.0] Port ERP — Sprint 9.8",
            "- Enterprise network & production release",
            "",
            "### [2.0.0] Agro Marketplace — Sprint 8.8",
            "- Commercial release",
            "",
            "### [1.5.0-alpha] Ecosystem — Sprint 7.6",
            "- Governance / compliance complete",
            "",
            "### [3.0.0] Platform Core — Sprint 1.5",
            "- Certification PASS / RC1 baseline",
        ]
    )
    write(
        "CHANGELOG.md",
        frontmatter(
            title="Changelog",
            aliases=["Changelog", "Knowledge Changelog"],
            tags=["changelog", "knowledge-1.1"],
        )
        + """# Changelog

"""
        + std_sections(
            overview="Condensed changelog for platform, ecosystem, applications, and knowledge vault.",
            architecture="Entries grouped by layer. Root repository `CHANGELOG.md` remains Platform RC1 source of truth.",
            components=changelog_components,
            relationships="[[releases/RELEASE_NOTES]] · [[PLATFORM_TIMELINE]] · [[registries/SPRINT_REGISTRY]]",
            responsibilities="Record completed milestones for the Obsidian vault audience.",
            interfaces="Edited by generator for Knowledge entries; historical entries curated.",
            rest_apis="N/A",
            events="Sprint completion → changelog entry → generator run",
            roadmap="Keep Knowledge changelog in sync via generator hooks.",
            references="Root `CHANGELOG.md`",
            related="[[ROADMAP]] · [[INDEX]] · [[SPRINT_PROGRESS]]",
        ),
    )


def generate_agent_pages(data: dict) -> None:
    flows = (
        "[[diagrams/flows/AGENT_COMMUNICATION]] · [[diagrams/AGENT_GRAPH]] · "
        "[[registries/AGENT_REGISTRY]] · [[AI Agents]]"
    )
    for a in data["agents"]:
        write(
            f"agents/{a['name']}.md",
            frontmatter(
                title=a["name"],
                aliases=[a["name"]],
                tags=["agent", a["layer"], "knowledge-1.1"],
            )
            + f"""# {a['name']}

"""
            + std_sections(
                overview=f"**{a['name']}** — {a['role']}. Status: `{a['status']}`. Layer: `{a['layer']}`.",
                architecture=(
                    "Participates in the multi-agent topology coordinated by Platform orchestrator "
                    f"and Ecosystem workforce patterns. See {flows}."
                ),
                components=NL.join(
                    [
                        "- Role definition",
                        "- Session / task interface",
                        "- Policy constraints",
                        "- Backlinks to domain pages",
                    ]
                ),
                relationships=(
                    f"{flows} · domain apps [[Auto Marketplace]] [[Port ERP]] "
                    "[[Agro Marketplace]] [[Drone Platform]] [[CRM]] [[Legal Platform]]"
                ),
                responsibilities=(
                    a["role"].capitalize()
                    + ". Must respect bridge-only integration and safe-use policies "
                    "(especially engineering agents)."
                ),
                interfaces="Orchestrator task requests; app assistant HTTP endpoints; Ecosystem assistant where applicable.",
                rest_apis=(
                    "Varies by host app — see [[registries/API_REGISTRY]]. "
                    "Drone: `/api/drone/v1/ai/*`. Auto: `/api/auto/v1/assistant/*`."
                ),
                events="assist_requested, task_delegated, workflow_step_assigned, session_remembered",
                roadmap="Skill catalog entries and shared evaluation harness.",
                references="[[registries/AGENT_REGISTRY]] · `docs/AGENT_REGISTRY.md` · `docs/AI_WORKFORCE.md`",
                related="[[AI Agents]] · [[Memory Engine]] · [[Workflow Engine]] · [[INDEX]]",
            ),
        )


def generate_alias_hubs() -> None:
    hubs = {
        "Platform Core.md": ("Platform Core", "PLATFORM_CORE", ["platform", "core"]),
        "Memory Engine.md": ("Memory Engine", "MEMORY_ENGINE", ["platform", "memory"]),
        "Workflow Engine.md": ("Workflow Engine", "WORKFLOW_ENGINE", ["platform", "workflow"]),
        "Plugin SDK.md": ("Plugin SDK", "PLUGIN_SDK", ["platform", "plugins"]),
        "AI Agents.md": ("AI Agents", "AI_AGENTS", ["agents"]),
        "Knowledge Graph.md": ("Knowledge Graph", "KNOWLEDGE_GRAPH", ["ecosystem", "knowledge"]),
        "Auto Marketplace.md": ("Auto Marketplace", "applications/AUTO_MARKETPLACE", ["app", "auto"]),
        "Port ERP.md": ("Port ERP", "applications/PORT_ERP", ["app", "port"]),
        "Agro Marketplace.md": ("Agro Marketplace", "applications/AGRO_MARKETPLACE", ["app", "agro"]),
        "Drone Platform.md": ("Drone Platform", "applications/DRONE_PLATFORM", ["app", "drone"]),
        "Legal Platform.md": ("Legal Platform", "applications/LEGAL_PLATFORM", ["app", "legal"]),
        "CRM.md": ("CRM", "applications/CRM", ["app", "crm"]),
        "Platform AI.md": ("Platform AI", "diagrams/architecture/PLATFORM_AI", ["platform", "ai"]),
    }
    for name, (title, target, tags) in hubs.items():
        write(
            name,
            frontmatter(title=title, aliases=[title], tags=tags + ["hub", "knowledge-1.1"])
            + f"""# {title}

Hub note for Obsidian graph — canonical detail: [[{target}]]

"""
            + std_sections(
                overview=f"Alias hub for **{title}**. Prefer this title in wiki links: `[[{title}]]`.",
                architecture=f"See canonical page [[{target}]].",
                components=f"Delegates to [[{target}]].",
                relationships=f"Backlink hub for [[{title}]] across the vault. Also [[INDEX]] · [[DASHBOARD]].",
                responsibilities="Stable human-readable link target for Obsidian knowledge graph.",
                interfaces="Wiki-link only.",
                rest_apis=f"See [[{target}]].",
                events="N/A",
                roadmap=f"Keep alias in sync with [[{target}]].",
                references=f"[[{target}]]",
                related="[[INDEX]] · [[registries/COMPONENT_REGISTRY]] · [[ARCHITECTURE]]",
            ),
        )


def main() -> None:
    data = load()
    generate_registries(data)
    generate_statistics(data)
    generate_release_notes(data)
    generate_agent_pages(data)
    generate_alias_hubs()
    print(f"Knowledge docs generated at {NOW}")


if __name__ == "__main__":
    main()
