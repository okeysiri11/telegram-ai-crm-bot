export const COLLAB_STEPS = [
  "AI Team Creation",
  "Роль Assignment",
  "Collaborative Session",
  "Task Distribution",
  "Shared База знаний",
  "Decision Engine",
  "Executive Итоги",
  "Team Performance",
  "Explain Decision",
  "Центр операций AI Foundation",
  "Создать",
] as const;

export const PRIORITIES = ["critical", "high", "medium", "low"] as const;

export const DEFAULT_SPECIALISTS = [
  { id: "ai_legal", name: "Legal Specialist" },
  { id: "ai_finance", name: "Finance Specialist" },
  { id: "ai_ops", name: "Operations Specialist" },
  { id: "ai_marketing", name: "Marketing Specialist" },
] as const;
