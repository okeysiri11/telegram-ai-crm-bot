/** Demo scenario catalog — Sprint 32.3.5. Existing routes only. */

export type DemoStep = {
  id: string;
  title: string;
  description: string;
  route: string;
  cta: string;
  duration: string;
};

export const DEMO_SCENARIO_STEPS: DemoStep[] = [
  {
    id: "first_entry",
    title: "Первый вход",
    description: "Welcome → роль → workspace → AI Team → Concierge",
    route: "/onboarding/first-entry",
    cta: "First Entry",
    duration: "2 мин",
  },
  {
    id: "role",
    title: "Выбор роли",
    description: "В т.ч. Владелец / Executive для режима руководителя",
    route: "/onboarding/first-entry",
    cta: "Роль",
    duration: "30 с",
  },
  {
    id: "workspace",
    title: "Workspace",
    description: "Домашний экран организации",
    route: "/workspace",
    cta: "Workspace",
    duration: "30 с",
  },
  {
    id: "dashboard",
    title: "Dashboard / Executive",
    description: "Command Center или Executive Mode",
    route: "/dashboard?mode=executive",
    cta: "Dashboard",
    duration: "1 мин",
  },
  {
    id: "mission_control",
    title: "Mission Control",
    description: "Живая телеметрия экосистем",
    route: "/platform-builder/mission-control",
    cta: "Mission Control",
    duration: "1 мин",
  },
  {
    id: "city",
    title: "Enterprise City",
    description: "Визуальная навигация по модулям",
    route: "/enterprise-city",
    cta: "City",
    duration: "1 мин",
  },
  {
    id: "ai",
    title: "AI Activity",
    description: "AI Team и live operations",
    route: "/platform-builder/ai-team",
    cta: "AI Team",
    duration: "45 с",
  },
  {
    id: "crm",
    title: "CRM",
    description: "Клиенты и сделки",
    route: "/workspace/crm",
    cta: "CRM",
    duration: "45 с",
  },
  {
    id: "back",
    title: "Возврат на Dashboard",
    description: "Завершение демо-петли",
    route: "/dashboard",
    cta: "Dashboard",
    duration: "15 с",
  },
];
