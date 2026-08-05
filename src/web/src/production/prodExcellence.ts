/**
 * Production excellence helpers — EP-07.
 * Logging, timeouts, visibility — no new Engine / Store.
 */

export const PRODUCTION_EXCELLENCE_VERSION = "1.0";

const isProd = typeof import.meta !== "undefined" && Boolean(import.meta.env?.PROD);

export type ProdLogLevel = "debug" | "info" | "warn" | "error";

/** Structured console logging — debug silenced in production builds. */
export function prodLog(level: ProdLogLevel, code: string, detail?: Record<string, unknown>) {
  if (level === "debug" && isProd) return;
  const payload = {
    svc: "enterprise_web_platform",
    code,
    at: new Date().toISOString(),
    ...(detail || {}),
  };
  const line = `[EWP] ${level.toUpperCase()} ${code}`;
  if (level === "error") console.error(line, payload);
  else if (level === "warn") console.warn(line, payload);
  else if (level === "info") console.info(line, payload);
  else if (!isProd) console.debug(line, payload);
}

/** Default request timeout for API calls (ms). */
export const API_TIMEOUT_MS = 20_000;

/** Shared live fetch soft-dedupe window (ms). */
export const LIVE_FETCH_DEDUPE_MS = 4_000;

/** Live poll interval — longer sessions, fewer background wakes. */
export const LIVE_POLL_MS_PROD = 20_000;

export function withTimeoutSignal(ms = API_TIMEOUT_MS, parent?: AbortSignal): AbortSignal {
  const ctrl = new AbortController();
  const timer = window.setTimeout(() => ctrl.abort(new Error("Request timeout")), ms);
  const onAbort = () => {
    window.clearTimeout(timer);
    ctrl.abort(parent?.reason);
  };
  if (parent) {
    if (parent.aborted) onAbort();
    else parent.addEventListener("abort", onAbort, { once: true });
  }
  ctrl.signal.addEventListener(
    "abort",
    () => {
      window.clearTimeout(timer);
    },
    { once: true },
  );
  return ctrl.signal;
}

export function isDocumentHidden(): boolean {
  return typeof document !== "undefined" && document.hidden;
}

/** User-facing reliability copy — what happened / what to do / what system does. */
export function reliabilityCopy(kind: "offline" | "timeout" | "boundary" | "live_failed") {
  if (kind === "offline") {
    return {
      title: "Connection lost",
      happened: "The browser is offline. Live data may be stale.",
      action: "Reconnect to the network, then retry.",
      auto: "The platform will resume updates automatically when online.",
    };
  }
  if (kind === "timeout") {
    return {
      title: "Request timed out",
      happened: "A service did not respond in time.",
      action: "Retry the action. If it persists, open Mission Control health.",
      auto: "Pending requests were cancelled to protect the session.",
    };
  }
  if (kind === "boundary") {
    return {
      title: "This view failed to render",
      happened: "An unexpected UI error stopped this screen.",
      action: "Try again, or return to Dashboard / Workspace.",
      auto: "The error was logged for diagnostics. Other screens remain available.",
    };
  }
  return {
    title: "Live data unavailable",
    happened: "The shared live snapshot could not refresh.",
    action: "Use Refresh now, or open Mission Control.",
    auto: "The last successful snapshot stays on screen when possible.",
  };
}

export function sanitizeErrorMessage(message: string): string {
  // Avoid leaking tokens / emails in production UI
  let out = message.replace(/Bearer\s+[A-Za-z0-9._-]+/gi, "Bearer [redacted]");
  out = out.replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[redacted-email]");
  if (isProd && out.length > 240) out = `${out.slice(0, 240)}…`;
  return out;
}
