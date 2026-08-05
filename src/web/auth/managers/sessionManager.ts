import { hubIntegrations } from "@/integrations/hub";
import type { LoginHistoryEntry, SessionRecord } from "../types";

let sessions: SessionRecord[] = [
  {
    sessionId: "ses_current",
    device: "MacBook Pro",
    browser: "Chrome",
    ipAddress: "10.0.0.12",
    lastActivity: new Date().toISOString(),
    current: true,
  },
  {
    sessionId: "ses_mobile",
    device: "iPhone",
    browser: "Safari",
    ipAddress: "10.0.0.44",
    lastActivity: new Date(Date.now() - 3600000).toISOString(),
    current: false,
  },
];

const history: LoginHistoryEntry[] = [
  { id: "lh1", at: new Date().toISOString(), ipAddress: "10.0.0.12", success: true, method: "password+mfa" },
  { id: "lh2", at: new Date(Date.now() - 86400000).toISOString(), ipAddress: "10.0.0.44", success: true, method: "password" },
  { id: "lh3", at: new Date(Date.now() - 172800000).toISOString(), ipAddress: "203.0.113.9", success: false, method: "password" },
];

function mapRemote(raw: Record<string, unknown>): SessionRecord {
  return {
    sessionId: String(raw.session_id || raw.sessionId || ""),
    device: String(raw.device || "device"),
    browser: String(raw.browser || ""),
    ipAddress: String(raw.ip || raw.ipAddress || ""),
    lastActivity: String(raw.last_activity || raw.at || new Date().toISOString()),
    current: Boolean(raw.current),
  };
}

export const sessionManager = {
  activeSessions(): SessionRecord[] {
    return [...sessions];
  },
  loginHistory(): LoginHistoryEntry[] {
    return [...history];
  },
  logoutCurrent() {
    sessions = sessions.filter((s) => !s.current);
  },
  logoutAll() {
    sessions = [];
  },
  revoke(sessionId: string) {
    sessions = sessions.filter((s) => s.sessionId !== sessionId);
  },
  async syncFromIsam(identityId: string) {
    if (!identityId) return sessions;
    const res = await fetch(
      `${hubIntegrations.authentication}/sessions?identity_id=${encodeURIComponent(identityId)}`,
    );
    if (!res.ok) return sessions;
    const body = (await res.json()) as { sessions?: Record<string, unknown>[] } | Record<string, unknown>[];
    const list = Array.isArray(body) ? body : body.sessions || [];
    if (list.length) {
      sessions = list.map((s) => mapRemote(s as Record<string, unknown>));
    }
    return sessions;
  },
  async terminateAllRemote(identityId: string) {
    const res = await fetch(`${hubIntegrations.authentication}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "terminate_all", identity_id: identityId }),
    });
    if (res.ok) sessions = [];
    return res.ok;
  },
  async trustRemote(sessionId: string, trusted = true) {
    const res = await fetch(`${hubIntegrations.authentication}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "trust", session_id: sessionId, trusted }),
    });
    return res.ok;
  },
};
