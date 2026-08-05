import { hubIntegrations } from "@/integrations/hub";
import type { MfaExtension, MfaMethod } from "../types";

type MfaRequirement = {
  required?: boolean;
  must_challenge?: boolean;
  user_enabled?: boolean;
  org_required?: boolean;
};

export const mfaCenter = {
  methods: ["totp", "email_code", "backup_codes"] as MfaMethod[],
  extensionsReady: ["fido2", "webauthn", "hardware_security_keys"] as MfaExtension[],
  status: {
    totpEnabled: false,
    emailCodeEnabled: true,
    backupCodesRemaining: 8,
    recoveryReady: true,
  },
  verifyTotp(code: string) {
    return /^\d{6}$/.test(code);
  },
  verifyEmailCode(code: string) {
    return code.length >= 4;
  },
  verifyBackup(code: string) {
    return code.length >= 8;
  },
  recoveryFlow() {
    return { steps: ["verify_email", "choose_new_factor", "confirm"], ready: true };
  },
  async fetchRequirement(identityId: string, organizationId = ""): Promise<MfaRequirement> {
    const q = new URLSearchParams({
      identity_id: identityId,
      organization_id: organizationId,
    });
    const res = await fetch(`${hubIntegrations.authentication}/mfa?${q}`);
    if (!res.ok) return {};
    const body = (await res.json()) as { requirement?: MfaRequirement };
    return body.requirement || {};
  },
  async enable(identityId: string) {
    const res = await fetch(`${hubIntegrations.authentication}/mfa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "enable", identity_id: identityId }),
    });
    if (res.ok) this.status.totpEnabled = true;
    return res.ok;
  },
  async disable(identityId: string) {
    const res = await fetch(`${hubIntegrations.authentication}/mfa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "disable", identity_id: identityId }),
    });
    if (res.ok) this.status.totpEnabled = false;
    return res.ok;
  },
  async setOrgPolicy(organizationId: string, requireMfa: boolean) {
    const res = await fetch(`${hubIntegrations.authentication}/mfa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "org_policy",
        organization_id: organizationId,
        require_mfa: requireMfa,
      }),
    });
    return res.ok;
  },
};
