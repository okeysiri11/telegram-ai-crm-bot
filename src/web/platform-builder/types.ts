export const PLATFORM_BUILDER_VERSION = "1.2.0";
export const PLATFORM_BUILDER_SPRINT = "28.3";
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
  "AI Orchestration",
  "Proactive Assistance",
  "Owner Relationship",
  "Smart Recommendations",
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
