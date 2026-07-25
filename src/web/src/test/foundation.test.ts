import { describe, expect, it } from "vitest";
import { webConfig } from "@/config/webConfig";
import { messages } from "@/i18n/messages";
import { hubIntegrations } from "@/integrations/hub";

describe("Enterprise Web Foundation", () => {
  it("exposes version and stack readiness", () => {
    expect(webConfig.version).toBe("9.0.5");
    expect(webConfig.sprint).toBe("26.5");
    expect(webConfig.multiTenant).toBe(true);
    expect(webConfig.mfaReady).toBe(true);
    expect(webConfig.supportedLocales).toEqual(["en", "ru", "uk"]);
  });

  it("has localized strings", () => {
    expect(messages.en["nav.workspace"]).toBeTruthy();
    expect(messages.en["nav.navigation"]).toBeTruthy();
    expect(messages.en["nav.dashboard"]).toBeTruthy();
    expect(messages.ru["nav.dashboard"]).toBeTruthy();
    expect(messages.uk["nav.dashboard"]).toBeTruthy();
  });

  it("links enterprise integrations", () => {
    expect(hubIntegrations.enterpriseHub).toContain("enterprise-hub");
    expect(hubIntegrations.webFoundation).toContain("enterprise-ewf");
    expect(hubIntegrations.designSystem).toContain("enterprise-eds");
    expect(hubIntegrations.identityCenter).toContain("enterprise-eic");
    expect(hubIntegrations.workspacePlatform).toContain("enterprise-ews");
    expect(hubIntegrations.navigationPlatform).toContain("enterprise-enp");
  });
});
