function publicApiOrigin(): string {
  const raw = String(import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || "").trim();
  if (!raw || raw === "/api") return "";
  if (raw.startsWith("http://") || raw.startsWith("https://")) {
    return raw.replace(/\/$/, "").replace(/\/api$/i, "");
  }
  return "";
}

const PUBLIC_API_ORIGIN = publicApiOrigin();

export const webConfig = {
  application: "enterprise_web_platform",
  version: "9.5.0",
  sprint: "33.2.1",
  n8nUrl: import.meta.env.VITE_N8N_URL || (import.meta.env.PROD ? "" : "http://localhost:5678"),
  litellmUrl: import.meta.env.VITE_LITELLM_URL || (import.meta.env.PROD ? "" : "http://localhost:4000"),
  /** Empty in local/dev and same-origin HTTPS. Absolute origin only when VITE_API_BASE(_URL) is set. */
  publicApiOrigin: PUBLIC_API_ORIGIN,
  apiBase: PUBLIC_API_ORIGIN ? `${PUBLIC_API_ORIGIN}/api` : import.meta.env.VITE_API_BASE || "/api",
  hubPrefix: "/api/enterprise-hub/v1",
  ebnPrefix: "/api/enterprise-ebn/v1",
  edcPrefix: "/api/enterprise-edc/v1",
  lifePrefix: "/api/enterprise-life/v1",
  assetPrefix: "/api/enterprise-assets/v1",
  spatialPrefix: "/api/enterprise-spatial/v1",
  cityVizPrefix: "/api/enterprise-city-viz/v1",
  interactionPrefix: "/api/enterprise-interaction/v1",
  intelligencePrefix: "/api/enterprise-intelligence/v1",
  orchestratorPrefix: "/api/enterprise-orchestrator/v1",
  kernelPrefix: "/api/enterprise-kernel/v1",
  ewfPrefix: "/api/enterprise-ewf/v1",
  edsPrefix: "/api/enterprise-eds/v1",
  eicPrefix: "/api/enterprise-eic/v1",
  ewsPrefix: "/api/enterprise-ews/v1",
  enpPrefix: "/api/enterprise-enp/v1",
  autoPrefix: "/api/auto/v1",
  casinoPrefix: "/api/casino/v1",
  autoOpsPrefix: "/api/auto-ops/v1",
  beautyOsPrefix: "/api/enterprise-bos/v1",
  beautyWorkspacePrefix: "/api/enterprise-bws/v1",
  beautyClientJourneyPrefix: "/api/enterprise-bcj/v1",
  cafeOsPrefix: "/api/enterprise-cos/v1",
  agroPrefix: "/api/agro/v1",
  agroSupplyChainPrefix: "/api/agro-supply-chain/v1",
  agroEnterprisePrefix: "/api/agro-enterprise/v1",
  agroOpsPrefix: "/api/agro-ops/v1",
  agroFinancePrefix: "/api/agro-finance/v1",
  aiAgronomistPrefix: "/api/ai-agronomist/v1",
  legalEnterprisePrefix: "/api/legal-enterprise/v1",
  legalOpsPrefix: "/api/legal-ops/v1",
  legalCasePrefix: "/api/legal-cm/v1",
  legalDocumentsPrefix: "/api/legal-di/v1",
  legalCompliancePrefix: "/api/legal-cp/v1",
  legalAiPrefix: "/api/legal-aa/v1",
  legalExecutivePrefix: "/api/legal-ei/v1",
  financeDigitalAssetsPrefix: "/api/finance-da/v1",
  financePaymentsPrefix: "/api/finance-pay/v1",
  financeTreasuryPrefix: "/api/finance-tr/v1",
  financeIntegrationPrefix: "/api/finance-int/v1",
  financeCfoPrefix: "/api/finance-cfo/v1",
  cryptoEnterprisePrefix: "/api/crypto-enterprise/v1",
  cryptoTaPrefix: "/api/crypto-ta/v1",
  cryptoMiPrefix: "/api/crypto-mi/v1",
  cryptoRiskPrefix: "/api/crypto-rm/v1",
  dronePrefix: "/api/drone/v1",
  precisionAgriculturePrefix: "/api/precision-agriculture/v1",
  aiMarketingOsPrefix: "/api/enterprise-amo/v1",
  commerceCorePrefix: "/api/enterprise-eco/v1",
  commsPrefix: "/api/enterprise-comms/v1",
  platformBuilderPrefix: "/api/platform-builder/v1",
  identityLoginPath: "/management/identity/login",
  identityRefreshPath: "/management/identity/refresh",
  /** Maps owner@* emails to platform IAM telegram id when minting JWT. */
  defaultTelegramId: Number(import.meta.env.VITE_OWNER_TELEGRAM_ID || 1208044579),
  socketUrl: import.meta.env.VITE_SOCKET_URL || "",
  defaultLocale: "ru" as const,
  supportedLocales: ["en", "ru", "uk"] as const,
  multiTenant: true,
  mfaReady: true,
  /**
   * Local Demo Auth when ISAM/IAM are unreachable.
   * Default on in DEV; set VITE_DEMO_AUTH=false to force production-only login.
   */
  demoAuthEnabled:
    import.meta.env.VITE_DEMO_AUTH === "true" ||
    (import.meta.env.DEV && import.meta.env.VITE_DEMO_AUTH !== "false"),
  /** Posts to existing Enterprise Observability — disable in offline CI if needed. */
  telemetryEnabled: import.meta.env.VITE_TELEMETRY_ENABLED !== "false",
};
