import { expect, test } from "@playwright/test";

test("real browser: Vanguard form → Recruiting INTERVIEW", async ({ page, request }) => {
  await expect
    .poll(async () => {
      const res = await request.get("http://127.0.0.1:8080/api/vanguard-site/v1/health");
      return res.ok();
    }, { timeout: 30_000 })
    .toBeTruthy();

  const email = `e2e.harden.${Date.now()}@example.com`;
  await page.goto("/vanguard");
  await expect(page.getByTestId("vanguard-career-page")).toBeVisible();
  await page.getByPlaceholder("Имя").fill("E2E_HARDEN");
  await page.getByPlaceholder("Email").fill(email);
  await page.getByPlaceholder("Страна").fill("UA");
  await page.getByPlaceholder("Программа / вакансия").fill("Frontend Recruiter");
  await page.getByPlaceholder("Почему вы откликаетесь").fill("Playwright acceptance");
  await page.getByTestId("vanguard-apply-submit").click();
  const received = page.getByTestId("vanguard-application-received");
  const applyError = page.getByTestId("vanguard-apply-error");
  await expect(received.or(applyError)).toBeVisible({ timeout: 20_000 });
  if (await applyError.isVisible().catch(() => false)) {
    throw new Error(`Vanguard apply failed: ${(await applyError.innerText()).trim()}`);
  }
  await expect(received).toBeVisible();
  const reference = (await page.getByTestId("vanguard-reference").innerText()).trim();
  expect(reference).toMatch(/^VG-[A-Z0-9]{6}$/);

  await page.goto("/login");
  const owner = page.getByTestId("login-as-owner");
  if (!(await owner.isVisible().catch(() => false))) {
    throw new Error("BLOCKED: Local Owner login is not available; cannot open Recruiting UI in the browser.");
  }
  await owner.click();
  await page.waitForURL(/workspace|dashboard|home|recruiting/, { timeout: 20_000 });
  await page.goto("/workspace/recruiting/projects/vanguard?tab=leads");
  await expect(page.getByTestId("vanguard-leads")).toContainText(reference, { timeout: 20_000 });
  await expect(page.getByTestId("vanguard-leads")).toContainText("E2E_HARDEN");

  await page.getByRole("button", { name: "Квалифицировать" }).click();
  await page.getByRole("button", { name: "В кандидаты" }).click();
  await page.getByRole("button", { name: "Кандидаты" }).click();
  await expect(page.getByTestId("vanguard-candidates")).toBeVisible();
  await page.getByRole("button", { name: "В интервью" }).click();
  await expect(page.getByTestId("vanguard-candidates")).toContainText("Интервью");
  await page.reload();
  await page.getByRole("button", { name: "Кандидаты" }).click();
  await expect(page.getByTestId("vanguard-candidates")).toContainText("Интервью");
});
