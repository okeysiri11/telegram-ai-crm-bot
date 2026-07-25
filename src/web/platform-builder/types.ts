export const PLATFORM_BUILDER_VERSION = "1.3.0";
export const PLATFORM_BUILDER_SPRINT = "28.4";
export const PLATFORM_BUILDER_API = "/api/platform-builder/v1";

export const FRAMEWORK_PHASES = [
  "step",
  "explanation",
  "information",
  "example",
  "preview",
  "create",
] as const;

export const AI_BUILDER_STEPS = [
  "Number of AI Agents",
  "AI Agent Name",
  "Profession",
  "Specialization",
  "Knowledge",
  "Skills",
  "Permissions",
  "Personality",
  "Summary",
  "Create",
] as const;

export const CONCIERGE_STEPS = [
  "Concierge Identity",
  "Concierge Role",
  "Organization Access",
  "AI Team Center",
  "AI Orchestration",
  "Proactive Assistance",
  "Owner Relationship",
  "Smart Recommendation Engine",
  "Group AI Chat Foundation",
  "Summary",
  "Create",
] as const;

export const VERTICAL_STEPS = [
  "Vertical Information",
  "Select Industry",
  "Module Selection",
  "AI Configuration",
  "AI Concierge",
  "Dashboard",
  "Workspace",
  "Live Organization Preview",
  "Summary",
  "Create",
] as const;

export const GENERIC_STEPS = [
  "Define Scope",
  "Configure Structure",
  "Set Options",
  "Review Information",
  "Preview",
  "Create",
] as const;

export type AcademyMode = "quick_start" | "guided_learning" | "expert";

export type BuilderDef = {
  id: string;
  name: string;
  route: string;
  kind: "hub" | "builder" | "academy" | "god_mode";
  status: string;
  steps?: readonly string[];
  purpose?: string;
  requiresRole?: "platform_owner";
  frameOnly?: boolean;
  constraints?: Record<string, boolean>;
};

export type HelpContent = {
  shortDescription: string;
  detailedExplanation: string;
  example: string;
  popup: { title: string; body: string };
  tooltip: string;
  purpose: string;
  benefits: string;
  typicalUse: string;
  businessValue: string;
};
