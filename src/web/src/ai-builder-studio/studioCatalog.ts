/**
 * AI Builder Studio catalogs — Sprint 32.8.
 * Composes existing AI Builder / Workflow / ecosystem catalogs.
 * No new Builder Engine.
 */

import { PROFESSIONS, SKILLS, COMMUNICATION_STYLES, PERMISSIONS } from "../../platform-builder/ai-builder/catalog";
import { BUSINESS_WORKFLOW_TEMPLATES } from "@/enterprise-workflow";
import { PRIORITIES } from "../../platform-builder/collaborative-ai/catalog";

export type StudioSectionId =
  | "home"
  | "team"
  | "workflow"
  | "knowledge"
  | "integrations"
  | "skills"
  | "prompts"
  | "templates"
  | "wizard";

export type StudioHomeCard = {
  id: StudioSectionId;
  title: string;
  detail: string;
  route?: string;
};

export const STUDIO_HOME_CARDS: StudioHomeCard[] = [
  { id: "team", title: "AI Team", detail: "Состав специалистов и роли" },
  { id: "workflow", title: "Workflow", detail: "Визуальные бизнес-процессы" },
  { id: "knowledge", title: "Knowledge", detail: "База знаний и источники", route: "/platform-builder/knowledge" },
  { id: "integrations", title: "Integrations", detail: "CRM · Finance · Notifications" },
  { id: "skills", title: "Skills", detail: "Библиотека навыков" },
  { id: "prompts", title: "Prompt Library", detail: "Системные и корпоративные промпты" },
  { id: "templates", title: "Templates", detail: "Шаблоны экосистем" },
  { id: "wizard", title: "Create Agent", detail: "Классический AI Builder wizard", route: "/platform-builder/ai?mode=wizard" },
];

/** Domain skill packs for Skill Library (SECTION 4). */
export const DOMAIN_SKILL_PACKS = [
  { id: "crm", title: "CRM", skills: ["crm_operations", "answer_questions", "recommendations"] },
  { id: "marketing", title: "Marketing", skills: ["create_reports", "recommendations", "automation"] },
  { id: "sales", title: "Sales", skills: ["crm_operations", "recommendations", "answer_questions"] },
  { id: "legal", title: "Legal", skills: ["analyze_documents", "create_contracts", "answer_questions"] },
  { id: "analytics", title: "Analytics", skills: ["analytics", "create_reports", "recommendations"] },
  { id: "finance", title: "Finance", skills: ["analytics", "create_reports", "workflow"] },
  { id: "knowledge", title: "Knowledge", skills: ["analyze_documents", "answer_questions", "learning"] },
  { id: "automation", title: "Automation", skills: ["automation", "workflow", "recommendations"] },
] as const;

export type PromptKind = "system" | "user" | "corporate" | "favorite";

export type PromptItem = {
  id: string;
  title: string;
  kind: PromptKind;
  body: string;
  style?: string;
};

/** Prompt library derived from communication styles + studio presets. */
export const PROMPT_LIBRARY: PromptItem[] = [
  ...COMMUNICATION_STYLES.map((s) => ({
    id: `sys_${s.id}`,
    title: `System · ${s.name}`,
    kind: "system" as const,
    body: s.sample,
    style: s.id,
  })),
  {
    id: "corp_brand",
    title: "Corporate · Brand voice",
    kind: "corporate",
    body: "Отвечай от имени компании, сохраняй тон бренда и ссылайся на Knowledge Base.",
  },
  {
    id: "corp_compliance",
    title: "Corporate · Compliance",
    kind: "corporate",
    body: "Перед ответом проверь юридические и финансовые ограничения. Не выдумывай факты.",
  },
  {
    id: "user_brief",
    title: "User · Daily brief",
    kind: "user",
    body: "Собери краткую сводку: задачи, риски, рекомендации AI Team.",
  },
  {
    id: "user_crm",
    title: "User · CRM follow-up",
    kind: "user",
    body: "Подготовь follow-up по просроченным сделкам и предложи next best action.",
  },
  {
    id: "fav_exec",
    title: "Favorite · Executive snapshot",
    kind: "favorite",
    body: "Сформируй Executive Snapshot: что происходит, что требует внимания, что рекомендует AI.",
  },
  {
    id: "fav_handoff",
    title: "Favorite · Agent handoff",
    kind: "favorite",
    body: "Передай задачу следующему специалисту с кратким контекстом и ожидаемым результатом.",
  },
];

export type EcosystemTemplate = {
  id: string;
  title: string;
  detail: string;
  route: string;
};

/** Seven Business Ecosystems — Template Library (SECTION 6). */
export const ECOSYSTEM_TEMPLATES: EcosystemTemplate[] = [
  { id: "beauty", title: "Beauty", detail: "Салон · booking · client care", route: "/workspace/beauty" },
  { id: "legal", title: "Legal", detail: "Дела · договоры · compliance", route: "/workspace/legal" },
  { id: "cafe", title: "Cafe", detail: "Заказы · меню · операции", route: "/workspace/cafe" },
  { id: "auto", title: "Automotive", detail: "Сервис · клиенты · склад", route: "/workspace/auto" },
  { id: "agro", title: "Agriculture", detail: "Поля · поставки · агрономия", route: "/workspace/agro" },
  { id: "drone", title: "Drone", detail: "Флот · миссии · production", route: "/workspace/drone" },
  { id: "crypto", title: "Bidex", detail: "Активы · риск · treasury", route: "/workspace/crypto" },
];

export const INTEGRATION_CARDS = [
  { id: "crm", title: "CRM", route: "/workspace/crm", detail: "Клиенты и сделки" },
  { id: "finance", title: "Finance", route: "/workspace/finance", detail: "Финансы и счета" },
  { id: "knowledge", title: "Knowledge Base", route: "/platform-builder/knowledge", detail: "Документы и playbooks" },
  { id: "notifications", title: "Notification Center", route: "/dashboard", detail: "Алерты и тосты" },
  { id: "mission", title: "Mission Control", route: "/platform-builder/mission-control", detail: "Операционный контур" },
  { id: "city", title: "Enterprise City", route: "/enterprise-city", detail: "Визуальная карта" },
];

export function studioCatalogStats() {
  return {
    professions: PROFESSIONS.length,
    skills: SKILLS.length,
    permissions: PERMISSIONS.length,
    prompts: PROMPT_LIBRARY.length,
    workflows: BUSINESS_WORKFLOW_TEMPLATES.length,
    templates: ECOSYSTEM_TEMPLATES.length,
    domainPacks: DOMAIN_SKILL_PACKS.length,
    priorities: PRIORITIES.length,
  };
}

export { PROFESSIONS, SKILLS, PERMISSIONS, PRIORITIES, BUSINESS_WORKFLOW_TEMPLATES };
