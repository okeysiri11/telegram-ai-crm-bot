/**
 * Sprint 30.9 — Tenant guard + sanitization tests.
 */
import { describe, expect, it } from "vitest";
import { assertSameTenant, sanitizeApiErrorMessage, validateTenantContext } from "./tenantGuard";

describe("Sprint 30.9 Tenant / API security helpers", () => {
  it("sanitizes sensitive fragments from API errors", () => {
    const msg = sanitizeApiErrorMessage("Bearer abc.def.ghi failed for user@corp.com sk-ABCDEFGHIJK");
    expect(msg).not.toMatch(/abc\.def/);
    expect(msg).toContain("[redacted]");
    expect(msg).toContain("[email]");
    expect(msg).toContain("[secret]");
  });

  it("validateTenantContext returns structured result", () => {
    const r = validateTenantContext();
    expect(r).toHaveProperty("ok");
    expect(Array.isArray(r.reasons)).toBe(true);
  });

  it("assertSameTenant allows matching tenant", () => {
    expect(() => assertSameTenant(undefined)).not.toThrow();
  });
});
