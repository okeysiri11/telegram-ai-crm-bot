/**
 * Sprint 49.0 — Beauty / Cafe / Crypto OTC business cabinets (not engineering matrix).
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { BeautyBusinessPage } from "../beauty/BeautyBusinessPage";
import { CafeBusinessPage } from "../cafe/CafeBusinessPage";
import { CryptoOtcDeskPage } from "../crypto/CryptoOtcDeskPage";

vi.stubGlobal(
  "fetch",
  vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ items: [] }),
  })),
);

function mount(path: string, el: React.ReactElement) {
  const withEmbed = path.includes("?") ? `${path}&embed=1` : `${path}?embed=1`;
  return render(
    <MemoryRouter initialEntries={[withEmbed]}>
      <Routes>
        <Route path="/workspace/beauty" element={el} />
        <Route path="/workspace/beauty/:sub" element={el} />
        <Route path="/workspace/cafe" element={el} />
        <Route path="/workspace/cafe/:sub" element={el} />
        <Route path="/workspace/crypto" element={el} />
        <Route path="/workspace/crypto/:sub" element={el} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("Sprint 49.0 business cabinets", () => {
  it("Beauty opens RU operational cabinet with salon nav", async () => {
    mount("/workspace/beauty", <BeautyBusinessPage />);
    const root = await screen.findByTestId("beauty-business-cabinet");
    expect(root).toBeTruthy();
    expect(root.textContent).toContain("Beauty");
    expect(root.querySelector('[aria-label="Разделы"]')?.textContent).toMatch(/Клиенты/);
    expect(root.querySelector('[aria-label="Разделы"]')?.textContent).toMatch(/Записи/);
    expect(root.querySelector('[aria-label="Разделы"]')?.textContent).toMatch(/Мастера/);
    expect(root.textContent).not.toMatch(/Enterprise Reuse/i);
    expect(root.textContent).not.toMatch(/Reusable Patterns/i);
  });

  it("Cafe opens RU venue cabinet with order types surface", async () => {
    mount("/workspace/cafe", <CafeBusinessPage />);
    const root = await screen.findByTestId("cafe-business-cabinet");
    expect(root).toBeTruthy();
    expect(root.querySelector('[aria-label="Разделы"]')?.textContent).toMatch(/Заказы/);
    expect(root.querySelector('[aria-label="Разделы"]')?.textContent).toMatch(/Меню/);
    expect(root.querySelector('[aria-label="Разделы"]')?.textContent).toMatch(/Смены/);
    expect(root.textContent).not.toMatch(/cross-vertical/i);
  });

  it("Crypto OTC is a trader desk without other verticals", async () => {
    mount("/workspace/crypto", <CryptoOtcDeskPage />);
    const root = await screen.findByTestId("crypto-otc-desk");
    expect(root).toBeTruthy();
    expect(root.textContent).toContain("Crypto OTC");
    const nav = root.querySelector('[aria-label="Разделы"]')?.textContent || "";
    expect(nav).toMatch(/Мои пары/);
    expect(nav).toMatch(/Графики/);
    expect(nav).toMatch(/OTC-сделки/);
    expect(root.textContent).not.toContain("Automotive");
    expect(root.textContent).not.toContain("Agriculture");
    expect(root.textContent).not.toContain("Enterprise Reuse");
  });
});
