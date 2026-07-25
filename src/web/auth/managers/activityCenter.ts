import type { ActivityEntry } from "../types";

const entries: ActivityEntry[] = [
  { id: "a1", kind: "login", summary: "Signed in from Chrome / MacBook", at: new Date().toISOString() },
  { id: "a2", kind: "password_change", summary: "Password changed", at: new Date(Date.now() - 86400000 * 10).toISOString() },
  { id: "a3", kind: "mfa_change", summary: "TOTP factor confirmed", at: new Date(Date.now() - 86400000 * 20).toISOString() },
  { id: "a4", kind: "role_change", summary: "Granted Organization Owner", at: new Date(Date.now() - 86400000 * 30).toISOString() },
  { id: "a5", kind: "permission_change", summary: "API Access write enabled", at: new Date(Date.now() - 86400000 * 31).toISOString() },
  { id: "a6", kind: "device", summary: "Trusted device: iPhone", at: new Date(Date.now() - 86400000 * 40).toISOString() },
];

export const activityCenter = {
  list(): ActivityEntry[] {
    return [...entries];
  },
  byKind(kind: ActivityEntry["kind"]) {
    return entries.filter((e) => e.kind === kind);
  },
};
