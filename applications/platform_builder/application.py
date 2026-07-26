"""Platform Builder application facade — Sprint 29.14."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from applications.platform_builder.academy import BuilderAcademy
from applications.platform_builder.academy_v2.engine import AcademyV2
from applications.platform_builder.control_center.control_center import PlatformControlCenter
from applications.platform_builder.collaborative_ai.engine import CollaborativeAIEngine
from applications.platform_builder.operations_center.engine import OperationsCenter
from applications.platform_builder.team_map.engine import LiveOrganizationMap
from applications.platform_builder.visual_behavior.engine import VisualBehaviorEngine
from applications.platform_builder.rendering.engine import VisualRenderingEngine
from applications.platform_builder.themes.engine import VisualThemeEngine
from applications.platform_builder.assets.engine import VisualAssetRegistry
from applications.platform_builder.simulation.engine import VisualSimulationEngine
from applications.platform_builder.director.engine import VisualDirectorEngine
from applications.platform_builder.story.engine import VisualStoryEngine
from applications.platform_builder.intelligence.engine import VisualIntelligenceEngine
from applications.platform_builder.experience.engine import VisualExperienceEngine
from applications.platform_builder.workspace_os.engine import EnterpriseWorkspaceOS
from applications.platform_builder.command_center.engine import EnterpriseCommandCenter
from applications.platform_builder.navigation_intelligence.engine import NavigationIntelligenceEngine
from applications.platform_builder.ai_builder.wizard import AIBuilderWizard
from applications.platform_builder.ai_team.team_center import AITeamCenter
from applications.platform_builder.builder_engine import BuilderEngine
from applications.platform_builder.catalog import BUILDERS, menu_for_role
from applications.platform_builder.concierge.wizard import ConciergeWizard
from applications.platform_builder.config import DEFAULT_CONFIG, PlatformBuilderConfig
from applications.platform_builder.framework.engine import UniversalBuilderFramework
from applications.platform_builder.god_mode import PLATFORM_OWNER_ROLE, GodMode, is_platform_owner
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store
from applications.platform_builder.vertical.wizard import VerticalWizard

ROOT = Path(__file__).resolve().parents[2]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PlatformBuilderApplication:
    def __init__(
        self,
        *,
        config: PlatformBuilderConfig | None = None,
        store: PlatformBuilderStore | None = None,
        engine: BuilderEngine | None = None,
        academy: BuilderAcademy | None = None,
        god_mode: GodMode | None = None,
        ai_builder: AIBuilderWizard | None = None,
        concierge: ConciergeWizard | None = None,
        ai_team: AITeamCenter | None = None,
        vertical: VerticalWizard | None = None,
        ubf: UniversalBuilderFramework | None = None,
        academy_v2: AcademyV2 | None = None,
        control_center: PlatformControlCenter | None = None,
        collaborative_ai: CollaborativeAIEngine | None = None,
        operations_center: OperationsCenter | None = None,
        team_map: LiveOrganizationMap | None = None,
        visual_behavior: VisualBehaviorEngine | None = None,
        rendering: VisualRenderingEngine | None = None,
        themes: VisualThemeEngine | None = None,
        assets: VisualAssetRegistry | None = None,
        simulation: VisualSimulationEngine | None = None,
        director: VisualDirectorEngine | None = None,
        story: VisualStoryEngine | None = None,
        intelligence: VisualIntelligenceEngine | None = None,
        experience: VisualExperienceEngine | None = None,
        workspace_os: EnterpriseWorkspaceOS | None = None,
        command_center_os: EnterpriseCommandCenter | None = None,
        navigation_intelligence: NavigationIntelligenceEngine | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or platform_builder_store
        self.engine = engine or BuilderEngine(self.store)
        self.academy = academy or BuilderAcademy(self.store)
        self.god_mode = god_mode or GodMode(self.store)
        self.ai_builder = ai_builder or AIBuilderWizard(self.store)
        self.concierge = concierge or ConciergeWizard(self.store)
        self.ai_team = ai_team or AITeamCenter(self.store)
        self.vertical = vertical or VerticalWizard(self.store)
        self.ubf = ubf or UniversalBuilderFramework(self.store)
        self.academy_v2 = academy_v2 or AcademyV2(self.store)
        self.control_center = control_center or PlatformControlCenter(self.store, self.god_mode)
        self.collaborative_ai = collaborative_ai or CollaborativeAIEngine(self.store)
        self.operations_center = operations_center or OperationsCenter(self.store)
        self.team_map = team_map or LiveOrganizationMap(self.store)
        self.visual_behavior = visual_behavior or VisualBehaviorEngine(self.store)
        self.rendering = rendering or VisualRenderingEngine(self.store, behavior=self.visual_behavior)
        self.themes = themes or VisualThemeEngine(self.store)
        self.assets = assets or VisualAssetRegistry(self.store)
        self.simulation = simulation or VisualSimulationEngine(self.store)
        self.director = director or VisualDirectorEngine(self.store)
        self.story = story or VisualStoryEngine(self.store)
        self.intelligence = intelligence or VisualIntelligenceEngine(self.store)
        self.experience = experience or VisualExperienceEngine(self.store)
        self.workspace_os = workspace_os or EnterpriseWorkspaceOS(self.store)
        self.command_center_os = command_center_os or EnterpriseCommandCenter(self.store)
        self.navigation_intelligence = navigation_intelligence or NavigationIntelligenceEngine(self.store)

    def reset(self) -> None:
        self.store.reset()
        self.academy = BuilderAcademy(self.store)
        self.god_mode = GodMode(self.store)
        self.engine = BuilderEngine(self.store)
        self.ai_builder = AIBuilderWizard(self.store)
        self.concierge = ConciergeWizard(self.store)
        self.ai_team = AITeamCenter(self.store)
        self.vertical = VerticalWizard(self.store)
        self.ubf = UniversalBuilderFramework(self.store)
        self.academy_v2 = AcademyV2(self.store)
        self.control_center = PlatformControlCenter(self.store, self.god_mode)
        self.collaborative_ai = CollaborativeAIEngine(self.store)
        self.operations_center = OperationsCenter(self.store)
        self.team_map = LiveOrganizationMap(self.store)
        self.visual_behavior = VisualBehaviorEngine(self.store)
        self.rendering = VisualRenderingEngine(self.store, behavior=self.visual_behavior)
        self.themes = VisualThemeEngine(self.store)
        self.assets = VisualAssetRegistry(self.store)
        self.simulation = VisualSimulationEngine(self.store)
        self.director = VisualDirectorEngine(self.store)
        self.story = VisualStoryEngine(self.store)
        self.intelligence = VisualIntelligenceEngine(self.store)
        self.experience = VisualExperienceEngine(self.store)
        self.workspace_os = EnterpriseWorkspaceOS(self.store)
        self.command_center_os = EnterpriseCommandCenter(self.store)
        self.navigation_intelligence = NavigationIntelligenceEngine(self.store)

    def bootstrap(self) -> dict[str, Any]:
        web = ROOT / "src" / "web" / "platform-builder"
        ubf_boot = self.ubf.bootstrap()
        bid = _id("pb_boot")
        record = {
            "bootstrap_id": bid,
            "bootstrap": True,
            "version": self.config.application_version,
            "sprint": self.config.sprint,
            "application": self.config.application,
            "api_prefix": self.config.api_prefix,
            "builder_engine_ready": True,
            "builder_academy_ready": True,
            "god_mode_ready": True,
            "help_system_ready": True,
            "navigation_ready": True,
            "dark_theme_ready": True,
            "ai_builder_ready": True,
            "ai_wizard_ready": True,
            "ai_registry_ready": True,
            "concierge_builder_ready": True,
            "concierge_registry_ready": True,
            "ai_team_center_ready": True,
            "group_ai_foundation_ready": True,
            "vertical_builder_ready": True,
            "vertical_registry_ready": True,
            "platform_registry_ready": True,
            "visual_layer_ready": True,
            "organization_preview_ready": True,
            "universal_builder_framework_ready": True,
            "builder_registry_ready": True,
            "template_engine_ready": True,
            "builder_sdk_foundation_ready": True,
            "academy_2_ready": True,
            "ai_guide_ready": True,
            "interactive_learning_ready": True,
            "recommendation_engine_ready": True,
            "progress_tracking_ready": True,
            "god_mode_expansion_ready": True,
            "platform_control_center_ready": True,
            "architecture_explorer_ready": True,
            "audit_center_ready": True,
            "platform_diagnostics_ready": True,
            "system_health_center_ready": True,
            "collaborative_ai_ready": True,
            "collective_intelligence_ready": True,
            "decision_engine_ready": True,
            "knowledge_exchange_ready": True,
            "ai_ops_foundation_ready": True,
            "operations_center_ready": True,
            "live_status_engine_ready": True,
            "visual_layer_ready": True,
            "status_dashboard_ready": True,
            "team_map_ready": True,
            "live_organization_ready": True,
            "relationship_engine_ready": True,
            "visual_event_bus_connected": True,
            "animation_layer_ready": True,
            "visual_behavior_engine_ready": True,
            "animation_framework_ready": True,
            "transition_engine_ready": True,
            "behavior_performance_optimized": True,
            "rendering_engine_ready": True,
            "visual_lod_engine_ready": True,
            "viewport_engine_ready": True,
            "layer_system_ready": True,
            "render_performance_monitor_ready": True,
            "theme_engine_ready": True,
            "branding_engine_ready": True,
            "theme_registry_ready": True,
            "live_theme_switching_ready": True,
            "visual_asset_registry_ready": True,
            "version_management_ready": True,
            "optimization_engine_ready": True,
            "asset_browser_ready": True,
            "simulation_engine_ready": True,
            "timeline_ready": True,
            "live_simulation_ready": True,
            "simulation_performance_optimized": True,
            "director_engine_ready": True,
            "scene_manager_ready": True,
            "focus_engine_ready": True,
            "priority_manager_ready": True,
            "story_engine_ready": True,
            "story_timeline_ready": True,
            "executive_story_ready": True,
            "milestone_viewer_ready": True,
            "visual_intelligence_engine_ready": True,
            "insight_engine_ready": True,
            "analytics_ready": True,
            "recommendation_engine_ready": True,
            "health_index_ready": True,
            "experience_engine_ready": True,
            "unified_ux_ready": True,
            "adaptive_interface_ready": True,
            "accessibility_operational": True,
            "workspace_os_ready": True,
            "workspace_manager_ready": True,
            "layout_engine_ready": True,
            "session_manager_ready": True,
            "context_engine_ready": True,
            "unified_workspace_platform_ready": True,
            "command_center_ready": True,
            "universal_command_platform_ready": True,
            "voice_foundation_ready": True,
            "ai_command_assistant_ready": True,
            "shortcut_engine_ready": True,
            "navigation_intelligence_engine_ready": True,
            "context_navigation_ready": True,
            "smart_navigation_ready": True,
            "platform_owner_role": PLATFORM_OWNER_ROLE,
            "builders_count": len(BUILDERS),
            "web_path_exists": web.exists(),
            "dashboard_page_exists": (web / "pages" / "PlatformBuilderDashboard.tsx").exists(),
            "framework_exists": (web / "framework" / "BuilderFramework.tsx").exists(),
            "ubf_page_exists": (web / "pages" / "UniversalFrameworkPage.tsx").exists(),
            "ai_builder_page_exists": (web / "pages" / "AIBuilderPage.tsx").exists(),
            "concierge_page_exists": (web / "pages" / "ConciergeBuilderPage.tsx").exists(),
            "vertical_page_exists": (web / "pages" / "VerticalBuilderPage.tsx").exists(),
            "collaborative_page_exists": (web / "pages" / "CollaborativeAIPage.tsx").exists(),
            "operations_page_exists": (web / "pages" / "OperationsCenterPage.tsx").exists(),
            "team_map_page_exists": (web / "pages" / "TeamMapPage.tsx").exists(),
            "visual_behavior_page_exists": (web / "pages" / "VisualBehaviorPage.tsx").exists(),
            "rendering_page_exists": (web / "pages" / "RenderingEnginePage.tsx").exists(),
            "themes_page_exists": (web / "pages" / "ThemeEnginePage.tsx").exists(),
            "assets_page_exists": (web / "pages" / "AssetRegistryPage.tsx").exists(),
            "simulation_page_exists": (web / "pages" / "SimulationEnginePage.tsx").exists(),
            "director_page_exists": (web / "pages" / "DirectorEnginePage.tsx").exists(),
            "story_page_exists": (web / "pages" / "StoryEnginePage.tsx").exists(),
            "intelligence_page_exists": (web / "pages" / "IntelligenceEnginePage.tsx").exists(),
            "experience_page_exists": (web / "pages" / "ExperienceEnginePage.tsx").exists(),
            "workspace_os_page_exists": (web / "pages" / "WorkspaceOSPage.tsx").exists(),
            "command_center_page_exists": (web / "pages" / "CommandCenterOSPage.tsx").exists(),
            "navigation_intelligence_page_exists": (
                web / "pages" / "NavigationIntelligencePage.tsx"
            ).exists(),
            "ubf_bootstrap": ubf_boot,
            "bootstrapped_at": _now(),
        }
        self.store.bootstraps.save(bid, record)
        return record

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "sprint": self.config.sprint,
            "release_status": self.config.release_status,
            "api_prefix": self.config.api_prefix,
            "platform_builder_ready": True,
            "builder_framework_ready": True,
            "builder_academy_ready": True,
            "god_mode_ready": True,
            "builder_navigation_ready": True,
            "help_system_ready": True,
            "dark_theme_ready": True,
            "ai_builder_ready": True,
            "ai_wizard_ready": True,
            "multi_agent_builder_ready": True,
            "knowledge_selector_ready": True,
            "personality_builder_ready": True,
            "ai_registry_ready": True,
            "group_ai_chat_foundation_ready": True,
            "concierge_builder_ready": True,
            "concierge_registry_ready": True,
            "organization_link_ready": True,
            "concierge_orchestration_ready": True,
            "concierge_preview_ready": True,
            "ai_team_center_ready": True,
            "ai_dashboard_ready": True,
            "group_ai_foundation_ready": True,
            "vertical_builder_ready": True,
            "vertical_registry_ready": True,
            "platform_registry_ready": True,
            "visual_layer_ready": True,
            "organization_preview_ready": True,
            "universal_builder_framework_ready": True,
            "builder_registry_ready": True,
            "template_engine_ready": True,
            "builder_sdk_foundation_ready": True,
            "live_preview_engine_ready": True,
            "validation_framework_ready": True,
            "extension_system_ready": True,
            "academy_2_ready": True,
            "ai_guide_ready": True,
            "interactive_learning_ready": True,
            "recommendation_engine_ready": True,
            "progress_tracking_ready": True,
            "live_builder_analysis_ready": True,
            "god_mode_expansion_ready": True,
            "platform_control_center_ready": True,
            "architecture_explorer_ready": True,
            "audit_center_ready": True,
            "platform_diagnostics_ready": True,
            "system_health_center_ready": True,
            "collaborative_ai_ready": True,
            "collective_intelligence_ready": True,
            "decision_engine_ready": True,
            "knowledge_exchange_ready": True,
            "ai_ops_foundation_ready": True,
            "operations_center_ready": True,
            "live_status_engine_ready": True,
            "status_dashboard_ready": True,
            "team_map_ready": True,
            "live_organization_ready": True,
            "relationship_engine_ready": True,
            "visual_event_bus_connected": True,
            "animation_layer_ready": True,
            "visual_behavior_engine_ready": True,
            "animation_framework_ready": True,
            "transition_engine_ready": True,
            "behavior_performance_optimized": True,
            "rendering_engine_ready": True,
            "visual_lod_engine_ready": True,
            "viewport_engine_ready": True,
            "layer_system_ready": True,
            "render_performance_monitor_ready": True,
            "theme_engine_ready": True,
            "branding_engine_ready": True,
            "theme_registry_ready": True,
            "live_theme_switching_ready": True,
            "visual_asset_registry_ready": True,
            "version_management_ready": True,
            "optimization_engine_ready": True,
            "asset_browser_ready": True,
            "simulation_engine_ready": True,
            "timeline_ready": True,
            "live_simulation_ready": True,
            "simulation_performance_optimized": True,
            "director_engine_ready": True,
            "scene_manager_ready": True,
            "focus_engine_ready": True,
            "priority_manager_ready": True,
            "story_engine_ready": True,
            "story_timeline_ready": True,
            "executive_story_ready": True,
            "milestone_viewer_ready": True,
            "visual_intelligence_engine_ready": True,
            "insight_engine_ready": True,
            "analytics_ready": True,
            "recommendation_engine_ready": True,
            "health_index_ready": True,
            "experience_engine_ready": True,
            "unified_ux_ready": True,
            "adaptive_interface_ready": True,
            "accessibility_operational": True,
            "workspace_os_ready": True,
            "workspace_manager_ready": True,
            "layout_engine_ready": True,
            "session_manager_ready": True,
            "context_engine_ready": True,
            "unified_workspace_platform_ready": True,
            "command_center_ready": True,
            "universal_command_platform_ready": True,
            "voice_foundation_ready": True,
            "ai_command_assistant_ready": True,
            "shortcut_engine_ready": True,
            "navigation_intelligence_engine_ready": True,
            "context_navigation_ready": True,
            "smart_navigation_ready": True,
            "engines": {
                "builder_engine": self.config.builder_engine,
                "builder_academy": self.config.builder_academy,
                "god_mode": self.config.god_mode,
                "help_system": self.config.help_system,
                "ai_builder": self.config.ai_builder,
                "concierge_builder": self.config.concierge_builder,
                "ai_team_center": self.config.ai_team_center,
                "vertical_builder": self.config.vertical_builder,
                "universal_builder_framework": self.config.universal_builder_framework,
                "builder_sdk": self.config.builder_sdk,
                "ai_guide": self.config.ai_guide,
                "platform_control_center": self.config.platform_control_center,
                "collaborative_ai": self.config.collaborative_ai,
                "collective_intelligence": self.config.collective_intelligence,
                "operations_center": self.config.operations_center,
                "visual_layer": self.config.visual_layer,
                "live_status_engine": self.config.live_status_engine,
                "team_map": self.config.team_map,
                "live_organization": self.config.live_organization,
                "visual_event_bus": self.config.visual_event_bus,
                "visual_behavior_engine": self.config.visual_behavior_engine,
                "animation_framework": self.config.animation_framework,
                "transition_engine": self.config.transition_engine,
                "rendering_engine": self.config.rendering_engine,
                "visual_lod_engine": self.config.visual_lod_engine,
                "viewport_engine": self.config.viewport_engine,
                "layer_system": self.config.layer_system,
                "theme_engine": self.config.theme_engine,
                "theme_registry": self.config.theme_registry,
                "branding_engine": self.config.branding_engine,
                "visual_asset_registry": self.config.visual_asset_registry,
                "version_registry": self.config.version_registry,
                "optimization_engine": self.config.optimization_engine,
                "simulation_engine": self.config.simulation_engine,
                "simulation_registry": self.config.simulation_registry,
                "timeline_engine": self.config.timeline_engine,
                "simulation_api": self.config.simulation_api,
                "director_engine": self.config.director_engine,
                "scene_manager": self.config.scene_manager,
                "focus_manager": self.config.focus_manager,
                "priority_manager": self.config.priority_manager,
                "story_engine": self.config.story_engine,
                "story_registry": self.config.story_registry,
                "story_builder": self.config.story_builder,
                "story_timeline": self.config.story_timeline,
                "executive_story_api": self.config.executive_story_api,
                "visual_intelligence_engine": self.config.visual_intelligence_engine,
                "insight_engine": self.config.insight_engine,
                "recommendation_engine": self.config.recommendation_engine,
                "analytics_registry": self.config.analytics_registry,
                "experience_engine": self.config.experience_engine,
                "experience_registry": self.config.experience_registry,
                "ux_rules_registry": self.config.ux_rules_registry,
                "adaptive_ui_registry": self.config.adaptive_ui_registry,
                "workspace_os": self.config.workspace_os,
                "workspace_registry": self.config.workspace_registry,
                "layout_engine": self.config.layout_engine,
                "context_engine": self.config.context_engine,
                "session_manager": self.config.session_manager,
                "command_center": self.config.command_center,
                "command_registry": self.config.command_registry,
                "command_api": self.config.command_api,
                "shortcut_engine": self.config.shortcut_engine,
                "voice_api": self.config.voice_api,
                "navigation_intelligence_engine": self.config.navigation_intelligence_engine,
                "navigation_registry": self.config.navigation_registry,
                "recommendation_api": self.config.recommendation_api,
                "context_api": self.config.context_api,
            },
            "ai_builder": self.ai_builder.status(),
            "concierge": self.concierge.status(),
            "ai_team": self.ai_team.status(),
            "vertical": self.vertical.status(),
            "ubf": self.ubf.status(),
            "academy_v2": self.academy_v2.status(),
            "control_center": {
                "status": "online",
                "owner_gated": True,
                "version": self.config.god_mode,
                "sprint": self.config.sprint,
            },
            "collaborative_ai": self.collaborative_ai.status(),
            "operations_center": self.operations_center.status(),
            "team_map": self.team_map.status(),
            "visual_behavior": self.visual_behavior.status(),
            "rendering": self.rendering.status(),
            "themes": self.themes.status(),
            "assets": self.assets.status(),
            "simulation": self.simulation.status(),
            "director": self.director.status(),
            "story": self.story.status(),
            "intelligence": self.intelligence.status(),
            "experience": self.experience.status(),
            "workspace_os": self.workspace_os.status(),
            "command_center_os": self.command_center_os.status(),
            "navigation_intelligence": self.navigation_intelligence.status(),
        }

    def inventory(self) -> dict[str, Any]:
        return {
            "application": self.config.application,
            "version": self.config.application_version,
            "sprint": self.config.sprint,
            "framework_phases": list(self.config.framework_phases),
            "universal_lifecycle": list(self.config.universal_lifecycle),
            "academy_modes": list(self.config.academy_modes),
            "builders": self.engine.list_builders(),
            "platform_owner_role": PLATFORM_OWNER_ROLE,
            "ai_builder": self.ai_builder.catalog(),
            "concierge": self.concierge.catalog(),
            "vertical": self.vertical.catalog(),
            "ubf": self.ubf.catalog(),
            "academy_v2": self.academy_v2.catalog(),
        }

    def dashboard(self) -> dict[str, Any]:
        return {
            "title": "Platform Builder Dashboard",
            "version": self.config.application_version,
            "sprint": self.config.sprint,
            "builders": [
                {
                    "id": b["id"],
                    "name": b["name"],
                    "status": b["status"],
                    "route": b["route"],
                    "kind": b["kind"],
                }
                for b in BUILDERS
                if b["id"] != "god_mode"
            ],
            "academy": self.academy.status(),
            "framework": {
                "phases": list(self.config.framework_phases),
                "lifecycle": list(self.config.universal_lifecycle),
                "ready": True,
            },
            "ai_builder": self.ai_builder.status(),
            "concierge": self.concierge.status(),
            "ai_team": self.ai_team.status(),
            "vertical": self.vertical.status(),
            "ubf": self.ubf.status(),
            "academy_v2": self.academy_v2.status(),
            "stats": {
                "builders": len([b for b in BUILDERS if b["kind"] == "builder"]),
                "frame_only": len([b for b in BUILDERS if b.get("frame_only")]),
                "operational": len([b for b in BUILDERS if b["status"] == "operational"]),
            },
        }

    def menu(self, role: str | None = None) -> dict[str, Any]:
        return {
            "section": "Platform Builder",
            "items": menu_for_role(role),
            "god_mode_visible": is_platform_owner(role),
        }

    def roles(self) -> dict[str, Any]:
        return {
            "roles": [
                {
                    "id": PLATFORM_OWNER_ROLE,
                    "name": "Platform Owner",
                    "scope": "platform",
                    "god_mode": True,
                    "description": "Full platform stewardship including God Mode.",
                },
                {
                    "id": "builder",
                    "name": "Builder",
                    "scope": "organization",
                    "god_mode": False,
                    "description": "Create objects through Platform Builder.",
                },
            ]
        }


platform_builder = PlatformBuilderApplication()
