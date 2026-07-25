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
  { id: "ai", name: "AI Builder", route: "/platform-builder/ai", kind: "builder", status: "operational", steps: AI_BUILDER_STEPS, frameOnly: false, purpose: "Compose AI agent teams with clear roles and personalities." },
  { id: "concierge", name: "Concierge Builder", route: "/platform-builder/concierge", kind: "builder", status: "operational", steps: CONCIERGE_STEPS, frameOnly: false, purpose: "Configure the single organizational Concierge assistant.", constraints: { onePerOrganization: true, separateFromAiAgents: true } },
  { id: "ai_team", name: "AI Team Center", route: "/platform-builder/ai-team", kind: "hub", status: "operational", purpose: "Monitor and manage all AI Specialists for the organization." },
  { id: "collaborative_ai", name: "Collaborative AI", route: "/platform-builder/collaborative-ai", kind: "builder", status: "operational", purpose: "Coordinate AI Specialists via Concierge for collective intelligence." },
  { id: "operations_center", name: "AI Operations Center", route: "/platform-builder/operations", kind: "hub", status: "operational", purpose: "Real-time visual control room for the AI Organization." },
  { id: "team_map", name: "AI Team Map", route: "/platform-builder/team-map", kind: "hub", status: "operational", purpose: "Live Organization Map with Visual Event Bus and relationship engine." },
  { id: "crm", name: "CRM Builder", route: "/platform-builder/crm", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "erp", name: "ERP Builder", route: "/platform-builder/erp", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "workflow", name: "Workflow Builder", route: "/platform-builder/workflow", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "knowledge", name: "Knowledge Builder", route: "/platform-builder/knowledge", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "automation", name: "Automation Builder", route: "/platform-builder/automation", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "dashboard_builder", name: "Dashboard Builder", route: "/platform-builder/dashboard-builder", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "template", name: "Template Builder", route: "/platform-builder/template", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
  { id: "marketplace", name: "Marketplace Builder", route: "/platform-builder/marketplace", kind: "builder", status: "frame", steps: GENERIC_STEPS, frameOnly: true },
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
