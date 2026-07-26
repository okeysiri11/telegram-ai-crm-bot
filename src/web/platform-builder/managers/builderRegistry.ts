import type { AcademyMode, BuilderDef, HelpContent } from "../types";
import {
  AI_BUILDER_STEPS,
  CONCIERGE_STEPS,
  GENERIC_STEPS,
  UNIVERSAL_FRAMEWORK_STEPS,
  VERTICAL_STEPS,
} from "../types";

export const BUILDER_CATALOG: BuilderDef[] = [
  { id: "dashboard", name: "Dashboard", route: "/platform-builder", kind: "hub", status: "operational" },
  { id: "universal_framework", name: "Universal Builder Framework", route: "/platform-builder/framework", kind: "hub", status: "operational", steps: UNIVERSAL_FRAMEWORK_STEPS, purpose: "One common architecture for every Platform Builder." },
  { id: "vertical", name: "Vertical Builder", route: "/platform-builder/vertical", kind: "builder", status: "operational", steps: VERTICAL_STEPS, frameOnly: false, purpose: "Visually create complete Enterprise Verticals without programming." },
  { id: "ai", name: "AI Builder Studio", route: "/platform-builder/builder-studio", kind: "builder", status: "operational", steps: AI_BUILDER_STEPS, frameOnly: false, purpose: "Compose AI agent teams, workflows, skills and templates as a constructor." },
  { id: "builder_studio", name: "AI Builder Studio", route: "/platform-builder/builder-studio", kind: "hub", status: "operational", purpose: "Unified constructor for AI Team, Workflow, Skills, Prompts and Templates." },
  { id: "concierge", name: "Concierge Builder", route: "/platform-builder/concierge", kind: "builder", status: "operational", steps: CONCIERGE_STEPS, frameOnly: false, purpose: "Configure the single organizational Concierge assistant.", constraints: { onePerOrganization: true, separateFromAiAgents: true } },
  { id: "ai_team", name: "AI Team Center", route: "/platform-builder/ai-team", kind: "hub", status: "operational", purpose: "Monitor and manage all AI Specialists for the organization." },
  { id: "collaborative_ai", name: "Collaborative AI", route: "/platform-builder/collaborative-ai", kind: "builder", status: "operational", purpose: "Coordinate AI Specialists via Concierge for collective intelligence." },
  { id: "operations_center", name: "AI Operations Center", route: "/platform-builder/operations", kind: "hub", status: "operational", purpose: "Real-time visual control room for the AI Organization." },
  { id: "team_map", name: "AI Team Map", route: "/platform-builder/team-map", kind: "hub", status: "operational", purpose: "Live Organization Map with Visual Event Bus and relationship engine." },
  { id: "visual_behavior", name: "Visual Behavior Engine", route: "/platform-builder/visual-behavior", kind: "hub", status: "operational", purpose: "Event-bus-driven visual behaviors and animations — no business logic." },
  { id: "rendering", name: "Visual Rendering Engine", route: "/platform-builder/rendering", kind: "hub", status: "operational", purpose: "GPU-friendly rendering with LOD, viewport culling, and layer system." },
  { id: "themes", name: "Visual Theme Engine", route: "/platform-builder/themes", kind: "hub", status: "operational", purpose: "Enterprise visual identity, branding, and live theme switching — appearance only." },
  { id: "assets", name: "Visual Asset Registry", route: "/platform-builder/assets", kind: "hub", status: "operational", purpose: "Store, version, optimize, and browse visual assets — separated from business logic." },
  { id: "simulation", name: "Visual Simulation Engine", route: "/platform-builder/simulation", kind: "hub", status: "operational", purpose: "Live enterprise simulation from Visual Event Bus only — never creates fake events." },
  { id: "director", name: "Visual Director Engine", route: "/platform-builder/director", kind: "hub", status: "operational", purpose: "Scene orchestration and focus/attention direction — presentation only, no business events." },
  { id: "story", name: "Visual Story Engine", route: "/platform-builder/story", kind: "hub", status: "operational", purpose: "Enterprise storytelling from verified Visual Event Bus events — never creates or reorders business events." },
  { id: "intelligence", name: "Visual Intelligence Engine", route: "/platform-builder/intelligence", kind: "hub", status: "operational", purpose: "Visual analytics and recommendations from verified events — no business logic changes or business events." },
  { id: "experience", name: "Visual Experience Engine", route: "/platform-builder/experience", kind: "hub", status: "operational", purpose: "Unified enterprise UX coordinating all visual subsystems — presentation only, no business logic." },
  { id: "workspace_os", name: "Enterprise Workspace OS", route: "/platform-builder/workspace-os", kind: "hub", status: "operational", purpose: "Unified operating environment for every module with multi-workspace contexts — role aware." },
  { id: "command_center", name: "Enterprise Command Center", route: "/platform-builder/command-center", kind: "hub", status: "operational", purpose: "Universal command interface for modules, AI, workspaces and services — interaction orchestration only." },
  { id: "navigation_intelligence", name: "Navigation Intelligence Engine", route: "/platform-builder/navigation-intelligence", kind: "hub", status: "operational", purpose: "Predicts and simplifies navigation from verified context — never executes business logic." },
  { id: "workflow_intelligence", name: "Workflow Intelligence OS", route: "/platform-builder/workflow-intelligence", kind: "hub", status: "operational", purpose: "Workflow visibility, dependency analysis and recommendations — never executes business logic." },
  { id: "digital_twin", name: "Enterprise Digital Twin", route: "/enterprise-twin", kind: "hub", status: "operational", purpose: "Living organization mirror — org map, heatmap, impact, timeline over existing services." },
  { id: "digital_twin_studio", name: "Digital Twin Studio", route: "/platform-builder/digital-twin?studio=1", kind: "hub", status: "operational", purpose: "Classic session-based twin studio — read-only verified state." },
  { id: "twin_intelligence", name: "Digital Twin Intelligence", route: "/platform-builder/twin-intelligence", kind: "hub", status: "operational", purpose: "Analyzes verified Digital Twin data — never changes state or executes workflows." },
  { id: "strategy_engine", name: "Enterprise Strategy Engine", route: "/platform-builder/strategy", kind: "hub", status: "operational", purpose: "Strategic analysis and executive recommendations — never executes business logic." },
  { id: "mission_control", name: "Enterprise Mission Control", route: "/platform-builder/mission-control", kind: "hub", status: "operational", purpose: "Unified executive operating center — aggregates existing services, never replaces modules." },
  { id: "business_ecosystem", name: "Business Ecosystem Foundation", route: "/platform-builder/business-ecosystem", kind: "hub", status: "operational", purpose: "Reusable industry extension architecture — ecosystems extend platform core, never copy it." },
  { id: "crm", name: "CRM Builder", route: "/platform-builder/crm", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "erp", name: "ERP Builder", route: "/platform-builder/erp", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "workflow", name: "Workflow Builder", route: "/platform-builder/workflow", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "knowledge", name: "Knowledge Builder", route: "/platform-builder/knowledge", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "automation", name: "Automation Builder", route: "/platform-builder/automation", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "dashboard_builder", name: "Dashboard Builder", route: "/platform-builder/dashboard-builder", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "template", name: "Template Builder", route: "/platform-builder/template", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "marketplace", name: "Marketplace Builder", route: "/platform-builder/marketplace", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "solution_hub", name: "Enterprise Marketplace", route: "/platform-builder/solution-hub", kind: "hub", status: "operational", purpose: "One-click solutions over Builder Studio catalogs — no new Marketplace Engine." },
  { id: "academy", name: "Builder Academy 2.0", route: "/platform-builder/academy", kind: "academy", status: "operational", purpose: "Interactive learning, AI Guide, and adaptive builder guidance." },
  { id: "god_mode", name: "God Mode", route: "/platform-builder/god-mode", kind: "god_mode", status: "operational", requiresRole: "platform_owner" },
];

export function getBuilder(id: string): BuilderDef | undefined {
  return BUILDER_CATALOG.find((b) => b.id === id);
}

export function buildersForMenu(isPlatformOwner: boolean): BuilderDef[] {
  return BUILDER_CATALOG.filter((b) => b.requiresRole !== "platform_owner" || isPlatformOwner);
}

export function helpFor(item: string, builderName: string): HelpContent {
  return {
    shortDescription: `${item} for ${builderName}`,
    detailedExplanation: `${item} guides you through a clear configuration step inside ${builderName}. Each choice shapes how the resulting object behaves across the platform.`,
    example: `Example: configure «${item}» to match your team’s operating rhythm.`,
    popup: { title: item, body: `Use ${item} to capture the essentials for ${builderName}.` },
    tooltip: `Learn about ${item}`,
    purpose: "What this setting is for",
    benefits: "How it helps your organization",
    typicalUse: "Where teams usually apply it",
    businessValue: "Business outcomes it supports",
  };
}

export const ACADEMY_MODES: { id: AcademyMode; name: string; description: string }[] = [
  { id: "quick_start", name: "Quick Start", description: "Move quickly through essential steps with compact guidance." },
  { id: "guided_learning", name: "Guided Learning", description: "Explain every screen with purpose, benefits, and examples." },
  { id: "expert", name: "Expert Mode", description: "Minimal chrome for experienced platform builders." },
];
