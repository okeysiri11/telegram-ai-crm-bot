/**
 * Safe post-login return path. Only internal app routes; no open redirects.
 */

const STORAGE_KEY = "ados_return_to";

const BLOCKED_EXACT = new Set(["/login", "/logout", "/auth/logout", "/auth/register", "/auth/forgot-password"]);
const BLOCKED_PREFIXES = ["/login?", "/login#"];

export function sanitizeReturnTo(raw: string | null | undefined): string | null {
  if (!raw || typeof raw !== "string") return null;
  let value = raw.trim();
  try {
    value = decodeURIComponent(value);
  } catch {
    return null;
  }
  value = value.trim();
  if (value.length === 0 || value.length > 512) return null;
  if (!value.startsWith("/")) return null;
  if (value.startsWith("//")) return null;
  if (value.includes("\\")) return null;
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(value)) return null;
  if (/[\n\r\t]/.test(value)) return null;
  const pathOnly = value.split("?")[0].split("#")[0];
  if (BLOCKED_EXACT.has(pathOnly)) return null;
  if (BLOCKED_PREFIXES.some((prefix) => value.startsWith(prefix) || pathOnly.startsWith("/login"))) return null;
  return value;
}

export function rememberReturnTo(path: string): void {
  const safe = sanitizeReturnTo(path);
  if (!safe) return;
  try {
    sessionStorage.setItem(STORAGE_KEY, safe);
  } catch {
    /* ignore */
  }
}

export function consumeReturnTo(): string | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    sessionStorage.removeItem(STORAGE_KEY);
    return sanitizeReturnTo(raw);
  } catch {
    return null;
  }
}

export function loginRedirect(returnTo: string): string {
  const safe = sanitizeReturnTo(returnTo) || "/casino";
  return `/login?returnTo=${encodeURIComponent(safe)}`;
}

export function resolvePostLoginPath(input: {
  queryReturnTo?: string | null;
  stateFrom?: string | null;
  roleHome: string;
}): string {
  const safe =
    sanitizeReturnTo(input.queryReturnTo) ||
    sanitizeReturnTo(input.stateFrom) ||
    consumeReturnTo();
  return safe || input.roleHome || "/dashboard";
}
