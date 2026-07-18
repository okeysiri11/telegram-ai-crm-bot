from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

from platform_legacy.deprecation import generate_deprecation_docs, list_registered_deprecations
from platform_legacy.deprecation_manager import deprecation_manager
from platform_legacy.feature_flags import LEGACY_FLAG_KEYS, load_legacy_migration_flags
from platform_legacy.migration_manager import MigrationState, migration_manager


def build_migration_matrix() -> str:
    lines = [
        "| Subsystem | State | Platform Module | Legacy Module | Legacy Flag |",
        "|-----------|-------|-----------------|---------------|-------------|",
    ]
    for name in migration_manager.list_subsystems():
        rec = migration_manager.get(name)
        flag = LEGACY_FLAG_KEYS.get(name, "—")
        lines.append(
            f"| {name} | {rec.state.value} | `{rec.platform_module}` | `{rec.legacy_module}` | `{flag}` |"
        )
    return "\n".join(lines)


def build_removal_roadmap() -> str:
    phases = [
        ("Phase 1 (current)", "Platform Core default; legacy via Compatibility Layer + flags"),
        ("Phase 2", "Subsystems move LEGACY → MIGRATING → PLATFORM"),
        ("Phase 3", "Legacy flags default off; compatibility path opt-in only"),
        ("Phase 4", "REMOVED state — legacy modules disabled entirely"),
    ]
    lines = ["| Phase | Goal |", "|-------|------|"]
    for phase, goal in phases:
        lines.append(f"| {phase} | {goal} |")
    return "\n".join(lines)


def generate_legacy_migration_markdown() -> str:
    flags = load_legacy_migration_flags()
    deprecated = deprecation_manager.list_deprecated()
    registered = list_registered_deprecations()
    sections = [
        "# Legacy Migration Guide",
        "",
        "Platform Core is the **default execution path**. Legacy Telegram CRM code remains",
        "operational through the `platform_legacy` Compatibility Layer until each subsystem",
        "reaches `REMOVED` state.",
        "",
        "## Compatibility Guarantees",
        "",
        "- No business functionality breaks during migration",
        "- Transitions are reversible via feature flags or `migration_manager.rollback()`",
        "- Legacy is reachable **only** through `platform_legacy` adapters",
        "- Direct imports of `handlers`, `database_legacy`, `services.pg_*`, `openrouter` are forbidden outside `platform_legacy/`",
        "",
        "## Migration Matrix",
        "",
        build_migration_matrix(),
        "",
        "## Feature Flags (runtime, no code deploy)",
        "",
        "| Flag | Env Variable | Default |",
        "|------|--------------|---------|",
    ]
    for subsystem, flag in sorted(LEGACY_FLAG_KEYS.items()):
        env_name = flag.upper()
        enabled = getattr(flags, flag, False)
        sections.append(f"| `{flag}` | `{env_name}` | `{enabled}` |")
    sections.extend(
        [
            "",
            "## Remaining Legacy Components",
            "",
        ]
    )
    for name in migration_manager.list_subsystems():
        rec = migration_manager.get(name)
        if rec.state in {MigrationState.LEGACY, MigrationState.MIGRATING}:
            sections.append(f"- **{name}** ({rec.state.value}): `{rec.legacy_module}`")
    sections.extend(
        [
            "",
            "## Removal Roadmap",
            "",
            build_removal_roadmap(),
            "",
            "## Deprecated APIs",
            "",
        ]
    )
    if registered:
        sections.append(generate_deprecation_docs())
    else:
        for api in deprecated:
            sections.append(
                f"- `{api['name']}` → {api['replacement']} (removal: {api.get('removal_target', 'TBD')})"
            )
    sections.extend(
        [
            "",
            "## Operations",
            "",
            "- `GET /management/v1/migration` — full report",
            "- `GET /management/v1/migration/status` — subsystem states",
            "- `GET /management/v1/migration/coverage` — platform vs legacy hits",
            "- `GET /management/v1/migration/deprecated` — deprecated API registry",
            "- `GET /management/v1/migration/feature-flags` — runtime flags",
            "- `GET /management/v1/migration/health` — migration health",
            "",
            "## Disabling Legacy Completely",
            "",
            "Set all subsystems to `REMOVED` via `migration_manager.set_state()` and ensure all",
            "`legacy_*` flags are `false`. Legacy adapters become unreachable; Platform Core only.",
            "",
        ]
    )
    return "\n".join(sections)


def write_legacy_migration_doc(path: Path | None = None) -> Path:
    target = path or ROOT / "LEGACY_MIGRATION.md"
    target.write_text(generate_legacy_migration_markdown(), encoding="utf-8")
    return target


def main() -> None:
    path = write_legacy_migration_doc()
    print(f"Wrote {path}")
