/**
 * Sprint 30.6 — Beta Live Demo scenario (first coherent walkthrough).
 * Extends demoScenarioCatalog; uses existing routes only.
 */

export type LiveDemoStep = {
  id: string;
  title: string;
  titleRu: string;
  description: string;
  route: string;
  cta: string;
};

export const BETA_LIVE_DEMO_STEPS: LiveDemoStep[] = [
  {
    id: "login",
    title: "Login",
    titleRu: "Вход",
    description: "Google / email login → enterprise session",
    route: "/login",
    cta: "Войти",
  },
  {
    id: "dashboard",
    title: "Dashboard",
    titleRu: "Дашборд",
    description: "Beta Home · role-aware landing",
    route: "/dashboard",
    cta: "Дашборд",
  },
  {
    id: "city",
    title: "Enterprise City",
    titleRu: "Город предприятия",
    description: "Interactive map · districts · buildings",
    route: "/city",
    cta: "Открыть город",
  },
  {
    id: "building",
    title: "Open Building",
    titleRu: "Открыть здание",
    description: "CRM Center from City (real module)",
    route: "/enterprise-city?building=crm",
    cta: "CRM здание",
  },
  {
    id: "ai_agent",
    title: "Launch AI Agent",
    titleRu: "Запуск AI-агента",
    description: "AI Agent Center · create & start task",
    route: "/ai-agents",
    cta: "AI-центр",
  },
  {
    id: "production",
    title: "Production Studio",
    titleRu: "Продакшн-студия",
    description: "Image · Video · Voice · Presentation · Prompts",
    route: "/production-studio",
    cta: "Продакшн",
  },
  {
    id: "generate",
    title: "Generate task",
    titleRu: "Создать задачу",
    description: "Russian CTA · Создать изображение",
    route: "/production-studio?studio=image",
    cta: "Создать изображение",
  },
  {
    id: "result",
    title: "Return result",
    titleRu: "Результат",
    description: "History · runtime queue · agent task status",
    route: "/production-studio?tab=history",
    cta: "История",
  },
];

export const BETA_LIVE_DEMO_META = {
  product: "ADOS Enterprise Platform · Beta Live Demo",
  sprint: "30.6",
  durationMin: 8,
  durationMax: 15,
  pitchRu:
    "Вход → Дашборд → Город → Здание → AI-агент → Продакшн → Задача → Результат — одна платформа.",
} as const;
