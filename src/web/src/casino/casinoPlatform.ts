/**
 * Odessa Prime Casino — platform entry constants.
 * Canonical route is /casino. Search, nav, City, and URL must share this path.
 * No second casino implementation.
 */

import type { SearchDocument } from "../../navigation/types";

export const CASINO_CANONICAL_ROUTE = "/casino";
export const CASINO_NAV_ID = "vert_casino";
export const CASINO_SEARCH_ID = "idx_casino_odessa_prime";
export const CASINO_MODULE_ID = "casino";

export const CASINO_SEARCH_DOC: SearchDocument = {
  id: CASINO_SEARCH_ID,
  category: "applications",
  title: "Odessa Prime Casino",
  path: CASINO_CANONICAL_ROUTE,
  tokens: [
    "casino",
    "казино",
    "odessa",
    "prime",
    "entertainment",
    "roulette",
    "lobby",
    "play",
    "chips",
    "open",
    "available",
  ],
  rankBoost: 14,
  kind: "Casino / Entertainment",
  status: "AVAILABLE",
  action: "Open",
};

export function isCasinoSearchDuplicate(doc: { id?: string; title?: string; path?: string }): boolean {
  if (doc.id === CASINO_SEARCH_ID) return false;
  const title = String(doc.title || "").toLowerCase();
  const path = String(doc.path || "");
  if (path === "/casino/venues/odessa-prime" || path.startsWith("/casino/venues/")) return true;
  if (doc.id === "idx_casino_lobby" || doc.id === "city_casino" || doc.id === "hub_city_casino") return true;
  if (title === "casino lobby") return true;
  if (title.includes("odessa prime casino") && path !== CASINO_CANONICAL_ROUTE) return true;
  if (title.includes("city · odessa prime") || title.includes("odessa prime casino · enterprise city")) return true;
  return false;
}

export function collapseCasinoSearchHits<T extends { id?: string; title?: string; path?: string }>(hits: T[]): T[] {
  const canonical = hits.find((h) => h.id === CASINO_SEARCH_ID);
  const out: T[] = [];
  let injected = false;
  for (const hit of hits) {
    const isCanonical = hit.id === CASINO_SEARCH_ID || (hit.title === "Odessa Prime Casino" && hit.path === CASINO_CANONICAL_ROUTE);
    if (isCanonical) {
      if (!injected) {
        out.push(canonical || hit);
        injected = true;
      }
      continue;
    }
    if (isCasinoSearchDuplicate(hit)) continue;
    out.push(hit);
  }
  return out;
}
