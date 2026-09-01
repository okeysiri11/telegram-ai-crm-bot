/**
 * Sprint Recruiting 2.6 — owner read identity maps to Vanguard ingest org.
 */

import { describe, expect, it } from "vitest";
import {
  VANGUARD_INGEST_ORGANIZATION_ID,
  recruitingReadOrganizationId,
  recruitingWorkspaceHeaders,
} from "./recruitingApi";

describe("Recruiting 2.6 read identity", () => {
  it("maps owner demo-corp / default to the ingest organization", () => {
    expect(recruitingReadOrganizationId("demo-corp", "platform_owner")).toBe(VANGUARD_INGEST_ORGANIZATION_ID);
    expect(recruitingReadOrganizationId("default", "owner")).toBe("ados");
    expect(recruitingReadOrganizationId("ados", "platform_owner")).toBe("ados");
  });

  it("does not remap a recruiter on demo-corp", () => {
    expect(recruitingReadOrganizationId("demo-corp", "recruiter")).toBe("demo-corp");
  });

  it("does not remap an owner on an unrelated tenant", () => {
    expect(recruitingReadOrganizationId("globefly", "platform_owner")).toBe("globefly");
  });

  it("sends recruiting org header and does not put secrets in headers", () => {
    const headers = recruitingWorkspaceHeaders("demo-corp", "platform_owner");
    expect(headers["X-Organization-Id"]).toBe("ados");
    expect(headers["X-Recruiting-Organization-Id"]).toBe("ados");
    expect(headers["X-Role"]).toBe("platform_owner");
    expect(headers["X-Tenant-Id"]).toBeUndefined();
    const blob = JSON.stringify(headers);
    expect(blob).not.toMatch(/IAM_JWT_SECRET|VANGUARD_INGEST_SECRET|API_JWT_SECRET/);
  });
});
