export const webConfig = {
  application: "enterprise_web_platform",
  version: "9.4.0",
  sprint: "30.4",
  apiBase: import.meta.env.VITE_API_BASE || "/api",
  hubPrefix: "/api/enterprise-hub/v1",
  ewfPrefix: "/api/enterprise-ewf/v1",
  edsPrefix: "/api/enterprise-eds/v1",
  eicPrefix: "/api/enterprise-eic/v1",
  ewsPrefix: "/api/enterprise-ews/v1",
  enpPrefix: "/api/enterprise-enp/v1",
  socketUrl: import.meta.env.VITE_SOCKET_URL || "",
  defaultLocale: "en" as const,
  supportedLocales: ["en", "ru", "uk"] as const,
  multiTenant: true,
  mfaReady: true,
  /** Posts to existing Enterprise Observability — disable in offline CI if needed. */
  telemetryEnabled: import.meta.env.VITE_TELEMETRY_ENABLED !== "false",
};
