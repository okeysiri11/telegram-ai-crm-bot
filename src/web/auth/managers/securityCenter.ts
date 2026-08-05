/**
 * Owner Security Center snapshot — Sprint 32.4.
 * Extends SecuritySnapshot; identity SoR remains ISAM.
 */

import type { SecuritySnapshot } from "../types";

export type SecurityHealthStatus = "healthy" | "degraded" | "critical";

export type SecurityCenterEvent = {
  id: string;
  type: string;
  at: string;
  severity?: "low" | "medium" | "high" | "critical";
};

function deriveHealth(risk: number, openIncidents: number): SecurityHealthStatus {
  if (risk >= 85 || openIncidents >= 5) return "critical";
  if (risk >= 50 || openIncidents >= 1) return "degraded";
  return "healthy";
}

export const securityCenter = {
  snapshot(): SecuritySnapshot {
    const riskScore = 18;
    const openIncidents = 0;
    const trustScore = Number((1 - riskScore / 100).toFixed(3));
    return {
      mfaStatus: "enabled",
      trustedDevices: 2,
      recentLogins: 5,
      failedAttempts: 1,
      securityEvents: 3,
      passwordAgeDays: 42,
      riskScore,
      trustScore,
      health: deriveHealth(riskScore, openIncidents),
      openIncidents,
      emergencyMode: false,
      zeroTrust: true,
      version: "32.4",
    };
  },
  events(): SecurityCenterEvent[] {
    const now = Date.now();
    return [
      { id: "se1", type: "login_success", at: new Date(now).toISOString(), severity: "low" },
      {
        id: "se2",
        type: "mfa_challenge",
        at: new Date(now - 7_200_000).toISOString(),
        severity: "medium",
      },
      {
        id: "se3",
        type: "failed_login",
        at: new Date(now - 172_800_000).toISOString(),
        severity: "high",
      },
      {
        id: "se4",
        type: "zero_trust_verify",
        at: new Date(now - 60_000).toISOString(),
        severity: "low",
      },
    ];
  },
  capabilities() {
    return {
      zeroTrust: true,
      incidentCenter: true,
      aiSecurity: true,
      antiParsing: true,
      auditCenter: true,
      systemOfRecord: "platform_security.security_center",
    };
  },
};
