/** Enterprise Integration Hub — Sprint 33.1 / 31.2 deepen. */
export {
  ALL_INTEGRATIONS,
  COMMUNICATION_INTEGRATIONS,
  BUSINESS_INTEGRATIONS,
  DEVELOPER_INTEGRATIONS,
  INTEGRATION_CATEGORIES,
  getIntegration,
  integrationsByCategory,
} from "./integrationCatalog";
export type { IntegrationDef, IntegrationCategory, IntegrationStatus } from "./integrationCatalog";
export {
  connectIntegration,
  syncIntegration,
  resolveStatus,
  listConnections,
  getConnection,
} from "./connectionState";
export { deriveIntegrationHub } from "./deriveIntegrations";
export type { IntegrationHubBundle, IntegrationMonitorRow } from "./deriveIntegrations";
export { EnterpriseIntegrationHubPage } from "./EnterpriseIntegrationHubPage";
export { IntegrationHubStrip } from "./IntegrationHubStrip";
export {
  PROVIDER_REGISTRY,
  PROVIDER_REGISTRY_META,
  providersByCategory,
  getProvider,
  aiFailoverChain,
  estimateCostUsd,
} from "./providerRegistry";
export type { ProviderEntry, ProviderCategory } from "./providerRegistry";
export {
  WORKFLOW_LIBRARY,
  listWorkflowTemplates,
  launchN8nWorkflow,
  listN8nExecutions,
  n8nMonitorSnapshot,
  N8N_UI,
} from "./n8nBridge";
export { ProductionProviderStrip } from "./ProductionProviderStrip";
