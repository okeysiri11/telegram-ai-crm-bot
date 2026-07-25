import type { MfaExtension, MfaMethod } from "../types";

export const mfaCenter = {
  methods: ["totp", "email_code", "backup_codes"] as MfaMethod[],
  extensionsReady: ["fido2", "webauthn", "hardware_security_keys"] as MfaExtension[],
  status: {
    totpEnabled: true,
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
};
