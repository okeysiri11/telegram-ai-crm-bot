/**
 * Sprint Recruiting 1.10 — Email SMTP UI + Telegram freeze overlay.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProviderConnectionsPage } from "./ProviderConnectionsPage";
import { CandidateEmailComposer } from "./CandidateEmailComposer";

const SECRET = "smtp-super-secret-pass";

let providerItems = [
  {
    provider: "email",
    label: "Email",
    status: "NOT_CONFIGURED",
    status_label_ru: "Не настроено",
    mode: "LIVE",
    mode_label_ru: "LIVE",
    frozen: false,
    connect_cta: true,
    wizard: [{ id: "smtp_password", label_ru: "Пароль SMTP", secret: true }],
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

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  const u = String(url);
  if (u.includes("/email/templates")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: [{ id: "intro", label_ru: "Знакомство", subject: "Вакансия Driver", body: "Здравствуйте, Анна" }] }) };
  }
  if (u.includes("/email/preview")) {
    return { ok: true, status: 200, json: async () => ({ ok: true, subject: "Вакансия Driver", body: "Здравствуйте, Анна" }) };
  }
  if (u.includes("/candidates/") && u.includes("/emails") && !init?.method) {
    return { ok: true, status: 200, json: async () => ({ ok: true, items: [{ id: "h1", status: "SENT", subject: "Вакансия", delivered: false }] }) };
  }
  if (u.includes("/candidates/") && u.includes("/email") && init?.method === "POST") {
    const body = String(init.body || "");
    if (body.includes("campaign_id")) {
      return { ok: false, status: 400, json: async () => ({ ok: false, error: "APPROVAL_REQUIRED", message_ru: "Рассылка кампании требует согласования." }) };
    }
    if (body.includes("fail-me")) {
      return { ok: true, status: 200, json: async () => ({ ok: false, item: { status: "FAILED" }, message_ru: "SMTP недоступен." }) };
    }
    return { ok: true, status: 200, json: async () => ({ ok: true, item: { id: "m1", status: "SENT", delivered: false } }) };
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

describe("Email SMTP provider card", () => {
  beforeEach(() => {
    fetchMock.mockClear();
    providerItems = [
      {
        provider: "email",
        label: "Email",
        status: "NOT_CONFIGURED",
        status_label_ru: "Не настроено",
        mode: "LIVE",
        mode_label_ru: "LIVE",
        frozen: false,
        connect_cta: true,
        wizard: [{ id: "smtp_password", label_ru: "Пароль SMTP", secret: true }],
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

  it("shows Email NOT_CONFIGURED card", async () => {
    renderProviders();
    expect(await screen.findByTestId("email-status-not-configured")).toBeTruthy();
    expect(screen.getByTestId("provider-card-email").textContent).toContain("Не настроено");
  });

  it("shows CONNECTED state", async () => {
    providerItems[0] = { ...providerItems[0], status: "CONNECTED", status_label_ru: "Подключено" };
    renderProviders();
    expect(await screen.findByTestId("email-status-connected")).toBeTruthy();
  });

  it("shows ERROR state", async () => {
    providerItems[0] = { ...providerItems[0], status: "ERROR", status_label_ru: "Ошибка", last_error: "AUTH_ERROR" } as typeof providerItems[0];
    renderProviders();
    expect(await screen.findByTestId("email-status-error")).toBeTruthy();
  });

  it("check connection action", async () => {
    providerItems[0] = { ...providerItems[0], status: "CONNECTED", status_label_ru: "Подключено" };
    renderProviders();
    fireEvent.click(await screen.findByTestId("email-check-connection"));
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/providers/email/test"))).toBe(true);
  });

  it("test email action", async () => {
    providerItems[0] = { ...providerItems[0], status: "CONNECTED", status_label_ru: "Подключено" };
    renderProviders();
    fireEvent.click(await screen.findByTestId("email-test-send"));
    fireEvent.click(await screen.findByTestId("email-test-send-confirm"));
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/providers/email/test-email"))).toBe(true);
  });

  it("password never rendered", async () => {
    renderProviders();
    fireEvent.click(await screen.findByText("Настроить"));
    expect(document.body.textContent).not.toContain(SECRET);
    const input = screen.getByTestId("secret-input-smtp_password") as HTMLInputElement;
    expect(input.type).toBe("password");
    expect(input.value).toBe("");
  });

  it("shows Telegram disabled/frozen without connection CTA", async () => {
    renderProviders();
    expect(await screen.findByTestId("telegram-frozen-badge")).toBeTruthy();
    expect(screen.getByTestId("provider-card-telegram").textContent).toContain("заморож");
    expect(screen.queryByTestId("provider-oauth-telegram")).toBeNull();
    expect(screen.getByTestId("provider-card-telegram").textContent).not.toContain("Подключить");
    expect(screen.getByTestId("provider-card-telegram").textContent).not.toContain("Настроить");
  });

  it("uses responsive layout classes", async () => {
    renderProviders();
    const grid = await screen.findByTestId("provider-connection-grid");
    expect(grid.className).toContain("md:grid-cols-2");
  });
});

describe("Candidate email composer", () => {
  beforeEach(() => fetchMock.mockClear());

  it("template selector, preview, send, history", async () => {
    render(
      <CandidateEmailComposer
        candidateId="c1"
        candidateName="Анна"
        candidateEmail="anna@example.com"
        headers={{ "X-Role": "owner" }}
      />,
    );
    expect(await screen.findByTestId("candidate-email-composer")).toBeTruthy();
    expect(screen.getByTestId("email-template-select")).toBeTruthy();
    fireEvent.click(screen.getByText("Предпросмотр"));
    expect((await screen.findByTestId("email-preview")).textContent).toContain("Анна");
    fireEvent.click(screen.getByTestId("email-send"));
    expect((await screen.findByTestId("email-send-state")).textContent).toContain("SMTP принял");
    expect(screen.getByTestId("email-history").textContent).toContain("SENT");
  });

  it("failure state", async () => {
    render(
      <CandidateEmailComposer
        candidateId="c1"
        candidateName="Анна"
        candidateEmail="fail-me@example.com"
        headers={{ "X-Role": "owner" }}
      />,
    );
    await screen.findByTestId("candidate-email-composer");
    fireEvent.change(screen.getByDisplayValue("fail-me@example.com"), { target: { value: "fail-me@example.com" } });
    fireEvent.click(screen.getByTestId("email-send"));
    expect(await screen.findByTestId("email-failure-state")).toBeTruthy();
  });

  it("campaign approval blocks send", async () => {
    render(
      <CandidateEmailComposer
        candidateId="c1"
        candidateName="Анна"
        candidateEmail="anna@example.com"
        headers={{ "X-Role": "owner" }}
        campaignId="camp-1"
      />,
    );
    expect((await screen.findByTestId("email-campaign-approval")).textContent).toContain("согласован");
    expect(screen.queryByTestId("email-send")).toBeNull();
  });
});
