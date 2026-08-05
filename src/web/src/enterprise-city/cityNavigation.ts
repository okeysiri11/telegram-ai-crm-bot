/**
 * City navigation memory — Sprint 27.8.
 * History · recent · favorites for buildings.
 * Extends session/local storage only — reuses favoritesManager paths when possible.
 */

import { favoritesManager } from "../../navigation/managers/favoritesManager";
import { getBuilding, type CityBuilding, type CityBuildingId } from "./cityCatalog";
import { getDistrict } from "./cityDistricts";

const HISTORY_KEY = "ews_city_history_v1";
const RECENT_KEY = "ews_city_recent_v1";
const FAV_KEY = "ews_city_favorites_v1";

function readIds(key: string): CityBuildingId[] {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as string[];
    return parsed.filter((id) => !!getBuilding(id as CityBuildingId)) as CityBuildingId[];
  } catch {
    return [];
  }
}

function writeIds(key: string, ids: CityBuildingId[]) {
  try {
    localStorage.setItem(key, JSON.stringify(ids.slice(0, 24)));
  } catch {
    /* ignore */
  }
}

export const cityNavigation = {
  pushHistory(id: CityBuildingId) {
    const next = [id, ...readIds(HISTORY_KEY).filter((x) => x !== id)].slice(0, 24);
    writeIds(HISTORY_KEY, next);
    this.pushRecent(id);
  },

  history(): CityBuildingId[] {
    return readIds(HISTORY_KEY);
  },

  pushRecent(id: CityBuildingId) {
    writeIds(RECENT_KEY, [id, ...readIds(RECENT_KEY).filter((x) => x !== id)].slice(0, 12));
  },

  recent(): CityBuildingId[] {
    return readIds(RECENT_KEY);
  },

  favorites(): CityBuildingId[] {
    return readIds(FAV_KEY);
  },

  isFavorite(id: CityBuildingId): boolean {
    return this.favorites().includes(id);
  },

  toggleFavorite(id: CityBuildingId): boolean {
    const cur = this.favorites();
    const next = cur.includes(id) ? cur.filter((x) => x !== id) : [id, ...cur].slice(0, 20);
    writeIds(FAV_KEY, next);
    const b = getBuilding(id);
    if (b) {
      const favId = `city_${id}`;
      if (next.includes(id)) {
        favoritesManager.add({
          id: favId,
          kind: "page",
          label: `City · ${b.label}`,
          path: b.route,
        });
      } else {
        favoritesManager.remove(favId);
      }
    }
    return next.includes(id);
  },

  breadcrumbs(focus: CityBuilding | null): { label: string; id?: string }[] {
    const crumbs: { label: string; id?: string }[] = [{ label: "Город предприятия" }];
    if (!focus) return crumbs;
    const d = getDistrict(focus.district);
    crumbs.push({ label: d?.labelRu || focus.district, id: `district:${focus.district}` });
    crumbs.push({ label: focus.label, id: focus.id });
    return crumbs;
  },
};
