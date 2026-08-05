/**
 * City Districts + Plaza + Street graph — Sprint 27.8 / 30.4.
 * Presentation metadata only; routes come from cityCatalog.
 */

import {
  CITY_BUILDINGS,
  type CityBuilding,
  type CityBuildingId,
  type CityDistrictId,
} from "./cityCatalog";

export type CityDistrictMeta = {
  id: CityDistrictId;
  label: string;
  labelRu: string;
  /** Approximate district centroid for labels / pan */
  x: number;
  y: number;
  /** Soft region tint class */
  css: string;
};

/** Sprint 30.4 — full Beta district set (Russian labels for UI). */
export const CITY_DISTRICTS: CityDistrictMeta[] = [
  { id: "settings", label: "Administration", labelRu: "Администрация", x: 76, y: 88, css: "ec-district-settings" },
  { id: "crm", label: "CRM", labelRu: "CRM", x: 16, y: 22, css: "ec-district-crm" },
  { id: "erp", label: "ERP", labelRu: "ERP", x: 28, y: 40, css: "ec-district-erp" },
  { id: "finance", label: "Finance", labelRu: "Финансы", x: 30, y: 58, css: "ec-district-finance" },
  { id: "production", label: "Production Studio", labelRu: "Продакшн-студия", x: 18, y: 72, css: "ec-district-production" },
  { id: "warehouse", label: "Warehouse", labelRu: "Склад", x: 38, y: 48, css: "ec-district-warehouse" },
  { id: "legal", label: "Legal", labelRu: "Юридический отдел", x: 58, y: 88, css: "ec-district-legal" },
  { id: "marketing", label: "Marketing", labelRu: "Маркетинг", x: 8, y: 54, css: "ec-district-marketing" },
  { id: "ai", label: "AI Center", labelRu: "AI-центр", x: 76, y: 28, css: "ec-district-ai" },
  { id: "security", label: "Security Center", labelRu: "Центр безопасности", x: 84, y: 72, css: "ec-district-security" },
  { id: "analytics", label: "Analytics", labelRu: "Аналитика", x: 66, y: 14, css: "ec-district-analytics" },
  { id: "documents", label: "Documents", labelRu: "Документы", x: 88, y: 48, css: "ec-district-documents" },
  { id: "marketplace", label: "Marketplace", labelRu: "Маркетплейс", x: 42, y: 72, css: "ec-district-marketplace" },
  { id: "knowledge", label: "Knowledge Center", labelRu: "Центр знаний", x: 72, y: 54, css: "ec-district-knowledge" },
  { id: "developer", label: "Developer Zone", labelRu: "Зона разработчика", x: 70, y: 72, css: "ec-district-developer" },
  { id: "enterprise", label: "Production", labelRu: "Производство", x: 48, y: 32, css: "ec-district-enterprise" },
];

export function getDistrict(id: CityDistrictId): CityDistrictMeta | undefined {
  return CITY_DISTRICTS.find((d) => d.id === id);
}

/** Sprint 30.6 — primary building opened when entering a district from the map. */
export const DISTRICT_PRIMARY_BUILDING: Partial<Record<CityDistrictId, CityBuildingId>> = {
  settings: "admin",
  crm: "crm",
  erp: "erp",
  finance: "finance",
  enterprise: "hub",
  warehouse: "warehouse",
  legal: "legal",
  marketing: "marketing",
  ai: "ai_team",
  security: "security",
  analytics: "analytics",
  documents: "documents",
  marketplace: "marketplace",
  production: "production",
  knowledge: "knowledge",
  developer: "developer",
};

export function primaryBuildingForDistrict(id: CityDistrictId): CityBuilding | undefined {
  const preferred = DISTRICT_PRIMARY_BUILDING[id];
  if (preferred) {
    const hit = CITY_BUILDINGS.find((b) => b.id === preferred);
    if (hit) return hit;
  }
  return CITY_BUILDINGS.find((b) => b.district === id);
}

export function districtForBuilding(b: CityBuilding): CityDistrictMeta {
  return getDistrict(b.district) || CITY_DISTRICTS[0]!;
}

/** Plaza is the central gathering building. */
export function getPlaza(): CityBuilding | undefined {
  return CITY_BUILDINGS.find((b) => b.kind === "plaza" || b.id === "plaza");
}

/**
 * Street navigation edges — connect plaza to district hubs + intra-district.
 */
export function streetGraph(): { from: CityBuildingId; to: CityBuildingId }[] {
  const plaza = getPlaza();
  const hubs: CityBuildingId[] = [
    "hub",
    "crm",
    "erp",
    "ai_team",
    "production",
    "marketplace",
    "analytics",
    "knowledge",
    "finance",
    "developer",
    "security",
    "settings",
    "warehouse",
    "legal",
    "marketing",
    "documents",
  ];
  const links: { from: CityBuildingId; to: CityBuildingId }[] = [];
  if (plaza) {
    for (const id of hubs) {
      if (CITY_BUILDINGS.some((b) => b.id === id)) {
        links.push({ from: plaza.id, to: id });
      }
    }
  }
  const byDistrict = new Map<string, CityBuilding[]>();
  for (const b of CITY_BUILDINGS) {
    if (b.kind === "plaza") continue;
    const list = byDistrict.get(b.district) || [];
    list.push(b);
    byDistrict.set(b.district, list);
  }
  for (const list of byDistrict.values()) {
    const sorted = [...list].sort((a, b) => a.x - b.x || a.y - b.y);
    for (let i = 0; i < sorted.length - 1; i++) {
      links.push({ from: sorted[i]!.id, to: sorted[i + 1]!.id });
    }
  }
  return links;
}
