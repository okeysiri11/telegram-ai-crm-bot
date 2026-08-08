/** Universal Builder Framework catalog — Sprint 42.5 RU. */

export const UBF_STEPS = [
  "Универсальный шаблон конструктора",
  "Универсальные UI-компоненты",
  "Каркас проверки",
  "Движок живого предпросмотра",
  "Реестр конструкторов",
  "Движок шаблонов",
  "Система расширений",
  "SDK конструктора",
  "Итоги",
  "Создать",
] as const;

export const LIFECYCLE = [
  "Инициализация",
  "Настройка",
  "Проверка",
  "Предпросмотр",
  "Итоги",
  "Создать",
  "Зарегистрировать",
  "Завершить",
] as const;

export const UI_COMPONENTS = [
  "Мастер",
  "Карточки",
  "Формы",
  "Индикатор прогресса",
  "Шаги",
  "Окно предпросмотра",
  "Экран итогов",
  "Подтверждение",
  "Проверка в реальном времени",
  "Анимации",
] as const;

export const VALIDATION_RULES = [
  { id: "required_fields", name: "Обязательные поля" },
  { id: "duplicate_detection", name: "Поиск дубликатов" },
  { id: "registry_validation", name: "Проверка реестра" },
  { id: "dependency_validation", name: "Проверка зависимостей" },
  { id: "knowledge_validation", name: "Проверка базы знаний" },
  { id: "relationship_validation", name: "Проверка связей" },
  { id: "live_error_detection", name: "Живое обнаружение ошибок" },
  { id: "suggestion_engine", name: "Движок подсказок" },
] as const;

export const PREVIEW_CAPABILITIES = [
  "Мгновенный предпросмотр",
  "Живое обновление",
  "Проверка в реальном времени",
  "Визуальные итоги",
] as const;

export const TARGET_BUILDERS = [
  "Конструктор AI",
  "Конструктор AI Консьержа",
  "Конструктор вертикалей",
  "Конструктор сценариев",
  "Конструктор CRM",
  "Конструктор ERP",
  "Конструктор базы знаний",
  "Конструктор магазина решений",
  "Конструктор панелей",
  "Конструктор автоматизации",
  "Конструктор документов",
  "Конструктор отделов",
  "Конструктор пользователей",
  "Будущие конструкторы",
] as const;

export const EXTENSION_TYPES = [
  "Плагины",
  "Свои шаги",
  "Своя проверка",
  "Свои компоненты",
  "Будущие расширения магазина",
] as const;

export type UbfDraft = {
  name: string;
  builderType: string;
  version: string;
  components: string[];
  validationRules: string[];
  saveAsTemplate: boolean;
  extensions: string[];
};

export function emptyUbfDraft(): UbfDraft {
  return {
    name: "",
    builderType: "",
    version: "1.0.0",
    components: [],
    validationRules: [],
    saveAsTemplate: true,
    extensions: [],
  };
}
