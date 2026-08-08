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

/** Sprint 42.4 — four primary hub cards (Human UX). */
export type HubCard = {
  id: string;
  icon: string;
  title: string;
  detail: string;
  section?: StudioSectionId;
  externalRoute?: string;
};

export const HUB_CARDS: HubCard[] = [
  {
    id: "concierge",
    icon: "🤖",
    title: "AI Консьерж",
    detail: "Создать и настроить главного помощника.",
    externalRoute: "/platform-builder/concierge",
  },
  {
    id: "team",
    icon: "👥",
    title: "Команда AI",
    detail: "Создать специализированных AI сотрудников.",
    section: "wizard",
  },
  {
    id: "settings",
    icon: "⚙",
    title: "Настройки платформы",
    detail: "Все системные параметры.",
    externalRoute: "/settings",
  },
  {
    id: "integrations",
    icon: "🔌",
    title: "Интеграции",
    detail: "Подключение сервисов и API.",
    section: "integrations",
  },
];

export const STUDIO_HOME_CARDS: StudioHomeCard[] = [
  { id: "team", title: "Команда AI", detail: "Состав специалистов и роли" },
  { id: "workflow", title: "Сценарии", detail: "Визуальные бизнес-процессы" },
  { id: "knowledge", title: "База знаний", detail: "Знания и источники", route: "/platform-builder/knowledge" },
  { id: "integrations", title: "Интеграции", detail: "CRM · Финансы · Уведомления" },
  { id: "skills", title: "Навыки", detail: "Библиотека навыков" },
  { id: "prompts", title: "Подсказки", detail: "Системные и корпоративные" },
  { id: "templates", title: "Шаблоны", detail: "Шаблоны экосистем" },
  { id: "wizard", title: "Создать агента", detail: "Мастер AI-агента", route: "/platform-builder/builder-studio?mode=wizard" },
];

/** Domain skill packs for Skill Library (SECTION 4). */
export const DOMAIN_SKILL_PACKS = [
  { id: "crm", title: "CRM", skills: ["crm_operations", "answer_questions", "recommendations"] },
  { id: "marketing", title: "Маркетинг", skills: ["create_reports", "recommendations", "automation"] },
  { id: "sales", title: "Продажи", skills: ["crm_operations", "recommendations", "answer_questions"] },
  { id: "legal", title: "Юриспруденция", skills: ["analyze_documents", "create_contracts", "answer_questions"] },
  { id: "analytics", title: "Аналитика", skills: ["analytics", "create_reports", "recommendations"] },
  { id: "finance", title: "Финансы", skills: ["analytics", "create_reports", "workflow"] },
  { id: "knowledge", title: "База знаний", skills: ["analyze_documents", "answer_questions", "learning"] },
  { id: "automation", title: "Автоматизация", skills: ["automation", "workflow", "recommendations"] },
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
    title: `Система · ${s.name}`,
    kind: "system" as const,
    body: s.sample,
    style: s.id,
  })),
  {
    id: "corp_brand",
    title: "Корпоративный · Голос бренда",
    kind: "corporate",
    body: "Отвечай от имени компании, сохраняй тон бренда и ссылайся на базу знаний.",
  },
  {
    id: "corp_compliance",
    title: "Корпоративный · Комплаенс",
    kind: "corporate",
    body: "Перед ответом проверь юридические и финансовые ограничения. Не выдумывай факты.",
  },
  {
    id: "user_brief",
    title: "Пользователь · Ежедневный бриф",
    kind: "user",
    body: "Собери краткую сводку: задачи, риски, рекомендации команды AI.",
  },
  {
    id: "user_crm",
    title: "Пользователь · Follow-up CRM",
    kind: "user",
    body: "Подготовь follow-up по просроченным сделкам и предложи следующее лучшее действие.",
  },
  {
    id: "fav_exec",
    title: "Избранное · Снимок для руководства",
    kind: "favorite",
    body: "Сформируй снимок для руководства: что происходит, что требует внимания, что рекомендует AI.",
  },
  {
    id: "fav_handoff",
    title: "Избранное · Передача агенту",
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
  { id: "beauty", title: "Красота", detail: "Салон · запись · забота о клиенте", route: "/workspace/beauty" },
  { id: "legal", title: "Юриспруденция", detail: "Дела · договоры · комплаенс", route: "/workspace/legal" },
  { id: "cafe", title: "Кафе", detail: "Заказы · меню · операции", route: "/workspace/cafe" },
  { id: "auto", title: "Авто", detail: "Сервис · клиенты · склад", route: "/workspace/auto" },
  { id: "agro", title: "Агро", detail: "Поля · поставки · агрономия", route: "/workspace/agro" },
  { id: "drone", title: "БПЛА", detail: "Флот · миссии · производство", route: "/workspace/drone" },
  { id: "crypto", title: "Bidex", detail: "Активы · риск · казна", route: "/workspace/crypto" },
];

export const INTEGRATION_CARDS = [
  { id: "crm", title: "CRM", route: "/crm", detail: "Клиенты и сделки" },
  { id: "finance", title: "Финансы", route: "/analytics", detail: "Финансы и счета" },
  { id: "knowledge", title: "База знаний", route: "/platform-builder/knowledge", detail: "Документы и плейбуки" },
  { id: "notifications", title: "Уведомления", route: "/notifications", detail: "Оповещения и тосты" },
  { id: "mission", title: "Миссион-контроль", route: "/platform-builder/mission-control", detail: "Операционный контур" },
  { id: "city", title: "Корпоративный город", route: "/city", detail: "Визуальная карта" },
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
