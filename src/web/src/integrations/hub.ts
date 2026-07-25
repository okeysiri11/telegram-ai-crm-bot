import { webConfig } from "@/config/webConfig";

export const hubIntegrations = {
  enterpriseHub: webConfig.hubPrefix,
  authentication: "/api/enterprise-isam/v1",
  aiOrchestrator: "/api/enterprise-eao/v1",
  workflow: "/api/enterprise-workflow/v1",
  notifications: "/api/enterprise-comms/v1",
  monitoring: "/api/enterprise-obs/v1",
  knowledgeGraph: "/api/enterprise-ekg/v1",
  marketplace: "/api/enterprise-ees/v1",
  webFoundation: webConfig.ewfPrefix,
  designSystem: webConfig.edsPrefix,
} as const;

export async function fetchWebFoundationHealth(): Promise<Record<string, unknown>> {
  const res = await fetch(`${webConfig.ewfPrefix}/health`);
  if (!res.ok) throw new Error("ewf health failed");
  return res.json() as Promise<Record<string, unknown>>;
}

export async function fetchDesignSystemHealth(): Promise<Record<string, unknown>> {
  const res = await fetch(`${webConfig.edsPrefix}/health`);
  if (!res.ok) throw new Error("eds health failed");
  return res.json() as Promise<Record<string, unknown>>;
}
