export const COLLAB_STEPS = [
  "AI Team Creation",
  "Role Assignment",
  "Collaborative Session",
  "Task Distribution",
  "Shared Knowledge",
  "Decision Engine",
  "Executive Summary",
  "Team Performance",
  "Explain Decision",
  "AI Operations Center Foundation",
  "Create",
] as const;

export const PRIORITIES = ["critical", "high", "medium", "low"] as const;

export const DEFAULT_SPECIALISTS = [
  { id: "ai_legal", name: "Legal Specialist" },
  { id: "ai_finance", name: "Finance Specialist" },
  { id: "ai_ops", name: "Operations Specialist" },
  { id: "ai_marketing", name: "Marketing Specialist" },
] as const;
