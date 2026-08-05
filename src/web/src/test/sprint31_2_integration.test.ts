/**
 * Sprint 31.2 — Integration Hub / n8n / providers (web track).
 * Naming note: Legal Pilot also uses 31.2.
 */
import { describe, expect, it } from "vitest";
import { webConfig } from "@/config/webConfig";
import {
  PROVIDER_REGISTRY,
  PROVIDER_REGISTRY_META,
  aiFailoverChain,
  estimateCostUsd,
  providersByCategory,
} from "@/enterprise-integrations/providerRegistry";
import {
  WORKFLOW_LIBRARY,
  launchN8nWorkflow,
  completeN8nExecution,
  listN8nExecutions,
  n8nMonitorSnapshot,
  N8N_UI,
} from "@/enterprise-integrations/n8nBridge";
import { DEVELOPER_INTEGRATIONS, getIntegration } from "@/enterprise-integrations/integrationCatalog";
import { hubIntegrations } from "@/integrations/hub";

describe("Sprint 31.2 Integration Hub & Providers", () => {
  it("web sprint is at least 31.2 integration track", () => {
    expect(Number.parseFloat(webConfig.sprint)).toBeGreaterThanOrEqual(31.2);
    expect(webConfig.n8nUrl).toContain("5678");
  });

  it("provider registry covers AI image video audio automation crm storage payments", () => {
    expect(PROVIDER_REGISTRY.length).toBeGreaterThanOrEqual(50);
    for (const cat of ["ai", "image", "video", "audio", "automation", "crm", "storage", "payments", "observability"] as const) {
      expect(providersByCategory(cat).length).toBeGreaterThan(0);
    }
    const aiIds = providersByCategory("ai").map((p) => p.id);
    for (const id of ["openai", "anthropic", "google_gemini", "openrouter", "deepseek", "mistral", "groq", "xai", "ollama", "litellm"]) {
      expect(aiIds).toContain(id);
    }
    expect(PROVIDER_REGISTRY_META.systemOfRecord).toBe("platform_runtime");
    expect(PROVIDER_REGISTRY_META.externalOrchestrator).toBe("n8n");
    expect(aiFailoverChain()[0].id).toBe("litellm");
    expect(estimateCostUsd("openai", 1000)).toBeCloseTo(0.15);
  });

  it("n8n workflow library launch and callback settle", () => {
    expect(WORKFLOW_LIBRARY.length).toBeGreaterThanOrEqual(3);
    const ex = launchN8nWorkflow("n8n_tpl_media_pipeline");
    expect(ex.status).toBe("running");
    const done = completeN8nExecution(ex.id, "success");
    expect(done?.status).toBe("success");
    expect(listN8nExecutions().some((e) => e.id === ex.id)).toBe(true);
    const mon = n8nMonitorSnapshot();
    expect(mon.businessLogicInN8n).toBe(false);
    expect(mon.systemOfRecord).toBe("platform_runtime");
    expect(N8N_UI.callbackPath).toContain("n8n");
  });

  it("catalog includes n8n and APH developer cards", () => {
    expect(getIntegration("n8n")?.title).toBe("n8n");
    expect(DEVELOPER_INTEGRATIONS.some((d) => d.id === "ai_providers")).toBe(true);
    expect(hubIntegrations.aiProviderHub).toContain("aph");
    expect(hubIntegrations.n8nBridge).toContain("n8n");
  });

  it("exports ProductionProviderStrip and Integration Hub page", async () => {
    expect(
      typeof (await import("@/enterprise-integrations/ProductionProviderStrip")).ProductionProviderStrip,
    ).toBe("function");
    expect(
      typeof (await import("@/enterprise-integrations/EnterpriseIntegrationHubPage"))
        .EnterpriseIntegrationHubPage,
    ).toBe("function");
  }, 20_000);
});
