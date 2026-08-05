/**
 * Sprint 30.8 — Tenant-scoped client persistence (reuse marketplace install pattern).
 * Not a parallel DB — workspace cache when APIs are unreachable.
 */

import { getIdentityContext } from "@/integrations/apiClient";

export function businessStorageKey(domain: string): string {
  const ctx = getIdentityContext();
  const tenant = ctx.tenantId || ctx.organization || "local";
  return `ewp_biz_${domain}_${tenant}_v1`;
}

export function loadJson<T>(domain: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(businessStorageKey(domain));
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function saveJson<T>(domain: string, value: T): void {
  try {
    localStorage.setItem(businessStorageKey(domain), JSON.stringify(value));
  } catch {
    /* quota */
  }
}

export function newId(prefix: string): string {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}
