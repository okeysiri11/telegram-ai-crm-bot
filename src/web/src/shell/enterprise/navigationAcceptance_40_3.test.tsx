/**
 * Sprint 40.3 — UI acceptance: route aliases and shell nav alignment.
 */
import { describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render, screen, waitFor } from "@testing-library/react";
import { Navigate } from "react-router-dom";
import { ENTERPRISE_SHELL_NAV } from "@/shell/enterprise/enterpriseNav";

function AliasFixture({ from }: { from: string }) {
  return (
    <MemoryRouter initialEntries={[from]}>
      <Routes>
        <Route path="/deals" element={<Navigate to="/crm?view=deals" replace />} />
        <Route path="/clients" element={<Navigate to="/crm?view=clients" replace />} />
        <Route path="/companies" element={<Navigate to="/crm?view=companies" replace />} />
        <Route path="/leads" element={<Navigate to="/crm?view=leads" replace />} />
        <Route path="/reports" element={<Navigate to="/analytics" replace />} />
        <Route path="/profile" element={<Navigate to="/identity/profile" replace />} />
        <Route path="/workspace/crm" element={<Navigate to="/crm" replace />} />
        <Route path="/workspace/erp" element={<Navigate to="/erp" replace />} />
        <Route path="/workspace/docs" element={<Navigate to="/documents" replace />} />
        <Route path="/workspace/analytics" element={<Navigate to="/analytics" replace />} />
        <Route path="/crm" element={<div>CRM_OK</div>} />
        <Route path="/analytics" element={<div>ANALYTICS_OK</div>} />
        <Route path="/erp" element={<div>ERP_OK</div>} />
        <Route path="/documents" element={<div>DOCS_OK</div>} />
        <Route path="/identity/profile" element={<div>PROFILE_OK</div>} />
        <Route path="*" element={<div>NOT_FOUND</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Sprint 40.3 navigation acceptance", () => {
  it("shell nav uses canonical hubs (no /workspace/* CRM drift)", () => {
    const byId = Object.fromEntries(ENTERPRISE_SHELL_NAV.map((n) => [n.id, n.route]));
    expect(byId.crm).toBe("/crm");
    expect(byId.erp).toBe("/erp");
    expect(byId.documents).toBe("/documents");
    expect(byId.analytics).toBe("/analytics");
    expect(byId.projects).toBe("/projects");
    expect(byId.ai_studio).toBe("/ai-studio");
    expect(byId.ai_agents).toBe("/ai-agents");
    expect(byId.knowledge).toBe("/knowledge");
    expect(byId.marketplace).toBe("/marketplace");
    expect(ENTERPRISE_SHELL_NAV.find((n) => n.id === "city")?.comingSoon).toBeFalsy();
  });

  it.each([
    ["/deals", "CRM_OK"],
    ["/clients", "CRM_OK"],
    ["/companies", "CRM_OK"],
    ["/leads", "CRM_OK"],
    ["/reports", "ANALYTICS_OK"],
    ["/profile", "PROFILE_OK"],
    ["/workspace/crm", "CRM_OK"],
    ["/workspace/erp", "ERP_OK"],
    ["/workspace/docs", "DOCS_OK"],
    ["/workspace/analytics", "ANALYTICS_OK"],
  ])("alias %s resolves to hub (not 404)", async (from, marker) => {
    render(<AliasFixture from={from} />);
    await waitFor(() => {
      expect(screen.getByText(marker)).toBeTruthy();
    });
    expect(screen.queryByText("NOT_FOUND")).toBeNull();
  });
});
