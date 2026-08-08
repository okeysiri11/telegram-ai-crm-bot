export const PLATFORM_BUILDER_VERSION = "1.67.0";
export const PLATFORM_BUILDER_SPRINT = "1.1.1";
export const PLATFORM_BUILDER_API = "/api/platform-builder/v1";

export const FRAMEWORK_PHASES = [
  "шаг",
  "пояснение",
  "информация",
  "пример",
  "предпросмотр",
  "создание",
] as const;

export const AI_BUILDER_STEPS = [
  "Количество",
  "Имя",
  "Назначение",
  "Специализация",
  "База знаний",
  "Навыки",
  "Права",
  "Стиль общения",
  "Итоги",
  "Готово",
] as const;

export const CONCIERGE_STEPS = [
  "Имя и образ",
  "Роль",
  "Стиль общения",
  "Навыки",
  "Модули",
  "Права",
  "Тестовый диалог",
] as const;

export const VERTICAL_STEPS = [
  "Сведения о вертикали",
  "Отрасль",
  "Модули",
  "Настройка AI",
  "AI Консьерж",
  "Панель управления",
  "Рабочее пространство",
  "Предпросмотр организации",
  "Итоги",
  "Создать",
] as const;

export const UNIVERSAL_FRAMEWORK_STEPS = [
  "Шаблон конструктора",
  "UI-компоненты",
  "Проверка данных",
  "Живой предпросмотр",
  "Реестр конструкторов",
  "Движок шаблонов",
  "Расширения",
  "SDK конструктора",
  "Итоги",
  "Создать",
] as const;

export const GENERIC_STEPS = [
  "Определить область",
  "Настроить структуру",
  "Параметры",
  "Проверить сведения",
  "Предпросмотр",
  "Создать",
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
  /** For preview-only frame builders — open the corresponding workspace / operational surface. */
  openWorkspaceRoute?: string;
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
