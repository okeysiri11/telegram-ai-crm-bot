import type { SecuritySnapshot } from "../types";

export const securityCenter = {
  snapshot(): SecuritySnapshot {
    return {
      mfaStatus: "enabled",
      trustedDevices: 2,
      recentLogins: 5,
      failedAttempts: 1,
      securityEvents: 3,
      passwordAgeDays: 42,
      riskScore: 18,
    };
  },
  events() {
    return [
      { id: "se1", type: "login_success", at: new Date().toISOString() },
      { id: "se2", type: "mfa_challenge", at: new Date(Date.now() - 7200000).toISOString() },
      { id: "se3", type: "failed_login", at: new Date(Date.now() - 172800000).toISOString() },
    ];
  },
};
