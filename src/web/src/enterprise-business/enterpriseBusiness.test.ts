/**
 * Sprint 30.8 — Enterprise business modules smoke tests.
 */
import { describe, expect, it } from "vitest";
import { createCrmClient, hydrateCrm, readCrmCache, writeCrmCache } from "./crmApi";
import { deriveOwnerMetrics } from "./deriveOwnerMetrics";
import { countProjects } from "./ProjectsModulePage";
import { countKnowledge } from "./KnowledgeModulePage";

describe("Sprint 30.8 Enterprise Business Modules", () => {
  it("CRM workspace cache supports create without mock seed", async () => {
    writeCrmCache({
      clients: [],
      companies: [],
      contacts: [],
      leads: [],
      deals: [],
      notes: [],
      attachments: [],
      activities: [],
      source: "workspace",
      loadedAt: null,
    });
    const client = await createCrmClient({
      firstName: "Иван",
      lastName: "Тест",
      email: "ivan@example.com",
      phone: "+7000",
    });
    expect(client.firstName).toBe("Иван");
    expect(readCrmCache().clients.some((c) => c.id === client.id)).toBe(true);
    const hydrated = await hydrateCrm();
    expect(hydrated.loadedAt).toBeTruthy();
  });

  it("owner metrics expose required platform cards", () => {
    const cards = deriveOwnerMetrics();
    const ids = cards.map((c) => c.id);
    for (const required of [
      "users",
      "orgs",
      "ai",
      "crm",
      "projects",
      "runtime",
      "health",
      "notifications",
      "activity",
      "status",
    ]) {
      expect(ids).toContain(required);
    }
    expect(cards.every((c) => c.route.startsWith("/"))).toBe(true);
  });

  it("exports operational module pages", async () => {
    expect(typeof (await import("./CrmModulePage")).CrmModulePage).toBe("function");
    expect(typeof (await import("./ProjectsModulePage")).ProjectsModulePage).toBe("function");
    expect(typeof (await import("./KnowledgeModulePage")).KnowledgeModulePage).toBe("function");
    expect(typeof (await import("./CalendarModulePage")).CalendarModulePage).toBe("function");
    expect(typeof (await import("./DriveModulePage")).DriveModulePage).toBe("function");
    expect(typeof (await import("./MarketplaceModulePage")).MarketplaceModulePage).toBe("function");
    expect(typeof (await import("./NotificationsModulePage")).NotificationsModulePage).toBe("function");
    expect(typeof (await import("./AiStudioModulePage")).AiStudioModulePage).toBe("function");
    expect(typeof countProjects()).toBe("number");
    expect(typeof countKnowledge()).toBe("number");
  });

  it("ModulePageById routes business modules to real pages", async () => {
    const { ModulePageById } = await import("@/modules/ModuleHubRoute");
    expect(typeof ModulePageById).toBe("function");
    const { getModuleBySlug } = await import("@/modules/moduleCatalog");
    expect(getModuleBySlug("crm")?.deepLink).toContain("/crm");
    expect(getModuleBySlug("projects")?.deepLink).toContain("/projects");
    expect(getModuleBySlug("knowledge")?.deepLink).toContain("/knowledge");
    expect(getModuleBySlug("documents")?.deepLink).toContain("/documents");
    expect(getModuleBySlug("marketplace")?.deepLink).toContain("/marketplace");
  });
});
