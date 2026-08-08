export const ACADEMY_V2_STEPS = [
  "User Experience Level",
  "Contextual Справка",
  "AI Guide",
  "Smart Recommendations",
  "Interactive Learning",
  "Live Builder Analysis",
  "Business Impact",
  "Academy Progress",
  "Итоги",
  "Создать",
] as const;

export const EXPERIENCE_LEVELS = [
  {
    id: "beginner",
    name: "Beginner",
    description: "Full explanations, walkthroughs, and protective defaults.",
  },
  {
    id: "intermediate",
    name: "Intermediate",
    description: "Balanced guidance with examples and recommendations.",
  },
  {
    id: "advanced",
    name: "Advanced",
    description: "Concise tips with optional deep dives.",
  },
  {
    id: "expert",
    name: "Expert",
    description: "Minimal chrome — guidance on demand only.",
  },
] as const;

export const HELP_FIELDS = [
  "explanation",
  "business_purpose",
  "example",
  "best_practice",
  "common_mistakes",
  "more_information",
] as const;

export const RECOMMENDATION_TYPES = [
  "AI Specialists",
  "Модули",
  "Отделы",
  "Панели управления",
  "Автоматизацияs",
  "Маркетплейс Apps",
  "База знаний Sources",
] as const;
