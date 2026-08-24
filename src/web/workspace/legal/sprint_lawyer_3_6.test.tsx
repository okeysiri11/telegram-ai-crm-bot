/**
 * Sprint Lawyer 3.6 — detail drawer tabs, cross-linking, AI handoff context.
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { LawyerDetailDrawer } from "./LawyerDetailDrawer";
import { LawyerAiLawyerPanel } from "./LawyerAiLawyerPanel";

const RELATED_BODY = {
  ok: true,
  item: { id: "case-1", title: "Дело 3.6", case_number: "A-36", status: "active", client_id: "client-1" },
  related: {
    clients: [{ id: "client-1", name: "Клиент 3.6", status: "active" }],
    cases: [],
    contracts: [{ id: "ct-1", title: "Договор 3.6", status: "draft" }],
    documents: [{ id: "doc-1", title: "Документ 3.6", status: "uploaded" }],
    tasks: [{ id: "t-1", title: "Задача 3.6", status: "new" }],
    hearings: [{ id: "h-1", title: "Заседание 3.6", status: "scheduled" }],
    calendar: [],
    monitoring: [{ id: "w-1", title: "Наблюдение W-36", status: "active" }],
    changes: [{ id: "chg-1", summary: "Новое заседание", change_type: "new_event" }],
    files: [{ id: "f-1", filename: "scan.png", mime_type: "image/png" }],
    activity: [{ id: "a-1", created_at: "2026-08-13T09:00:00+00:00", summary: "Дело создано", action: "created" }],
    ai: [],
  },
};

vi.stubGlobal(
  "fetch",
  vi.fn(async (url: string) => {
    const u = String(url);
    if (u.includes("/related")) {
      return { ok: true, status: 200, json: async () => RELATED_BODY };
    }
    if (u.includes("/ai/")) {
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [], modes: [], sources: [], inspector: {} }) };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
  }),
);

describe("Sprint Lawyer 3.6 — detail drawer", () => {
  it("opens drawer with common tabs and overview", async () => {
    render(
      <LawyerDetailDrawer
        kind="case"
        itemId="case-1"
        headers={{}}
        canOperate
        onClose={() => undefined}
        onNavigate={() => undefined}
      />,
    );
    expect(await screen.findByTestId("lawyer-drawer-title")).toBeTruthy();
    const tabs = screen.getByTestId("lawyer-drawer-tabs").textContent || "";
    expect(tabs).toMatch(/Обзор/);
    expect(tabs).toMatch(/Файлы/);
    expect(tabs).toMatch(/Связи/);
    expect(tabs).toMatch(/Активность/);
    expect(screen.getByTestId("lawyer-drawer-overview").textContent).toMatch(/A-36/);
  });

  it("links tab shows cross-linked entities incl. monitoring and navigates", async () => {
    const onNavigate = vi.fn();
    render(
      <LawyerDetailDrawer
        kind="case"
        itemId="case-1"
        headers={{}}
        canOperate
        onClose={() => undefined}
        onNavigate={onNavigate}
      />,
    );
    await screen.findByTestId("lawyer-drawer-title");
    fireEvent.click(screen.getByText("Связи"));
    const links = screen.getByTestId("lawyer-drawer-links").textContent || "";
    expect(links).toMatch(/Клиент 3\.6/);
    expect(links).toMatch(/Договор 3\.6/);
    expect(links).toMatch(/Наблюдение W-36/);
    expect(links).toMatch(/Новое заседание/);
    const openButtons = screen.getAllByText("Открыть");
    fireEvent.click(openButtons[0]);
    expect(onNavigate).toHaveBeenCalled();
  });

  it("AI handoff sends explicit context", async () => {
    const onHandoffAi = vi.fn();
    render(
      <LawyerDetailDrawer
        kind="case"
        itemId="case-1"
        headers={{}}
        canOperate
        onClose={() => undefined}
        onNavigate={() => undefined}
        onHandoffAi={onHandoffAi}
      />,
    );
    await screen.findByTestId("lawyer-drawer-title");
    fireEvent.click(screen.getByTestId("lawyer-drawer-ai-handoff"));
    await waitFor(() => expect(onHandoffAi).toHaveBeenCalled());
    const ctx = onHandoffAi.mock.calls[0][0];
    expect(ctx.caseId).toBe("case-1");
    expect(ctx.clientId).toBe("client-1");
    expect(ctx.documentIds).toContain("doc-1");
    expect((ctx.contextLabels || []).join(" ")).toMatch(/Дело/);
  });
});

describe("Sprint Lawyer 3.6 — AI panel handoff context", () => {
  it("shows Контекст block with checked sources", async () => {
    render(
      <LawyerAiLawyerPanel
        headers={{}}
        canOperate
        clients={[]}
        cases={[]}
        documents={[]}
        onRefresh={() => undefined}
        initial={{
          caseId: "case-1",
          documentIds: ["doc-1"],
          contextLabels: ["Дело A-36", "1 документ(ов)"],
        }}
      />,
    );
    const ctx = await screen.findByTestId("lawyer-ai-handoff-context");
    expect(ctx.textContent).toMatch(/Контекст:/);
    expect(ctx.textContent).toMatch(/✓ Дело A-36/);
    expect(ctx.textContent).toMatch(/✓ 1 документ/);
  });
});
