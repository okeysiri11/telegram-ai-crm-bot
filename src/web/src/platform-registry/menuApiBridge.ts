/**
 * Sprint 35.1 — Web Menu API Bridge.
 * Fetches navigation from Platform Registry HTTP API.
 * Falls back to static PLATFORM_MENU_CATALOG projection (never a second SoR).
 */

import { webConfig } from "@/config/webConfig";
import type { ExperienceMode } from "@/ux-revolution/experienceModeStore";
import type { IntelligentNavGroup } from "@/ux-revolution/intelligentNavGroups";
import { groupsFromPlatformRegistry, type PlatformMenuItem } from "./menuCatalog";

type RegistryNavResponse = {
  success?: boolean;
  data?: {
    items?: Array<Record<string, unknown>>;
    groups?: Array<Record<string, unknown>>;
  };
};

let cachedGroups: IntelligentNavGroup[] | null = null;
let cacheKey = "";
let inflight: Promise<IntelligentNavGroup[] | null> | null = null;

function mapApiItemsToCatalog(items: Array<Record<string, unknown>>): PlatformMenuItem[] {
  return items.map((raw) => ({
    id: String(raw.id ?? ""),
    title: String(raw.title ?? raw.label ?? raw.id ?? ""),
    titleEn: raw.title_en ? String(raw.title_en) : undefined,
    icon: String(raw.icon ?? "dashboard"),
    route: String(raw.route ?? "/"),
    telegramCommand: raw.telegram_command != null ? String(raw.telegram_command) : null,
    requiredPermissions: Array.isArray(raw.required_permissions)
      ? (raw.required_permissions as string[])
      : undefined,
    requiredRoles: Array.isArray(raw.required_roles) ? (raw.required_roles as string[]) : undefined,
    group: (String(raw.group ?? "workspace") as PlatformMenuItem["group"]),
    simple: Boolean(raw.simple),
    ownerOnly: Boolean(raw.owner_only ?? raw.ownerOnly),
  }));
}

function groupsFromItems(
  items: PlatformMenuItem[],
  mode: ExperienceMode,
  opts?: { owner?: boolean },
): IntelligentNavGroup[] {
  // Temporarily reuse grouping logic by shadowing catalog through a local rebuild
  const owner = opts?.owner ?? false;
  const buckets = new Map<string, PlatformMenuItem[]>();
  for (const item of items) {
    if (item.ownerOnly && !owner) continue;
    const g = item.group === "verticals" ? "business" : item.group;
    if (!buckets.has(g)) buckets.set(g, []);
    buckets.get(g)!.push(item);
  }
  // Delegate to static helper with identical shape by constructing via fallback path
  // when API items empty — otherwise synthesize using groupsFromPlatformRegistry filters:
  return groupsFromPlatformRegistry(mode, opts).map((group) => {
    const apiItems = buckets.get(group.id) || [];
    if (!apiItems.length) return group;
    return {
      ...group,
      items: apiItems
        .filter((i) => (mode === "simple" && !owner ? i.simple : true))
        .map((m) => ({
          id: m.id,
          label: m.title,
          route: m.route,
          icon: m.icon as IntelligentNavGroup["icon"],
          simple: Boolean(m.simple),
        })),
    };
  }).filter((g) => g.items.length > 0);
}

/** Fetch registry navigation; returns null on failure (caller uses fallback). */
export async function fetchRegistryNavigationGroups(
  mode: ExperienceMode,
  opts?: { owner?: boolean; roles?: string[]; token?: string },
): Promise<IntelligentNavGroup[] | null> {
  const owner = opts?.owner ?? false;
  const key = `${mode}:${owner}:${(opts?.roles || []).join(",")}`;
  if (cachedGroups && cacheKey === key) return cachedGroups;
  if (inflight) return inflight;

  inflight = (async () => {
    try {
      const roles = (opts?.roles || []).join(",");
      const qs = new URLSearchParams({
        client: "web",
        owner: owner ? "1" : "0",
        simple: mode === "simple" ? "1" : "0",
      });
      if (roles) qs.set("roles", roles);
      const base = webConfig.apiBase.replace(/\/$/, "");
      const url = `${base}/management/v1/platform-registry/navigation?${qs.toString()}`;
      const headers: Record<string, string> = { Accept: "application/json" };
      if (opts?.token) headers.Authorization = `Bearer ${opts.token}`;
      const res = await fetch(url, { headers });
      if (!res.ok) return null;
      const body = (await res.json()) as RegistryNavResponse;
      const items = body?.data?.items;
      if (!Array.isArray(items) || items.length === 0) return null;
      const catalog = mapApiItemsToCatalog(items).filter((i) => i.id);
      const groups = groupsFromItems(catalog, mode, { owner });
      cachedGroups = groups;
      cacheKey = key;
      return groups;
    } catch {
      return null;
    } finally {
      inflight = null;
    }
  })();

  return inflight;
}

/** Sync entry: prefer API cache, else static projection fallback. */
export function groupsForModeWithBridge(
  mode: ExperienceMode,
  opts?: { owner?: boolean },
): IntelligentNavGroup[] {
  const owner = opts?.owner ?? false;
  const key = `${mode}:${owner}:`;
  if (cachedGroups && cacheKey.startsWith(`${mode}:${owner}`)) {
    return cachedGroups;
  }
  return groupsFromPlatformRegistry(mode, opts);
}

export function prefetchRegistryNavigation(
  mode: ExperienceMode,
  opts?: { owner?: boolean; roles?: string[]; token?: string },
): void {
  void fetchRegistryNavigationGroups(mode, opts);
}

export const WEB_MENU_API_BRIDGE_SPRINT = "35.1";
