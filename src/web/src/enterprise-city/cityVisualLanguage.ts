/**
 * Enterprise City visual language — EP-05 / Sprint 27.8.
 * Presentation helpers only. No business Store / Runtime.
 */

import type { CityActivityTone, CityBuilding, CityBuildingId, CityDistrictId, CityLiveStatus } from "./cityCatalog";
import { CITY_BUILDINGS, getBuilding } from "./cityCatalog";
import { CITY_DISTRICTS, streetGraph } from "./cityDistricts";

export const CITY_EXPERIENCE_VERSION = "1.1";

const FOCUS_KEY = "ewp_city_focus_v1";

/** Localized visual states (RU primary; UA twin for legend). City only — Dashboard stays EN. */
export type CityVisualState = "ok" | "attention" | "critical" | "running" | "waiting" | "done";

export const CITY_STATE_LABELS: Record<
  CityVisualState,
  { ru: string; ua: string; enDash: string; css: string }
> = {
  ok: { ru: "Всё хорошо", ua: "Все добре", enDash: "Healthy", css: "ec-state-ok" },
  attention: { ru: "Требует внимания", ua: "Потребує уваги", enDash: "Needs attention", css: "ec-state-attention" },
  critical: { ru: "Критично", ua: "Критично", enDash: "Critical", css: "ec-state-critical" },
  running: { ru: "Выполняется", ua: "Виконується", enDash: "Running", css: "ec-state-running" },
  waiting: { ru: "Ожидает", ua: "Очікує", enDash: "Waiting", css: "ec-state-waiting" },
  done: { ru: "Завершено", ua: "Завершено", enDash: "Done", css: "ec-state-done" },
};

export function resolveVisualState(st: CityLiveStatus): CityVisualState {
  if (st.tone === "alert") return "critical";
  if (st.tone === "busy") return "running";
  if (st.notifications >= 3 || st.tasks >= 5) return "attention";
  if (st.tone === "active") return "running";
  if (st.tone === "idle" && st.tasks > 0) return "waiting";
  if (
    st.tone === "idle" &&
    st.tasks === 0 &&
    st.notifications === 0 &&
    /stable|quiet|idle|done|config|command|guarded|preferences|welcome/i.test(st.processLabel)
  ) {
    return /done|stable|quiet/i.test(st.processLabel) ? "done" : "ok";
  }
  if (st.tone === "idle") return "ok";
  return "ok";
}

export function stateLabelRu(st: CityLiveStatus): string {
  return CITY_STATE_LABELS[resolveVisualState(st)].ru;
}

export function badgeToneForState(state: CityVisualState): "success" | "warning" | "danger" | "default" | "info" {
  if (state === "critical") return "danger";
  if (state === "attention") return "warning";
  if (state === "running") return "info";
  if (state === "done" || state === "ok") return "success";
  return "default";
}

/** Building identity — readable without text (district + silhouette). */
export type BuildingIdentity = {
  districtClass: string;
  silhouette: string;
  purposeRu: string;
  purposeUa: string;
};

const FALLBACK_IDENTITY: BuildingIdentity = {
  districtClass: "ec-district-enterprise",
  silhouette: "ec-sil-hub",
  purposeRu: "Модуль платформы",
  purposeUa: "Модуль платформи",
};

const IDENTITY: Partial<Record<CityBuildingId, BuildingIdentity>> = {
  plaza: {
    districtClass: "ec-district-enterprise",
    silhouette: "ec-sil-hub",
    purposeRu: "Центральная площадь",
    purposeUa: "Центральна площа",
  },
  hub: {
    districtClass: "ec-district-enterprise",
    silhouette: "ec-sil-hub",
    purposeRu: "Центр компании",
    purposeUa: "Центр компанії",
  },
  dashboard: {
    districtClass: "ec-district-enterprise",
    silhouette: "ec-sil-dash",
    purposeRu: "Командный центр",
    purposeUa: "Командний центр",
  },
  crm: {
    districtClass: "ec-district-crm",
    silhouette: "ec-sil-crm",
    purposeRu: "Клиенты и сделки",
    purposeUa: "Клієнти і угоди",
  },
  sales: {
    districtClass: "ec-district-crm",
    silhouette: "ec-sil-sales",
    purposeRu: "Продажи",
    purposeUa: "Продажі",
  },
  marketing: {
    districtClass: "ec-district-marketing",
    silhouette: "ec-sil-mkt",
    purposeRu: "Рост и кампании",
    purposeUa: "Зростання і кампанії",
  },
  erp: {
    districtClass: "ec-district-erp",
    silhouette: "ec-sil-prod",
    purposeRu: "Операции ERP",
    purposeUa: "Операції ERP",
  },
  finance: {
    districtClass: "ec-district-finance",
    silhouette: "ec-sil-fin",
    purposeRu: "Финансы",
    purposeUa: "Фінанси",
  },
  production: {
    districtClass: "ec-district-production",
    silhouette: "ec-sil-prod",
    purposeRu: "AI Production Center",
    purposeUa: "AI Production Center",
  },
  prod_image: {
    districtClass: "ec-district-production",
    silhouette: "ec-sil-docs",
    purposeRu: "Image Studio",
    purposeUa: "Image Studio",
  },
  prod_video: {
    districtClass: "ec-district-production",
    silhouette: "ec-sil-bi",
    purposeRu: "Video Studio",
    purposeUa: "Video Studio",
  },
  prod_reels: {
    districtClass: "ec-district-production",
    silhouette: "ec-sil-sales",
    purposeRu: "Reels Factory",
    purposeUa: "Reels Factory",
  },
  prod_ads: {
    districtClass: "ec-district-production",
    silhouette: "ec-sil-fin",
    purposeRu: "Ads Factory",
    purposeUa: "Ads Factory",
  },
  prod_prompt: {
    districtClass: "ec-district-production",
    silhouette: "ec-sil-concierge",
    purposeRu: "Creative prompts",
    purposeUa: "Creative prompts",
  },
  prod_brand: {
    districtClass: "ec-district-production",
    silhouette: "ec-sil-admin",
    purposeRu: "Brand kit",
    purposeUa: "Brand kit",
  },
  prod_publish: {
    districtClass: "ec-district-production",
    silhouette: "ec-sil-mc",
    purposeRu: "Publishing",
    purposeUa: "Publishing",
  },
  mission_control: {
    districtClass: "ec-district-production",
    silhouette: "ec-sil-mc",
    purposeRu: "Живые операции",
    purposeUa: "Живі операції",
  },
  marketplace: {
    districtClass: "ec-district-marketplace",
    silhouette: "ec-sil-docs",
    purposeRu: "Магазин модулей",
    purposeUa: "Магазин модулів",
  },
  hr: {
    districtClass: "ec-district-enterprise",
    silhouette: "ec-sil-hr",
    purposeRu: "Люди",
    purposeUa: "Люди",
  },
  admin: {
    districtClass: "ec-district-settings",
    silhouette: "ec-sil-admin",
    purposeRu: "Администрирование",
    purposeUa: "Адміністрування",
  },
  settings: {
    districtClass: "ec-district-settings",
    silhouette: "ec-sil-admin",
    purposeRu: "Настройки платформы",
    purposeUa: "Налаштування платформи",
  },
  analytics: {
    districtClass: "ec-district-analytics",
    silhouette: "ec-sil-bi",
    purposeRu: "Аналитика",
    purposeUa: "Аналітика",
  },
  ai_team: {
    districtClass: "ec-district-ai",
    silhouette: "ec-sil-ai",
    purposeRu: "AI-команда",
    purposeUa: "AI-команда",
  },
  ai_studio: {
    districtClass: "ec-district-ai",
    silhouette: "ec-sil-ai",
    purposeRu: "AI Studio",
    purposeUa: "AI Studio",
  },
  knowledge: {
    districtClass: "ec-district-knowledge",
    silhouette: "ec-sil-kb",
    purposeRu: "Знания",
    purposeUa: "Знання",
  },
  documents: {
    districtClass: "ec-district-documents",
    silhouette: "ec-sil-docs",
    purposeRu: "Документы",
    purposeUa: "Документи",
  },
  warehouse: {
    districtClass: "ec-district-warehouse",
    silhouette: "ec-sil-prod",
    purposeRu: "Склад и поставки",
    purposeUa: "Склад і постачання",
  },
  legal: {
    districtClass: "ec-district-legal",
    silhouette: "ec-sil-admin",
    purposeRu: "Юридический контур",
    purposeUa: "Юридичний контур",
  },
  concierge: {
    districtClass: "ec-district-ai",
    silhouette: "ec-sil-concierge",
    purposeRu: "Executive Advisor",
    purposeUa: "Executive Advisor",
  },
  developer: {
    districtClass: "ec-district-developer",
    silhouette: "ec-sil-mc",
    purposeRu: "Инструменты разработчика",
    purposeUa: "Інструменти розробника",
  },
  security: {
    districtClass: "ec-district-security",
    silhouette: "ec-sil-admin",
    purposeRu: "Безопасность",
    purposeUa: "Безпека",
  },
};

export function buildingIdentity(id: CityBuildingId): BuildingIdentity {
  return IDENTITY[id] || FALLBACK_IDENTITY;
}

export const DISTRICT_LABELS_RU: Record<CityDistrictId, string> = Object.fromEntries(
  CITY_DISTRICTS.map((d) => [d.id, d.labelRu]),
) as Record<CityDistrictId, string>;

/** Soft links — streets from district graph (Sprint 27.8). */
export function districtLinks(): { from: CityBuildingId; to: CityBuildingId }[] {
  return streetGraph();
}

export function setCityFocus(id: CityBuildingId | null) {
  try {
    if (!id) sessionStorage.removeItem(FOCUS_KEY);
    else sessionStorage.setItem(FOCUS_KEY, id);
  } catch {
    /* ignore */
  }
}

export function getCityFocus(): CityBuildingId | null {
  try {
    const v = sessionStorage.getItem(FOCUS_KEY);
    if (!v) return null;
    return getBuilding(v as CityBuildingId) ? (v as CityBuildingId) : null;
  } catch {
    return null;
  }
}

/** Executive glance counts from live status map. */
export function cityGlance(statusById: Record<CityBuildingId, CityLiveStatus>) {
  let ok = 0;
  let attention = 0;
  let critical = 0;
  let running = 0;
  let ai = 0;
  for (const id of Object.keys(statusById) as CityBuildingId[]) {
    const st = statusById[id];
    if (!st) continue;
    const vs = resolveVisualState(st);
    if (vs === "critical") critical++;
    else if (vs === "attention") attention++;
    else if (vs === "running") running++;
    else ok++;
    if (st.aiActive) ai++;
  }
  return { ok, attention, critical, running, ai, total: CITY_BUILDINGS.length };
}

export function advisorHintForBuilding(
  id: CityBuildingId,
  st: CityLiveStatus,
): { observation: string; why: string; action: string; impact: string; route: string; assistant: string } {
  const b = getBuilding(id)!;
  const state = resolveVisualState(st);
  const label = CITY_STATE_LABELS[state].ru;
  return {
    observation: `${b.label}: ${label}.`,
    why: buildingIdentity(id).purposeRu,
    action: `Открыть ${b.short}`,
    impact: state === "critical" || state === "attention" ? "Снять риск по контуру" : "Углубить контекст владельца",
    route: b.route,
    assistant: b.aiAssistant || "City Concierge",
  };
}

export function toneToLegacyCss(tone: CityActivityTone): string {
  return `ec-tone-${tone}`;
}

/** @deprecated alias — prefer CityDistrictId labels */
export type CityBuildingDistrict = CityBuilding["district"];
