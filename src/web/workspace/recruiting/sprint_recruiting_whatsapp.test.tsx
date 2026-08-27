/**
 * Sprint Recruiting 1.11 — WhatsApp production UI.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProviderConnectionsPage } from "./ProviderConnectionsPage";
import { WhatsAppConversation } from "./WhatsAppConversation";

const SECRET = "wa-super-secret-token";

let providerItems = [
  {
    provider: "whatsapp",
    label: "WhatsApp",
    status: "NOT_CONFIGURED",
    status_label_ru: "Не настроено",
    mode: "LIVE",
    mode_label_ru: "LIVE",
    frozen: false,
    connect_cta: true,
    wizard: [
      { id: "phone_number_id", label_ru: "Phone identifier", secret: false },
      { id: "access_token", label_ru: "API token", secret: true },
    ],
  },
  {
    provider: "telegram",
    label: "Telegram",
    status: "DISABLED",
    status_label_ru: "Отключено (заморожено)",
    mode: "LIVE",
    frozen: true,
    connect_cta: false,
    message_ru: "Telegram намеренно отключён.",
  },
];

const conversationItems = [
  {
    id: "in1",
    direction: "incoming",
    body: "привет",
    created_at: "2026-08-27T10:00:00Z",
    send_status: "RECEIVED",
  },
  {
    id: "out1",
    direction: "outgoing",
    body: "ответ",
    created_at: "2026-08-27T10:01:00Z",
    send_status: "SENT",
    delivered: true,
    read: true,
  },
];

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (u.includes("/whatsapp/ai-draft") && init?.method === "POST") {
    return {
      ok: true,
      status: 200,
      json: async () => ({ ok: true, body: "Здравствуйте, Анна.", sent: false, live_write_access: false }),
    };
  }
  if (u.includes("/candidates/") && u.includes("/whatsapp") && init?.method === "POST") {
    const body = String(init.body || "");
    if (body.includes('"confirm":true')) {
      return { ok: true, status: 200, json: async () => ({ ok: true, item: { id: "m1", status: "SENT", delivered: false } }) };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true, approval_required: true, sent: false }) };
  }
  if (u.includes("/whatsapp/conversations")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: conversationItems }) };
  }
  if (u.includes("/providers") && init?.method === "POST") {
    return { ok: true, status: 200, json: async () => ({ ok: true, status: "CONNECTED" }) };
  }
  if (u.includes("/providers")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: providerItems }) };
  }
  return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
});

vi.stubGlobal("fetch", fetchMock);

function renderProviders() {
  return render(
    <MemoryRouter initialEntries={["/workspace/recruiting/integrations?embed=1"]}>
      <Routes>
        <Route path="/workspace/recruiting/integrations" element={<ProviderConnectionsPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("WhatsApp provider card", () => {
  beforeEach(() => {
    fetchMock.mockClear();
    providerItems = [
      {
        provider: "whatsapp",
        label: "WhatsApp",
        status: "NOT_CONFIGURED",
        status_label_ru: "Не настроено",
        mode: "LIVE",
        mode_label_ru: "LIVE",
        frozen: false,
        connect_cta: true,
        wizard: [
          { id: "phone_number_id", label_ru: "Phone identifier", secret: false },
          { id: "access_token", label_ru: "API token", secret: true },
        ],
      },
      {
        provider: "telegram",
        label: "Telegram",
        status: "DISABLED",
        status_label_ru: "Отключено (заморожено)",
        mode: "LIVE",
        frozen: true,
        connect_cta: false,
        message_ru: "Telegram намеренно отключён.",
      },
    ];
  });

  it("shows WhatsApp NOT_CONFIGURED card", async () => {
    renderProviders();
    expect(await screen.findByTestId("whatsapp-status-not-configured")).toBeTruthy();
    expect(screen.getByTestId("provider-card-whatsapp").textContent).toContain("Не настроено");
  });

  it("shows credential form with secret masking", async () => {
    renderProviders();
    fireEvent.click(await screen.findByText("Настроить"));
    expect(document.body.textContent).not.toContain(SECRET);
    const input = screen.getByTestId("secret-input-access_token") as HTMLInputElement;
    expect(input.type).toBe("password");
    expect(input.value).toBe("");
    fireEvent.change(input, { target: { value: SECRET } });
    expect(input.type).toBe("password");
  });

  it("check connection action", async () => {
    providerItems[0] = { ...providerItems[0], status: "CONNECTED", status_label_ru: "Подключено" };
    renderProviders();
    fireEvent.click(await screen.findByTestId("whatsapp-check-connection"));
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/providers/whatsapp/test"))).toBe(true);
  });

  it("shows CONNECTED state", async () => {
    providerItems[0] = { ...providerItems[0], status: "CONNECTED", status_label_ru: "Подключено" };
    renderProviders();
    expect(await screen.findByTestId("whatsapp-status-connected")).toBeTruthy();
  });

  it("shows ERROR state", async () => {
    providerItems[0] = { ...providerItems[0], status: "ERROR", status_label_ru: "Ошибка", last_error: "AUTH_ERROR" } as typeof providerItems[0];
    renderProviders();
    expect(await screen.findByTestId("whatsapp-status-error")).toBeTruthy();
    expect(document.body.textContent).not.toContain(SECRET);
  });
});

describe("WhatsApp conversation", () => {
  beforeEach(() => fetchMock.mockClear());

  it("renders incoming/outgoing messages and statuses", async () => {
    render(<WhatsAppConversation candidateId="c1" candidateName="Анна" candidatePhone="79001112233" headers={{ "X-Role": "owner" }} />);
    expect(await screen.findByTestId("whatsapp-conversation")).toBeTruthy();
    expect(screen.getByTestId("whatsapp-provider-badge").textContent).toContain("WhatsApp");
    expect(screen.getByTestId("whatsapp-incoming").textContent).toContain("привет");
    expect(screen.getByTestId("whatsapp-outgoing").textContent).toContain("ответ");
    expect(screen.getAllByTestId("whatsapp-timestamp").length).toBeGreaterThan(0);
    expect(screen.getByTestId("whatsapp-outgoing").textContent).toContain("прочитано");
  });

  it("requires human confirmation before send", async () => {
    render(<WhatsAppConversation candidateId="c1" candidateName="Анна" candidatePhone="79001112233" headers={{ "X-Role": "owner" }} />);
    await screen.findByTestId("whatsapp-conversation");
    fireEvent.change(screen.getByTestId("whatsapp-compose-text"), { target: { value: "hello" } });
    fireEvent.click(screen.getByTestId("whatsapp-send"));
    expect(await screen.findByTestId("whatsapp-human-confirm")).toBeTruthy();
    const pending = fetchMock.mock.calls.filter((call) => String(call[0]).includes("/candidates/c1/whatsapp"));
    expect(pending.some((call) => String(call[1]?.body || "").includes('"confirm":true'))).toBe(false);
    fireEvent.click(screen.getByTestId("whatsapp-confirm-send"));
    await waitFor(() => {
      expect(fetchMock.mock.calls.some((call) => String(call[1]?.body || "").includes('"confirm":true'))).toBe(true);
    });
  });

  it("AI draft does not send automatically", async () => {
    render(<WhatsAppConversation candidateId="c1" candidateName="Анна" candidatePhone="79001112233" headers={{ "X-Role": "owner" }} />);
    await screen.findByTestId("whatsapp-conversation");
    fireEvent.click(screen.getByTestId("whatsapp-ai-draft"));
    await waitFor(() => {
      expect((screen.getByTestId("whatsapp-compose-text") as HTMLTextAreaElement).value).toContain("Анна");
    });
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/whatsapp/ai-draft"))).toBe(true);
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/candidates/c1/whatsapp"))).toBe(false);
  });
});
