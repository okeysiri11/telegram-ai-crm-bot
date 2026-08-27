import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { VanguardCareerPage } from "./VanguardCareerPage";

const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  if (String(url).includes("/applications") && init?.method === "POST") {
    const body = JSON.parse(String(init.body || "{}"));
    return {
      ok: true,
      status: 201,
      json: async () => ({
        ok: true,
        application_received: true,
        reference: "VG-TEST01",
        item: { ...body, project_key: "vanguard", source: "vanguard", external_id: "VG-TEST01" },
      }),
    };
  }
  return { ok: true, status: 201, json: async () => ({ ok: true }) };
});

vi.stubGlobal("fetch", fetchMock);

describe("Vanguard career form", () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it("submits application to vanguard-site API and shows reference", async () => {
    render(
      <MemoryRouter>
        <VanguardCareerPage />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("vanguard-career-page")).toBeTruthy();
    fireEvent.change(screen.getByPlaceholderText("Имя"), { target: { value: "E2E_LIVE" } });
    fireEvent.change(screen.getByPlaceholderText("Email"), { target: { value: "e2e.live@example.com" } });
    fireEvent.click(screen.getByTestId("vanguard-apply-submit"));
    expect(await screen.findByTestId("vanguard-application-received")).toBeTruthy();
    expect(screen.getByTestId("vanguard-reference").textContent).toMatch(/VG-TEST01/);
    await waitFor(() => {
      const posts = fetchMock.mock.calls.filter((c) => String(c[1]?.method) === "POST");
      const apply = posts.find((c) => String(c[0]).includes("/api/vanguard-site/v1/applications"));
      expect(apply).toBeTruthy();
      const headers = (apply?.[1]?.headers || {}) as Record<string, string>;
      expect(headers["Idempotency-Key"]).toBeTruthy();
    });
  });
});
