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
};
