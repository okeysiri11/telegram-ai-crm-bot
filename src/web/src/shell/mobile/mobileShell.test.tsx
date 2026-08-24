import { describe, expect, it } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useSearchParams } from "react-router-dom";
import { DEBUG_NOTIFICATION_FIXTURES, useNotificationStore } from "@/notifications/notificationStore";
import {
  navFromVertical,
  PLATFORM_MANAGEMENT_NAV,
  verticalIdFromPath,
  operationalNavForVertical,
  mobileDrawerNav,
  isMobileNavHrefActive,
  workspaceHomePath,
  resolveMobileHomeWorkspace,
  workspaceLabel,
  isDemoAccount,
  sectionTitle,
  createActionsForWorkspace,
  mobileHomeQuickActions,
  importantTodayFromLive,
  workspaceContextCopy,
  hrefLooksLocal,
  MOBILE_VERTICAL_HUB,
  isOwnerSystemContext,
  MOBILE_SETTINGS_CATALOG,
  visibleMobileSettings,
} from "@/shell/mobile";
import { MobileHome } from "@/shell/mobile/MobileHome";
import { MobileChrome } from "@/shell/mobile/MobileChrome";
import { MobileBottomNav } from "@/shell/mobile/MobileBottomNav";
import { MobileWorkspaceHub } from "@/shell/mobile/MobileWorkspaceHub";
import { MobileCreateSheet } from "@/shell/mobile/MobileCreateSheet";
import { MobileWorkspaceDrawer } from "@/shell/mobile/MobileWorkspaceDrawer";
import { useMobileChromeStore } from "@/shell/mobile/mobileChromeStore";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";
import { useMobileOverlayHistory } from "@/shell/mobile/useMobileOverlayHistory";
import { liveBuildLabel } from "@/shell/mobile/liveBuildLabel";
import { WorkspaceLandingGate } from "@/modules/WorkspaceLandingGate";
import { AGRO_DOMAIN_MENU_LABELS, AGRO_OPS_NAV } from "../../../workspace/agro/agroOpsNav";
import { UnifiedToastStrip } from "@/workspace-chrome/UnifiedToastStrip";
import { webConfig } from "@/config/webConfig";

describe("mobile workspace navigation", () => {
  it("resolves verticals from path without hardcoding agro", () => {
    expect(verticalIdFromPath("/workspace/auto")).toBe("auto");
    expect(verticalIdFromPath("/vertical/agro/deals")).toBe("agro");
    expect(verticalIdFromPath("/workspace/crypto")).toBe("crypto");
    expect(verticalIdFromPath("/workspace/legal")).toBe("legal");
    expect(workspaceLabel("agro")).toBe("Агро");
    expect(workspaceHomePath("auto")).toContain("/workspace/auto");
  });

  it("sends owner to the workspace hub instead of the same dashboard", () => {
    expect(isOwnerSystemContext("owner")).toBe(true);
    expect(workspaceHomePath("owner")).toBe("/workspace");
    const qa = mobileHomeQuickActions("owner");
    expect(qa.find((a) => a.id === "panel")?.action).toBe("panel");
    expect(qa.find((a) => a.id === "ai")?.href).toBe("/ai-agents");
    expect(qa.find((a) => a.id === "settings")?.href).toBe("/settings");
  });

  it("builds nav from each vertical catalog", () => {
    for (const id of ["agro", "auto", "crypto", "legal", "beauty", "cafe", "drone", "crm"]) {
      const items = navFromVertical(id);
      expect(items.length).toBeGreaterThan(3);
      expect(items.some((item) => item.label.length > 0)).toBe(true);
    }
  });

  it("keeps platform management off the home path list", () => {
    expect(PLATFORM_MANAGEMENT_NAV.some((i) => i.label.includes("System Health") || i.href === "/health")).toBe(
      true,
    );
  });

  it("marks demo accounts without treating them as production", () => {
    expect(isDemoAccount("owner@demo.corp", "demo-corp")).toBe(true);
    expect(isDemoAccount("ops@company.io", "org-prod")).toBe(false);
  });

  it("reads section titles from view query", () => {
    expect(sectionTitle("/workspace/agro", "?view=deals", "agro", navFromVertical("agro"))).toBe("Сделки");
    expect(sectionTitle("/workspace/agro", "?view=weather", "agro", [])).toBe("Погода");
  });
});

describe("mobile create catalog", () => {
  it("uses auto ops cabinets instead of desktop-only forms", () => {
    const auto = createActionsForWorkspace("auto");
    expect(auto.map((a) => a.label)).toEqual(
      expect.arrayContaining(["Автомобиль", "Клиент", "Сделка", "Платёж", "Расход", "Поставка", "Документ", "Задача"]),
    );
    expect(auto.find((a) => a.label === "Автомобиль")?.href).toBe("/workspace/auto?view=vehicles&action=create");
  });

  it("uses agro ops cabinets", () => {
    const agro = createActionsForWorkspace("agro");
    expect(agro.map((a) => a.label)).toEqual(
      expect.arrayContaining(["Контрагент", "Сделка", "Поставка", "Склад", "Документ", "Задача"]),
    );
    expect(agro.find((a) => a.label === "Контрагент")?.href).toBe("/workspace/agro?view=counterparties");
  });
});

describe("owner context copy", () => {
  it("does not name the workspace Owner", () => {
    const copy = workspaceContextCopy("owner", "Owner");
    expect(copy.title).toBe("Владелец системы");
    expect(copy.kicker).toBe("Режим");
    expect(copy.hint).toMatch(/Выберите рабочее пространство/);
  });
});

describe("important today", () => {
  it("stays empty without live counts", () => {
    expect(importantTodayFromLive({ unread: 0, healthFailed: 0 })).toEqual([]);
  });
});

describe("public-compatible hrefs", () => {
  it("does not leak localhost into mobile navigation", () => {
    const hrefs = [
      ...mobileHomeQuickActions("owner").map((i) => i.href),
      ...createActionsForWorkspace("auto").map((i) => i.href),
      ...createActionsForWorkspace("agro").map((i) => i.href),
      ...MOBILE_VERTICAL_HUB.map((i) => i.href),
      ...PLATFORM_MANAGEMENT_NAV.map((i) => i.href),
      webConfig.apiBase,
    ];
    expect(hrefs.filter((h) => hrefLooksLocal(h))).toEqual([]);
    expect(webConfig.apiBase === "/api" || webConfig.apiBase.startsWith("https://")).toBe(true);
  });
});

describe("notification seed policy", () => {
  it("does not auto-load demo toast fixtures", () => {
    expect(DEBUG_NOTIFICATION_FIXTURES.some((n) => n.title === "AI insight ready")).toBe(true);
    expect(useNotificationStore.getState().items.some((n) => n.title === "AI insight ready")).toBe(false);
  });

  it("does not toast historical unread items on mount", () => {
    useNotificationStore.setState({
      items: [
        {
          id: "hist",
          kind: "ai",
          title: "AI insight ready",
          body: "Weekly forecast available",
          createdAt: new Date().toISOString(),
          read: false,
        },
      ],
    });
    render(<UnifiedToastStrip />);
    expect(screen.queryByText("AI insight ready")).toBeNull();
  });
});

describe("mobile home", () => {
  it("shows workspace, working quick actions, and empty important today", () => {
    useNotificationStore.setState({ items: [] });
    render(
      <MemoryRouter>
        <MobileHome workspaceId="agro" workspaceLabel="Агро" roleLabel="Директор" />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("mobile-home-workspace")).toHaveTextContent("Агро");
    expect(screen.getByTestId("mobile-open-workspace")).toBeEnabled();
    expect(screen.getByTestId("mobile-open-workspace")).toHaveTextContent("Перейти в Агро");
    expect(screen.getByTestId("mobile-open-panel")).toHaveTextContent("Открыть панель");
    expect(screen.getByTestId("mobile-open-ai")).toHaveTextContent("Команда AI");
    expect(screen.getByTestId("mobile-open-settings")).toHaveTextContent("Настройки");
    expect(screen.getByText("На сегодня критичных событий нет.")).toBeInTheDocument();
    expect(screen.queryByText("NPS")).toBeNull();
  });

  it("renders owner system mode instead of a fake Owner workspace", () => {
    render(
      <MemoryRouter>
        <MobileHome workspaceId="owner" workspaceLabel="Owner" roleLabel="Владелец" />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("mobile-home-workspace")).toHaveTextContent("Владелец системы");
    expect(screen.getByText("Выберите рабочее пространство")).toBeInTheDocument();
    expect(screen.getByTestId("mobile-hub-auto")).toBeInTheDocument();
    expect(screen.getByTestId("mobile-hub-agro")).toBeInTheDocument();
  });

  it("navigates owner workspace and AI actions to real routes", async () => {
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            path="/dashboard"
            element={<MobileHome workspaceId="owner" workspaceLabel="Owner" roleLabel="Владелец" />}
          />
          <Route path="/workspace" element={<p data-testid="arrived-workspace">workspace</p>} />
        </Routes>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("mobile-open-workspace"));
    await waitFor(() => expect(screen.getByTestId("arrived-workspace")).toBeInTheDocument());
  });

  it("opens the AI command center from home", async () => {
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            path="/dashboard"
            element={<MobileHome workspaceId="owner" workspaceLabel="Owner" roleLabel="Владелец" />}
          />
          <Route path="/ai-agents" element={<p data-testid="arrived-ai">ai</p>} />
        </Routes>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("mobile-open-ai"));
    await waitFor(() => expect(screen.getByTestId("arrived-ai")).toBeInTheDocument());
  });
});

describe("mobile workspace hub", () => {
  it("lists operational verticals", () => {
    render(
      <MemoryRouter>
        <MobileWorkspaceHub />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("mobile-workspace-hub")).toBeInTheDocument();
    expect(screen.getByTestId("mobile-hub-auto")).toHaveTextContent("Авто");
    expect(screen.getByTestId("mobile-hub-agro")).toHaveTextContent("Агро");
  });
});

describe("mobile bottom nav and create sheet", () => {
  it("highlights home and opens create sheet", () => {
    useMobileChromeStore.getState().closeAll();
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route path="/dashboard" element={<p>home</p>} />
          <Route path="/workspace" element={<p>hub</p>} />
          <Route path="/notifications" element={<p>notes</p>} />
        </Routes>
        <MobileBottomNav />
        <MobileCreateSheet verticalId="auto" />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("mobile-bottom-home")).toHaveClass("is-active");
    fireEvent.click(screen.getByTestId("mobile-bottom-create"));
    expect(screen.getByTestId("mobile-create-sheet")).toBeInTheDocument();
    expect(screen.getByText("Автомобиль")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("mobile-bottom-workspace"));
    expect(screen.getByText("hub")).toBeInTheDocument();
  });
});

describe("mobile widths", () => {
  for (const width of [360, 390, 412, 430]) {
    it(`renders home at ${width}px`, () => {
      Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
      render(
        <MemoryRouter>
          <MobileHome workspaceId="owner" workspaceLabel="Owner" roleLabel="Владелец" />
        </MemoryRouter>,
      );
      expect(screen.getByTestId("mobile-home")).toBeInTheDocument();
      expect(screen.getByTestId("mobile-open-workspace")).toBeEnabled();
    });
  }
});

describe("mobile 1.2 settings and create deep link", () => {
  it("lists authorized settings sections without localhost hrefs", () => {
    expect(MOBILE_SETTINGS_CATALOG.map((i) => i.label)).toEqual(
      expect.arrayContaining([
        "Профиль",
        "Организация",
        "Рабочие пространства",
        "Пользователи и роли",
        "Telegram",
        "Уведомления",
        "Безопасность",
        "AI",
        "AUTO",
        "AGRO",
        "Источники данных",
      ]),
    );
    expect(visibleMobileSettings().every((i) => !hrefLooksLocal(i.href))).toBe(true);
  });

  it("opens create vehicle with action query", () => {
    expect(createActionsForWorkspace("auto").find((a) => a.id === "vehicle")?.href).toContain("action=create");
  });
});

describe("mobile agro 1.3 operational workspace", () => {
  const AGRO_OPS_LABELS = [
    "Главная",
    "Командный центр",
    "Сводка",
    "Поля",
    "Культуры",
    "Посевы",
    "Техника",
    "Работы",
    "Урожай",
    "Операции",
    "Контрагенты",
    "Сделки",
    "Договоры",
    "Документы",
    "Расчёты",
    "Бухгалтерия",
    "Поставки",
    "Склады",
    "Погода",
    "Цены и рынки",
    "Логистика",
    "Агро-разведка",
    "Аналитика",
    "Календарь",
    "Задачи",
    "Уведомления",
    "Настройки",
  ];

  it("uses the operational Agro cabinet, not domain catalog A", () => {
    const items = operationalNavForVertical("agro");
    expect(items).toHaveLength(AGRO_OPS_LABELS.length);
    expect(AGRO_OPS_NAV).toHaveLength(AGRO_OPS_LABELS.length);
    expect(items.map((i) => i.label)).toEqual(AGRO_OPS_LABELS);
    expect(items.find((i) => i.id === "accounting")?.href).toBe("/workspace/agro?view=accounting");
    expect(items.find((i) => i.id === "weather")?.href).toBe("/workspace/agro?view=weather");
    expect(items.find((i) => i.id === "intel")?.href).toBe("/workspace/agro?view=intel");
    expect(items.find((i) => i.id === "home")?.href).toBe("/workspace/agro");
    const drawer = mobileDrawerNav("agro", { verticalId: null, items: [] });
    expect(drawer.map((i) => i.label)).toEqual(AGRO_OPS_LABELS);
    for (const label of AGRO_DOMAIN_MENU_LABELS) {
      expect(drawer.some((i) => i.label.includes(label))).toBe(false);
    }
    expect(drawer.every((i) => !hrefLooksLocal(i.href))).toBe(true);
    expect(hrefLooksLocal("http://localhost:5180/workspace/agro")).toBe(true);
    expect(hrefLooksLocal("http://127.0.0.1:8080")).toBe(true);
  });

  it("marks weather active from the view query only", () => {
    expect(isMobileNavHrefActive("/workspace/agro?view=weather", "/workspace/agro", "?view=weather")).toBe(true);
    expect(isMobileNavHrefActive("/workspace/agro", "/workspace/agro", "?view=weather")).toBe(false);
    expect(isMobileNavHrefActive("/workspace/agro", "/workspace/agro", "")).toBe(true);
    expect(sectionTitle("/workspace/agro", "?view=weather", "agro", operationalNavForVertical("agro"))).toBe("Погода");
    expect(sectionTitle("/workspace/agro", "?view=accounting", "agro", [])).toBe("Бухгалтерия");
    expect(sectionTitle("/workspace/agro", "", "agro", [])).toBeNull();
    expect(workspaceHomePath("agro")).toBe("/workspace/agro");
  });

  it("opens the real Agro workspace from «Открыть рабочее пространство»", async () => {
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            path="/dashboard"
            element={<MobileHome workspaceId="agro" workspaceLabel="Агро" roleLabel="Директор" />}
          />
          <Route path="/workspace/agro" element={<p data-testid="agro-ops">agro ops</p>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(mobileHomeQuickActions("agro").find((a) => a.id === "panel")?.action).toBe("panel");
    expect(workspaceHomePath("agro")).toBe("/workspace/agro");
    fireEvent.click(screen.getByTestId("mobile-open-workspace"));
    await waitFor(() => expect(screen.getByTestId("agro-ops")).toBeInTheDocument());
  });

  it("opens the operational Agro panel from «Открыть панель» without leaving home", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 412 });
    useVerticalWorkspaceStore.getState().setVerticalId("agro");
    useMobileChromeStore.getState().closeAll();

    function AgroSection() {
      const [params] = useSearchParams();
      return <p data-testid="agro-section">{params.get("view") || "home"}</p>;
    }

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            path="/dashboard"
            element={
              <>
                <MobileChrome />
                <MobileHome workspaceId="agro" workspaceLabel="Агро" roleLabel="Директор" />
              </>
            }
          />
          <Route path="/workspace/agro" element={<AgroSection />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByTestId("mobile-home")).toBeInTheDocument();
    expect(screen.queryByTestId("mobile-workspace-drawer")).toBeNull();

    fireEvent.click(screen.getByTestId("mobile-open-panel"));
    const panel = await screen.findByTestId("mobile-workspace-drawer");
    expect(panel).toHaveAttribute("data-ops-panel", "true");
    expect(screen.getByTestId("mobile-home")).toBeInTheDocument();
    expect(screen.queryByTestId("agro-section")).toBeNull();
    for (const label of AGRO_OPS_LABELS) {
      expect(panel).toHaveTextContent(label);
    }
    expect(screen.queryByText("Товары (закупка / продажа)")).toBeNull();
    expect(screen.queryByText("Управление платформой")).toBeNull();
    // AGRO 2.6: «Поля» is an operational module — must appear in the drawer.
    expect(screen.getByTestId("mobile-drawer-fields")).toHaveTextContent("Поля");
    expect(screen.getByTestId("mobile-drawer-sowing")).toHaveTextContent("Посевы");
    expect(screen.getByTestId("mobile-drawer-harvest")).toHaveTextContent("Урожай");

    fireEvent.click(screen.getByTestId("mobile-drawer-accounting"));
    await waitFor(() => expect(screen.getByTestId("agro-section")).toHaveTextContent("accounting"));
  });

  it("opens Контрагенты from the operational panel", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 412 });
    useVerticalWorkspaceStore.getState().setVerticalId("agro");
    useMobileChromeStore.getState().closeAll();

    function AgroSection() {
      const [params] = useSearchParams();
      return <p data-testid="agro-section">{params.get("view") || "home"}</p>;
    }

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            path="/dashboard"
            element={
              <>
                <MobileChrome />
                <MobileHome workspaceId="agro" workspaceLabel="Агро" roleLabel="Директор" />
              </>
            }
          />
          <Route path="/workspace/agro" element={<AgroSection />} />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByTestId("mobile-open-panel"));
    await screen.findByTestId("mobile-drawer-counterparties");
    fireEvent.click(screen.getByTestId("mobile-drawer-counterparties"));
    await waitFor(() => expect(screen.getByTestId("agro-section")).toHaveTextContent("counterparties"));
  });

  it("keeps Agro as the home workspace after it is selected", () => {
    useVerticalWorkspaceStore.getState().setVerticalId("agro");
    expect(resolveMobileHomeWorkspace("agro")).toBe("agro");
    expect(resolveMobileHomeWorkspace("owner")).toBe("owner");
    expect(workspaceHomePath("agro")).toBe("/workspace/agro");
    expect(workspaceHomePath("agro")).not.toContain("/vertical/");
  });

  it("renders the operational drawer without mixing domain catalog A", () => {
    useMobileChromeStore.getState().setDrawerOpen(true);
    render(
      <MemoryRouter initialEntries={["/workspace/agro"]}>
        <MobileWorkspaceDrawer
          workspaceLabel="Агро"
          roleLabel="Директор"
          items={operationalNavForVertical("agro")}
          showPlatform={false}
          platformItems={[]}
        />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("mobile-workspace-drawer")).toBeInTheDocument();
    expect(screen.getByTestId("mobile-drawer-accounting")).toHaveTextContent("Бухгалтерия");
    expect(screen.getByTestId("mobile-drawer-weather")).toHaveTextContent("Погода");
    expect(screen.getByTestId("mobile-drawer-intel")).toHaveTextContent("Агро-разведка");
    expect(screen.queryByText("Товары (закупка / продажа)")).toBeNull();
    expect(screen.getByTestId("mobile-drawer-fields")).toHaveTextContent("Поля");
    expect(screen.getByTestId("mobile-drawer-works")).toHaveTextContent("Работы");
    expect(screen.queryByText("Управление платформой")).toBeNull();
    useMobileChromeStore.getState().closeAll();
  });

  it("closes the drawer on Android back before leaving the page", async () => {
    function Probe() {
      useMobileOverlayHistory();
      const open = useMobileChromeStore((s) => s.drawerOpen);
      return <p data-testid="overlay-state">{open ? "open" : "closed"}</p>;
    }
    useMobileChromeStore.getState().closeAll();
    render(
      <MemoryRouter>
        <Probe />
      </MemoryRouter>,
    );
    useMobileChromeStore.getState().setDrawerOpen(true);
    await waitFor(() => expect(screen.getByTestId("overlay-state")).toHaveTextContent("open"));
    window.dispatchEvent(new PopStateEvent("popstate"));
    await waitFor(() => expect(screen.getByTestId("overlay-state")).toHaveTextContent("closed"));
  });

  it("loads Agro ops on /workspace/agro at 412px instead of the catalog landing", () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 412 });
    render(
      <MemoryRouter initialEntries={["/workspace/agro"]}>
        <WorkspaceLandingGate landingId="agro">
          <p data-testid="agro-ops-cabinet">cabinet</p>
        </WorkspaceLandingGate>
      </MemoryRouter>,
    );
    expect(screen.getByTestId("agro-ops-cabinet")).toBeInTheDocument();
    expect(screen.queryByText("Открыть ферму")).toBeNull();
  });
});

describe("live tunnel indicator", () => {
  it("labels trycloudflare hosts as LIVE without secrets", () => {
    expect(liveBuildLabel("example.trycloudflare.com")).toMatch(/^LIVE • /);
    expect(liveBuildLabel("example.trycloudflare.com")).not.toMatch(/localhost|token|secret/i);
  });
});
