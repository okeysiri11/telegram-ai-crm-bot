/**
 * Sprint 49.1 — BOS/COS/crypto fetch helpers (GET + POST).
 * MOBILE 1.2: request timeout + upload progress. Relative prefixes stay public-host compatible.
 */

import { webConfig } from "@/config/webConfig";

export const OPS_TIMEOUT_MS = 20_000;

export type OpsResult = { ok: boolean; status: number; json: unknown };
export type UploadProgress = (percent: number) => void;

function timeoutSignal(ms: number): AbortSignal {
  const ctrl = new AbortController();
  const wait = typeof window !== "undefined" ? window.setTimeout : setTimeout;
  wait(() => ctrl.abort(), ms);
  return ctrl.signal;
}

function fail(e: unknown): OpsResult {
  const name = e instanceof DOMException ? e.name : "";
  const msg = name === "AbortError" || name === "TimeoutError" ? "timeout" : e instanceof Error ? e.message : "network_error";
  return { ok: false, status: 0, json: { error: msg, message_ru: msg === "timeout" ? "Превышено время ожидания. Повторите запрос." : "Нет сети. Проверьте соединение." } };
}

async function getJson(url: string): Promise<OpsResult> {
  try {
    const res = await fetch(url, { credentials: "include", signal: timeoutSignal(OPS_TIMEOUT_MS) });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return fail(e);
  }
}

async function postJson(url: string, body: Record<string, unknown>): Promise<OpsResult> {
  try {
    const res = await fetch(url, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: timeoutSignal(OPS_TIMEOUT_MS),
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return fail(e);
  }
}

function uploadWithProgress(
  url: string,
  fd: FormData,
  headers: Record<string, string>,
  onProgress?: UploadProgress,
): Promise<OpsResult> {
  return new Promise((resolve) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    xhr.withCredentials = true;
    xhr.timeout = OPS_TIMEOUT_MS;
    for (const [k, v] of Object.entries(headers)) {
      if (k.toLowerCase() !== "content-type") xhr.setRequestHeader(k, v);
    }
    xhr.upload.onprogress = (ev) => {
      if (ev.lengthComputable && onProgress) onProgress(Math.round((ev.loaded / ev.total) * 100));
    };
    xhr.onload = () => {
      let json: unknown = {};
      try {
        json = JSON.parse(xhr.responseText || "{}");
      } catch {
        json = {};
      }
      resolve({ ok: xhr.status >= 200 && xhr.status < 300, status: xhr.status, json });
    };
    xhr.ontimeout = () => resolve(fail(new DOMException("timeout", "TimeoutError")));
    xhr.onerror = () => resolve(fail(new Error("network_error")));
    xhr.send(fd);
  });
}

export async function bosGet(path: string) {
  return getJson(`${webConfig.beautyOsPrefix}${path}`);
}

export async function bosPost(path: string, body: Record<string, unknown>) {
  return postJson(`${webConfig.beautyOsPrefix}${path}`, body);
}

export async function bosBootstrap() {
  return fetch(`${webConfig.beautyOsPrefix}/bootstrap`, {
    method: "POST",
    credentials: "include",
  });
}

export async function cosGet(path: string) {
  return getJson(`${webConfig.cafeOsPrefix}${path}`);
}

export async function cosPost(path: string, body: Record<string, unknown>) {
  return postJson(`${webConfig.cafeOsPrefix}${path}`, body);
}

export async function cosBootstrap() {
  return fetch(`${webConfig.cafeOsPrefix}/bootstrap`, {
    method: "POST",
    credentials: "include",
  });
}

export async function cryptoEnterpriseGet(path: string) {
  const prefix =
    (webConfig as { cryptoEnterprisePrefix?: string }).cryptoEnterprisePrefix ||
    "/api/crypto-enterprise/v1";
  return getJson(`${prefix}${path}`);
}

export async function cryptoTaPost(path: string, body: Record<string, unknown>) {
  const prefix =
    (webConfig as { cryptoTaPrefix?: string }).cryptoTaPrefix || "/api/crypto-ta/v1";
  return postJson(`${prefix}${path}`, body);
}

export async function cryptoFxIntelGet(path: string) {
  const prefix =
    (webConfig as { cryptoMiPrefix?: string }).cryptoMiPrefix || "/api/crypto-mi/v1";
  return getJson(`${prefix}/fx-intel${path}`);
}

export async function cryptoFxIntelPost(path: string, body: Record<string, unknown> = {}) {
  const prefix =
    (webConfig as { cryptoMiPrefix?: string }).cryptoMiPrefix || "/api/crypto-mi/v1";
  return postJson(`${prefix}/fx-intel${path}`, body);
}

export function agroOpsPrefix(): string {
  return (webConfig as { agroOpsPrefix?: string }).agroOpsPrefix || "/api/agro-ops/v1";
}

export function agroOpsFileUrl(fileId: string): string {
  return `${agroOpsPrefix()}/files/${fileId}/content`;
}

export async function agroOpsGet(path: string, headers: Record<string, string> = {}) {
  const prefix = agroOpsPrefix();
  try {
    const res = await fetch(`${prefix}${path}`, {
      credentials: "include",
      headers: { ...headers },
      signal: timeoutSignal(OPS_TIMEOUT_MS),
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return fail(e);
  }
}

export async function agroOpsBootstrap(headers: Record<string, string> = {}) {
  return agroOpsPost("/bootstrap", {}, headers);
}

export async function agroOpsPost(path: string, body: Record<string, unknown> = {}, headers: Record<string, string> = {}) {
  const prefix = agroOpsPrefix();
  try {
    const res = await fetch(`${prefix}${path}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return { ok: false, status: 0, json: { error: e instanceof Error ? e.message : "network_error" } };
  }
}

export async function agroOpsPut(path: string, body: Record<string, unknown> = {}, headers: Record<string, string> = {}) {
  const prefix = agroOpsPrefix();
  try {
    const res = await fetch(`${prefix}${path}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return { ok: false, status: 0, json: { error: e instanceof Error ? e.message : "network_error" } };
  }
}

export async function agroOpsUpload(
  path: string,
  file: File,
  fields: Record<string, string> = {},
  headers: Record<string, string> = {},
  onProgress?: UploadProgress,
) {
  const prefix = agroOpsPrefix();
  const fd = new FormData();
  fd.append("file", file);
  for (const [k, v] of Object.entries(fields)) fd.append(k, v);
  return uploadWithProgress(`${prefix}${path}`, fd, headers, onProgress);
}

export function legalOpsPrefix(): string {
  return (webConfig as { legalOpsPrefix?: string }).legalOpsPrefix || "/api/legal-ops/v1";
}

export function autoOpsPrefix(): string {
  const origin = (webConfig as { publicApiOrigin?: string }).publicApiOrigin || "";
  const prefix = (webConfig as { autoOpsPrefix?: string }).autoOpsPrefix || "/api/auto-ops/v1";
  if (prefix.startsWith("http")) return prefix;
  return `${origin}${prefix}`;
}

export function autoOpsFileUrl(fileId: string): string {
  return `${autoOpsPrefix()}/files/${fileId}/content`;
}

export async function autoOpsGet(path: string, headers: Record<string, string> = {}) {
  const prefix = autoOpsPrefix();
  try {
    const res = await fetch(`${prefix}${path}`, {
      credentials: "include",
      headers: { ...headers },
      signal: timeoutSignal(OPS_TIMEOUT_MS),
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return fail(e);
  }
}

export async function autoOpsPost(path: string, body: Record<string, unknown> = {}, headers: Record<string, string> = {}) {
  const prefix = autoOpsPrefix();
  try {
    const res = await fetch(`${prefix}${path}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(body),
      signal: timeoutSignal(OPS_TIMEOUT_MS),
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return fail(e);
  }
}

export async function autoOpsDownload(path: string, headers: Record<string, string> = {}) {
  const prefix = autoOpsPrefix();
  try {
    const res = await fetch(`${prefix}${path}`, { credentials: "include", headers: { ...headers } });
    const blob = await res.blob();
    const name = path.includes("kind=") ? `auto-${path.split("kind=")[1].split("&")[0]}.csv` : "auto-export.csv";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
    return { ok: res.ok, status: res.status };
  } catch (e) {
    return { ok: false, status: 0, error: e instanceof Error ? e.message : "network_error" };
  }
}

export async function autoOpsDelete(path: string, headers: Record<string, string> = {}) {
  const prefix = autoOpsPrefix();
  try {
    const res = await fetch(`${prefix}${path}`, {
      method: "DELETE",
      credentials: "include",
      headers: { ...headers },
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return { ok: false, status: 0, json: { error: e instanceof Error ? e.message : "network_error" } };
  }
}

export async function autoOpsUpload(
  path: string,
  file: File,
  fields: Record<string, string> = {},
  headers: Record<string, string> = {},
  onProgress?: UploadProgress,
) {
  const prefix = autoOpsPrefix();
  const fd = new FormData();
  fd.append("file", file);
  for (const [k, v] of Object.entries(fields)) fd.append(k, v);
  return uploadWithProgress(`${prefix}${path}`, fd, headers, onProgress);
}

export function legalOpsFileUrl(fileId: string): string {
  return `${legalOpsPrefix()}/files/${fileId}/content`;
}

export async function legalOpsGet(path: string, headers: Record<string, string> = {}) {
  const prefix = legalOpsPrefix();
  try {
    const res = await fetch(`${prefix}${path}`, {
      credentials: "include",
      headers: { ...headers },
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return {
      ok: false,
      status: 0,
      json: { error: e instanceof Error ? e.message : "network_error" },
    };
  }
}

export async function legalOpsPost(path: string, body: Record<string, unknown> = {}, headers: Record<string, string> = {}) {
  const prefix =
    (webConfig as { legalOpsPrefix?: string }).legalOpsPrefix || "/api/legal-ops/v1";
  try {
    const res = await fetch(`${prefix}${path}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return {
      ok: false,
      status: 0,
      json: { error: e instanceof Error ? e.message : "network_error" },
    };
  }
}

export async function legalOpsUpload(
  path: string,
  file: File,
  fields: Record<string, string> = {},
  headers: Record<string, string> = {},
) {
  const prefix =
    (webConfig as { legalOpsPrefix?: string }).legalOpsPrefix || "/api/legal-ops/v1";
  const fd = new FormData();
  fd.append("file", file);
  for (const [k, v] of Object.entries(fields)) fd.append(k, v);
  try {
    const res = await fetch(`${prefix}${path}`, {
      method: "POST",
      credentials: "include",
      headers: { ...headers },
      body: fd,
    });
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return {
      ok: false,
      status: 0,
      json: { error: e instanceof Error ? e.message : "network_error" },
    };
  }
}

export function asList(json: unknown, keys: string[] = ["items", "data", "results", "customers", "services", "appointments", "employees", "orders", "menu", "tables", "staff", "reservations", "shifts"]): unknown[] {
  if (Array.isArray(json)) return json;
  if (json && typeof json === "object") {
    const o = json as Record<string, unknown>;
    for (const k of keys) {
      if (Array.isArray(o[k])) return o[k] as unknown[];
    }
  }
  return [];
}

export function pick(row: Record<string, unknown>, ...keys: string[]): string {
  for (const k of keys) {
    const v = row[k];
    if (v != null && String(v).trim()) return String(v);
  }
  return "—";
}
