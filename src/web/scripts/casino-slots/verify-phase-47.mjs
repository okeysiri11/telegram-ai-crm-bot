import { chromium } from "playwright";
import { existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const OUT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../../artifacts/casino");
const BASE = process.env.PHASE47_URL || "http://127.0.0.1:5188";
const MACHINES = [
  "olympus-crown",
  "candy-fortune",
  "pharaohs-book",
  "big-catch",
  "buffalo-fortune",
  "lady-emerald",
];

function findChromium() {
  const candidates = [
    process.env.PLAYWRIGHT_CHROMIUM_PATH,
    resolve(process.env.HOME || "", "Library/Caches/ms-playwright/chromium-1148/chrome-mac/Chromium.app/Contents/MacOS/Chromium"),
  ].filter(Boolean);
  for (const c of candidates) if (existsSync(c)) return c;
  return undefined;
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: findChromium(), headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.setDefaultTimeout(20000);
  const fail = [];

  async function go(path) {
    await page.goto(BASE + path, { waitUntil: "domcontentloaded" });
  }

  await go("/casino/slots/olympus-crown");
  await page.waitForSelector("[data-testid='seated-cabinet']");
  await page.waitForTimeout(650);
  const seated = await page.evaluate(() => {
    const root = document.documentElement;
    const cab = document.querySelector("[data-testid='seated-cabinet']")?.getBoundingClientRect();
    const screen = document.querySelector("[data-testid='slot-preview-seated']")?.getBoundingClientRect();
    const reels = document.querySelector("[data-testid='slot-reels']")?.getBoundingClientRect();
    return {
      scroll: root.scrollHeight - root.clientHeight,
      cabH: cab?.height || 0,
      overflow: !screen || !reels
        ? true
        : reels.left < screen.left - 1 || reels.top < screen.top - 1 || reels.right > screen.right + 1 || reels.bottom > screen.bottom + 1,
      chair: Boolean(document.querySelector("[data-testid='seated-armchair']")),
      webPanel: Boolean(document.querySelector("[data-testid='slot-web-panel']")),
    };
  });
  if (seated.scroll > 2) fail.push("vertical scroll");
  if (seated.cabH < 900) fail.push("cabinet not close");
  if (seated.overflow) fail.push("reel overflow");
  if (seated.chair) fail.push("fake chair");
  if (seated.webPanel) fail.push("web panel");
  await page.screenshot({ path: resolve(OUT, "phase47-olympus-seated.png") });

  await page.hover("[data-testid='slot-spin']");
  await page.waitForTimeout(200);
  await page.screenshot({ path: resolve(OUT, "phase47-olympus-hover-spin.png") });

  await page.click("[data-testid='slot-bet-25']");
  const bet = (await page.textContent("[data-testid='slot-demo-bet']"))?.trim();
  if (bet !== "25") fail.push(`bet 25 => ${bet}`);
  await page.screenshot({ path: resolve(OUT, "phase47-olympus-bet25.png") });

  await page.click("[data-testid='slot-spin']");
  await page.waitForTimeout(180);
  await page.screenshot({ path: resolve(OUT, "phase47-olympus-spinning.png") });
  await page.waitForTimeout(1300);

  await page.click("[data-testid='slot-service']");
  if (!(await page.$("[data-testid='slot-service-panel']"))) fail.push("service");
  await page.screenshot({ path: resolve(OUT, "phase47-olympus-service.png") });
  await page.click("[data-testid='slot-service']");

  const before = Number(await page.textContent("[data-testid='slot-demo-balance']"));
  await page.click("[data-testid='slot-insert-bill']");
  const after = Number(await page.textContent("[data-testid='slot-demo-balance']"));
  if (after <= before) fail.push("insert bill");
  await page.screenshot({ path: resolve(OUT, "phase47-olympus-insert-bill.png") });

  for (const id of MACHINES.filter((item) => item !== "olympus-crown")) {
    await go(`/casino/slots/${id}`);
    await page.waitForSelector("[data-testid='seated-cabinet']");
    await page.waitForTimeout(450);
    await page.screenshot({ path: resolve(OUT, `phase47-${id}-seated.png`) });
  }

  page.setViewportSize({ width: 1440, height: 900 });
  await go("/casino/slots/lady-emerald");
  await page.waitForSelector("[data-testid='seated-cabinet']");
  await page.waitForTimeout(350);
  await page.screenshot({ path: resolve(OUT, "phase47-emerald-1440.png") });
  page.setViewportSize({ width: 1366, height: 768 });
  await go("/casino/slots/pharaohs-book");
  await page.waitForSelector("[data-testid='seated-cabinet']");
  await page.waitForTimeout(350);
  await page.screenshot({ path: resolve(OUT, "phase47-pharaohs-1366.png") });

  await browser.close();
  if (fail.length) {
    console.error("PHASE47_VISUAL_FAIL", fail);
    process.exit(1);
  }
  console.log("PHASE47_VISUAL_PASS");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
