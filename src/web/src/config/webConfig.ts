export const webConfig = {
  application: "enterprise_web_platform",
  version: "9.0.1",
  sprint: "26.2",
  apiBase: import.meta.env.VITE_API_BASE || "/api",
  hubPrefix: "/api/enterprise-hub/v1",
  ewfPrefix: "/api/enterprise-ewf/v1",
  edsPrefix: "/api/enterprise-eds/v1",
  socketUrl: import.meta.env.VITE_SOCKET_URL || "",
  defaultLocale: "en" as const,
  supportedLocales: ["en", "ru", "uk"] as const,
  multiTenant: true,
  mfaReady: true,
};
